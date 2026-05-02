"""Command line interface for WaveSmith."""

import json
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.table import Table

from wavesmith import __version__
from wavesmith.ai import build_ai_prompt_manifest
from wavesmith.art import build_art_brief
from wavesmith.audio.analyzer import DEFAULT_FEATURE_FPS, AudioAnalysisError, analyze_audio
from wavesmith.gpu import probe_gpu
from wavesmith.lyrics import LyricCue, LyricsError, load_lyrics
from wavesmith.presets.generator import generate_preset_dict
from wavesmith.presets.loader import (
    PresetError,
    PresetSummary,
    list_builtin_preset_summaries,
    load_preset,
)
from wavesmith.render.backends import RenderBackendError
from wavesmith.render.batch import run_batch
from wavesmith.render.compare import run_compare
from wavesmith.render.ffmpeg import FfmpegMissingError, FfmpegRenderError
from wavesmith.render.options import RenderOptionsError, build_render_options, parse_resolution
from wavesmith.render.pipeline import RenderResult, render_video

app = typer.Typer(
    help="Local-first audio-reactive video generation for music visualizers.",
    no_args_is_help=True,
)
console = Console()


def _compact_path(path: Path, *, keep: int = 12) -> str:
    """Return a terminal-friendly path display."""
    name = path.name
    if len(name) > keep + 8:
        name = f"{name[:keep]}...{path.suffix}"
    parent = path.parent.as_posix()
    if parent == ".":
        return name
    return f"{parent}/{name}"


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"WaveSmith {__version__}")
        raise typer.Exit()


def _print_render_summary(output_video: Path, result: RenderResult) -> None:
    console.print(f"[green]Rendered:[/green] {output_video} ({result.duration_seconds:.2f}s)")
    console.print(f"analysis_cache={result.cache_status} cache={_compact_path(result.cache_path)}")
    if result.effective_fps is not None and result.encode_elapsed_seconds is not None:
        console.print(
            f"backend={result.backend} encode_time={result.encode_elapsed_seconds:.2f}s "
            f"effective_fps={result.effective_fps:.1f}"
        )
    console.print(f"render_log={_compact_path(result.log_path, keep=26)}")
    if result.thumbnail_path:
        console.print(f"thumbnail={_compact_path(result.thumbnail_path, keep=26)}")
    if result.thumbnail_time_seconds is not None:
        console.print(f"thumbnail_time={result.thumbnail_time_seconds:.3f}s")


def _run_render_command(
    *,
    input_audio: Path,
    output_video: Path,
    preset: str,
    resolution: str,
    fps: int,
    max_seconds: float | None,
    watermark: str | None,
    crf: int,
    ffmpeg_preset: str,
    backend: str,
    force_analysis: bool,
    thumbnail: bool,
    thumbnail_at: str,
    thumbnail_style: str,
    lyrics: Path | None,
    lyrics_offset: float,
) -> None:
    try:
        options = build_render_options(
            input_audio=input_audio,
            output_video=output_video,
            preset=preset,
            resolution=resolution,
            fps=fps,
            max_seconds=max_seconds,
            watermark=watermark,
            crf=crf,
            ffmpeg_preset=ffmpeg_preset,
            backend=backend,
            force_analysis=force_analysis,
            thumbnail=thumbnail,
            thumbnail_at=thumbnail_at,
            thumbnail_style=thumbnail_style,
            lyrics_path=lyrics,
            lyrics_offset=lyrics_offset,
        )
        result = render_video(options)
    except RenderOptionsError as exc:
        console.print(f"[red]Invalid render options:[/red] {exc}")
        raise typer.Exit(2) from exc
    except PresetError as exc:
        console.print(f"[red]Preset error:[/red] {exc}")
        raise typer.Exit(2) from exc
    except FfmpegMissingError as exc:
        console.print(f"[red]Missing dependency:[/red] {exc}")
        raise typer.Exit(3) from exc
    except FfmpegRenderError as exc:
        console.print(f"[red]Render failed:[/red] {exc}")
        raise typer.Exit(4) from exc
    except RenderBackendError as exc:
        console.print(f"[red]Render backend error:[/red] {exc}")
        raise typer.Exit(4) from exc
    except AudioAnalysisError as exc:
        console.print(f"[red]Audio analysis failed:[/red] {exc}")
        raise typer.Exit(4) from exc
    except LyricsError as exc:
        console.print(f"[red]Lyrics error:[/red] {exc}")
        raise typer.Exit(4) from exc

    _print_render_summary(output_video, result)


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, help="Show the WaveSmith version."),
    ] = False,
) -> None:
    """WaveSmith command group."""


@app.command("list-presets")
def list_presets(
    details: Annotated[
        bool,
        typer.Option("--details", "-d", help="Show descriptions and module stacks."),
    ] = False,
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Write preset metadata as JSON."),
    ] = False,
    family: Annotated[
        str | None,
        typer.Option("--family", help="Only show presets in this family."),
    ] = None,
    tag: Annotated[
        str | None,
        typer.Option("--tag", help="Only show presets with this tag."),
    ] = None,
) -> None:
    """List built-in visual presets."""
    summaries = _filter_preset_summaries(list_builtin_preset_summaries(), family, tag)
    if as_json:
        payload = [
            {
                "name": summary.name,
                "description": summary.description,
                "family": summary.family,
                "tags": list(summary.tags),
                "modules": list(summary.modules),
                "path": str(summary.path),
            }
            for summary in summaries
        ]
        console.print_json(json.dumps(payload))
        return

    if details:
        table = Table("Preset", "Family", "Tags", "Modules", "Description")
        for summary in summaries:
            table.add_row(
                summary.name,
                summary.family,
                ", ".join(summary.tags),
                ", ".join(summary.modules),
                summary.description,
            )
        console.print(table)
        return

    for preset in summaries:
        console.print(preset.name)


def _filter_preset_summaries(
    summaries: list[PresetSummary],
    family: str | None,
    tag: str | None,
) -> list[PresetSummary]:
    if family:
        family = family.strip().lower()
        summaries = [summary for summary in summaries if summary.family.lower() == family]
    if tag:
        tag = tag.strip().lower()
        summaries = [summary for summary in summaries if tag in summary.tags]
    return summaries


@app.command()
def validate_preset(
    preset_file: Annotated[Path, typer.Argument(help="Path to a preset YAML file.")],
) -> None:
    """Validate a preset file before rendering."""
    try:
        preset = load_preset(preset_file)
    except PresetError as exc:
        console.print(f"[red]Preset validation failed:[/red] {exc}")
        raise typer.Exit(5) from exc

    console.print(f"[green]Valid preset:[/green] {preset.name}")


@app.command("gpu-info")
def gpu_info() -> None:
    """Probe experimental ModernGL GPU rendering support."""
    capability = probe_gpu()
    if capability.available:
        console.print("[green]GPU backend available[/green]")
        console.print(f"backend={capability.backend}")
        console.print(f"renderer={capability.renderer or 'unknown'}")
        console.print(f"version={capability.version or 'unknown'}")
        return

    console.print("[red]GPU backend unavailable[/red]")
    console.print(f"backend={capability.backend}")
    console.print(f"error={capability.error or 'unknown error'}")
    raise typer.Exit(4)


@app.command("art-brief")
def art_brief(
    lyrics: Annotated[Path, typer.Option("--lyrics", help="Input .lrc or .srt timed lyrics file.")],
    out: Annotated[Path | None, typer.Option("--out", help="Optional art brief JSON path.")] = None,
) -> None:
    """Build a local art direction brief from timed lyrics."""
    try:
        cues = load_lyrics(lyrics)
    except LyricsError as exc:
        console.print(f"[red]Lyrics error:[/red] {exc}")
        raise typer.Exit(2) from exc

    brief = build_art_brief(cues).to_dict()
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")
        console.print(f"[green]Art brief written:[/green] {out}")
    else:
        console.print_json(json.dumps(brief))


def _lyrics_stats(cues: list[LyricCue]) -> dict[str, float | int]:
    total_duration = cues[-1].end - cues[0].start
    gaps = [
        max(0.0, cues[index + 1].start - cues[index].end)
        for index in range(len(cues) - 1)
    ]
    overlaps = sum(1 for index in range(len(cues) - 1) if cues[index + 1].start < cues[index].end)
    return {
        "cues": len(cues),
        "start": cues[0].start,
        "end": cues[-1].end,
        "duration": total_duration,
        "largest_gap": max(gaps, default=0.0),
        "overlaps": overlaps,
    }


@app.command("lyrics-inspect")
def lyrics_inspect(
    lyrics: Annotated[Path, typer.Argument(help="Input .lrc or .srt timed lyrics file.")],
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Write timing statistics as JSON."),
    ] = False,
) -> None:
    """Inspect timed lyrics before rendering."""
    try:
        cues = load_lyrics(lyrics)
    except LyricsError as exc:
        console.print(f"[red]Lyrics error:[/red] {exc}")
        raise typer.Exit(2) from exc

    stats = _lyrics_stats(cues)
    if as_json:
        console.print_json(json.dumps(stats))
        return

    console.print(f"[green]Lyrics loaded:[/green] {stats['cues']} cues")
    console.print(
        f"range={stats['start']:.2f}s..{stats['end']:.2f}s "
        f"duration={stats['duration']:.2f}s"
    )
    console.print(f"largest_gap={stats['largest_gap']:.2f}s overlaps={stats['overlaps']}")
    if stats["largest_gap"] > 8.0:
        console.print(
            "[yellow]Note:[/yellow] large timing gaps may leave long empty lyric sections."
        )
    if stats["overlaps"]:
        console.print("[yellow]Note:[/yellow] overlapping cues can replace each other quickly.")


@app.command("make-preset")
def make_preset(
    prompt: Annotated[str, typer.Argument(help="Short visual style prompt.")],
    out: Annotated[Path, typer.Option("--out", help="Output preset YAML path.")],
    name: Annotated[
        str,
        typer.Option("--name", help="Preset name written into YAML."),
    ] = "custom_prompt",
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite an existing preset file."),
    ] = False,
) -> None:
    """Generate a local schema-validated preset YAML file from a prompt."""
    if out.exists() and not force:
        console.print("[red]Preset already exists:[/red] use --force to overwrite it.")
        raise typer.Exit(2)

    preset = generate_preset_dict(prompt, name=name)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(preset, sort_keys=False), encoding="utf-8")
    load_preset(out)
    console.print(f"[green]Preset written:[/green] {out}")


@app.command("ai-prompt")
def ai_prompt(
    art_brief_file: Annotated[Path, typer.Argument(help="Input art brief JSON file.")],
    out: Annotated[Path, typer.Option("--out", help="Output AI prompt manifest JSON path.")],
    target: Annotated[
        str,
        typer.Option("--target", help="AI assist target: preset, poster, or lyrics_timing."),
    ] = "preset",
    provider: Annotated[
        str,
        typer.Option("--provider", help="Optional provider label, e.g. openai or huggingface."),
    ] = "generic",
) -> None:
    """Prepare a local prompt manifest for an optional AI workflow."""
    if not art_brief_file.exists():
        console.print(f"[red]Art brief file does not exist:[/red] {art_brief_file}")
        raise typer.Exit(2)
    try:
        art_brief = json.loads(art_brief_file.read_text(encoding="utf-8"))
        manifest = build_ai_prompt_manifest(
            art_brief=art_brief,
            target=target,  # type: ignore[arg-type]
            provider=provider,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        console.print(f"[red]AI prompt error:[/red] {exc}")
        raise typer.Exit(2) from exc

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    console.print(f"[green]AI prompt manifest written:[/green] {out}")


@app.command()
def render(
    input_audio: Annotated[Path, typer.Argument(help="Input MP3 or WAV file.")],
    output_video: Annotated[Path, typer.Argument(help="Output MP4 video path.")],
    preset: Annotated[str, typer.Option("--preset", help="Built-in preset name.")] = "neon_orb",
    resolution: Annotated[
        str,
        typer.Option("--resolution", help="Output resolution, e.g. 1920x1080."),
    ] = "1920x1080",
    fps: Annotated[int, typer.Option("--fps", min=1, help="Frames per second.")] = 30,
    max_seconds: Annotated[
        float | None,
        typer.Option("--max-seconds", min=0.1, help="Optional render duration limit."),
    ] = None,
    watermark: Annotated[str | None, typer.Option("--watermark", help="Watermark text.")] = None,
    crf: Annotated[
        int,
        typer.Option("--crf", min=0, max=51, help="ffmpeg CRF quality value."),
    ] = 18,
    ffmpeg_preset: Annotated[
        str,
        typer.Option("--ffmpeg-preset", help="ffmpeg encoder preset."),
    ] = "medium",
    backend: Annotated[
        str,
        typer.Option("--backend", help="Render backend: cpu or gpu."),
    ] = "cpu",
    force_analysis: Annotated[
        bool,
        typer.Option("--force-analysis", help="Bypass any future analysis cache."),
    ] = False,
    thumbnail: Annotated[
        bool,
        typer.Option("--thumbnail", help="Extract a local JPG thumbnail after rendering."),
    ] = False,
    thumbnail_at: Annotated[
        str,
        typer.Option(
            "--thumbnail-at",
            help="Thumbnail time: seconds, percent, best, or start/intro/middle/end.",
        ),
    ] = "50%",
    thumbnail_style: Annotated[
        str,
        typer.Option("--thumbnail-style", help="Thumbnail style: frame or poster."),
    ] = "frame",
    lyrics: Annotated[
        Path | None,
        typer.Option("--lyrics", help="Optional .lrc or .srt timed lyrics file."),
    ] = None,
    lyrics_offset: Annotated[
        float,
        typer.Option("--lyrics-offset", help="Shift lyric timings in seconds."),
    ] = 0.0,
) -> None:
    """Render one audio file to one MP4 video."""
    _run_render_command(
        input_audio=input_audio,
        output_video=output_video,
        preset=preset,
        resolution=resolution,
        fps=fps,
        max_seconds=max_seconds,
        watermark=watermark,
        crf=crf,
        ffmpeg_preset=ffmpeg_preset,
        backend=backend,
        force_analysis=force_analysis,
        thumbnail=thumbnail,
        thumbnail_at=thumbnail_at,
        thumbnail_style=thumbnail_style,
        lyrics=lyrics,
        lyrics_offset=lyrics_offset,
    )


@app.command()
def preview(
    input_audio: Annotated[Path, typer.Argument(help="Input MP3 or WAV file.")],
    output_video: Annotated[Path, typer.Argument(help="Output MP4 preview path.")],
    preset: Annotated[str, typer.Option("--preset", help="Built-in preset name.")] = "neon_orb",
    resolution: Annotated[
        str,
        typer.Option("--resolution", help="Preview resolution."),
    ] = "640x360",
    fps: Annotated[int, typer.Option("--fps", min=1, help="Preview frames per second.")] = 15,
    seconds: Annotated[
        float,
        typer.Option("--seconds", min=0.1, help="Preview duration limit."),
    ] = 20.0,
    watermark: Annotated[str | None, typer.Option("--watermark", help="Watermark text.")] = None,
    crf: Annotated[
        int,
        typer.Option("--crf", min=0, max=51, help="ffmpeg CRF quality value."),
    ] = 22,
    ffmpeg_preset: Annotated[
        str,
        typer.Option("--ffmpeg-preset", help="ffmpeg encoder preset."),
    ] = "veryfast",
    backend: Annotated[
        str,
        typer.Option("--backend", help="Render backend: cpu or gpu."),
    ] = "cpu",
    force_analysis: Annotated[
        bool,
        typer.Option("--force-analysis", help="Bypass analysis cache."),
    ] = False,
    thumbnail: Annotated[
        bool,
        typer.Option("--thumbnail/--no-thumbnail", help="Extract a JPG thumbnail."),
    ] = True,
    thumbnail_at: Annotated[
        str,
        typer.Option(
            "--thumbnail-at",
            help="Thumbnail time: seconds, percent, best, or start/intro/middle/end.",
        ),
    ] = "middle",
    thumbnail_style: Annotated[
        str,
        typer.Option("--thumbnail-style", help="Thumbnail style: frame or poster."),
    ] = "frame",
    lyrics: Annotated[
        Path | None,
        typer.Option("--lyrics", help="Optional .lrc or .srt timed lyrics file."),
    ] = None,
    lyrics_offset: Annotated[
        float,
        typer.Option("--lyrics-offset", help="Shift lyric timings in seconds."),
    ] = 0.0,
) -> None:
    """Render a short low-cost preview with practical defaults."""
    _run_render_command(
        input_audio=input_audio,
        output_video=output_video,
        preset=preset,
        resolution=resolution,
        fps=fps,
        max_seconds=seconds,
        watermark=watermark,
        crf=crf,
        ffmpeg_preset=ffmpeg_preset,
        backend=backend,
        force_analysis=force_analysis,
        thumbnail=thumbnail,
        thumbnail_at=thumbnail_at,
        thumbnail_style=thumbnail_style,
        lyrics=lyrics,
        lyrics_offset=lyrics_offset,
    )


@app.command()
def compare(
    input_audio: Annotated[Path, typer.Argument(help="Input MP3 or WAV file.")],
    output_dir: Annotated[Path, typer.Argument(help="Directory for comparison outputs.")],
    presets: Annotated[
        list[str] | None,
        typer.Option(
            "--preset",
            help="Preset to compare. Repeat this option for multiple presets.",
        ),
    ] = None,
    resolution: Annotated[
        str,
        typer.Option("--resolution", help="Comparison render resolution."),
    ] = "640x360",
    fps: Annotated[int, typer.Option("--fps", min=1, help="Frames per second.")] = 30,
    seconds: Annotated[
        float,
        typer.Option("--seconds", min=0.1, help="Comparison duration limit."),
    ] = 10.0,
    watermark: Annotated[str | None, typer.Option("--watermark", help="Watermark text.")] = None,
    crf: Annotated[
        int,
        typer.Option("--crf", min=0, max=51, help="ffmpeg CRF quality value."),
    ] = 18,
    ffmpeg_preset: Annotated[
        str,
        typer.Option("--ffmpeg-preset", help="ffmpeg encoder preset."),
    ] = "medium",
    backend: Annotated[
        str,
        typer.Option("--backend", help="Render backend: cpu or gpu."),
    ] = "cpu",
    force_analysis: Annotated[
        bool,
        typer.Option("--force-analysis", help="Bypass analysis cache for every render."),
    ] = False,
    thumbnails: Annotated[
        bool,
        typer.Option("--thumbnails/--no-thumbnails", help="Extract JPG thumbnails."),
    ] = True,
    thumbnail_at: Annotated[
        str,
        typer.Option(
            "--thumbnail-at",
            help="Thumbnail time: seconds, percent, best, or start/intro/middle/end.",
        ),
    ] = "best",
    thumbnail_style: Annotated[
        str,
        typer.Option("--thumbnail-style", help="Thumbnail style: frame or poster."),
    ] = "frame",
    stop_on_error: Annotated[
        bool,
        typer.Option("--stop-on-error", help="Stop after the first failed preset."),
    ] = False,
) -> None:
    """Render one audio file through multiple presets for side-by-side comparison."""
    selected_presets = presets or _default_compare_presets(backend)
    try:
        width, height = parse_resolution(resolution)
        for preset in selected_presets:
            load_preset(preset)
        summary = run_compare(
            input_audio=input_audio,
            output_dir=output_dir,
            presets=selected_presets,
            width=width,
            height=height,
            fps=fps,
            seconds=seconds,
            watermark=watermark,
            crf=crf,
            ffmpeg_preset=ffmpeg_preset,
            backend=backend,
            force_analysis=force_analysis,
            thumbnails=thumbnails,
            thumbnail_at=thumbnail_at,
            thumbnail_style=thumbnail_style,
            stop_on_error=stop_on_error,
        )
    except (ValueError, RenderOptionsError) as exc:
        console.print(f"[red]Invalid compare options:[/red] {exc}")
        raise typer.Exit(2) from exc
    except PresetError as exc:
        console.print(f"[red]Preset error:[/red] {exc}")
        raise typer.Exit(2) from exc

    table = Table("Preset", "Status", "FPS", "Output", "Thumbnail")
    for item in summary.results:
        table.add_row(
            item.preset,
            item.status,
            f"{item.effective_fps:.1f}" if item.effective_fps is not None else "",
            _compact_path(Path(item.output_video), keep=28),
            _compact_path(Path(item.thumbnail), keep=28) if item.thumbnail else "",
        )
    console.print(table)
    console.print(
        f"[green]Compare complete:[/green] {summary.succeeded} succeeded, {summary.failed} failed"
    )
    console.print(f"summary={_compact_path(Path(summary.summary_path), keep=26)}")
    if summary.failed:
        raise typer.Exit(4)


def _default_compare_presets(backend: str) -> list[str]:
    if backend == "gpu":
        return ["gpu_shader_bloom", "gpu_crystal_storm", "gpu_fire_solar"]
    return ["neon_orb", "shader_bloom", "waveform_ribbon"]


@app.command()
def analyze(
    input_audio: Annotated[Path, typer.Argument(help="Input MP3 or WAV file.")],
    out: Annotated[Path | None, typer.Option("--out", help="Optional analysis JSON path.")] = None,
    feature_fps: Annotated[
        int,
        typer.Option(
            "--feature-fps",
            min=1,
            help="Maximum serialized feature samples per second.",
        ),
    ] = DEFAULT_FEATURE_FPS,
    force: Annotated[bool, typer.Option("--force", help="Force analysis refresh.")] = False,
) -> None:
    """Analyze audio and write feature JSON."""
    if force:
        console.print("[yellow]Note:[/yellow] --force is reserved for cache refresh in M5.")

    output_path = out or input_audio.with_suffix(".analysis.json")
    try:
        analysis = analyze_audio(input_audio, feature_fps=feature_fps)
    except AudioAnalysisError as exc:
        console.print(f"[red]Audio analysis failed:[/red] {exc}")
        raise typer.Exit(2) from exc

    analysis.write_json(output_path)
    console.print(f"[green]Analysis written:[/green] {output_path}")


@app.command()
def batch(
    input_dir: Annotated[Path, typer.Argument(help="Directory containing audio files.")],
    output_dir: Annotated[Path, typer.Argument(help="Directory for generated videos.")],
    preset: Annotated[str, typer.Option("--preset", help="Built-in preset name.")] = "neon_orb",
    resolution: Annotated[
        str,
        typer.Option("--resolution", help="Output resolution."),
    ] = "1920x1080",
    fps: Annotated[int, typer.Option("--fps", min=1, help="Frames per second.")] = 30,
    max_seconds: Annotated[
        float | None,
        typer.Option("--max-seconds", min=0.1, help="Optional render duration limit."),
    ] = None,
    watermark: Annotated[str | None, typer.Option("--watermark", help="Watermark text.")] = None,
    crf: Annotated[
        int,
        typer.Option("--crf", min=0, max=51, help="ffmpeg CRF quality value."),
    ] = 18,
    ffmpeg_preset: Annotated[
        str,
        typer.Option("--ffmpeg-preset", help="ffmpeg encoder preset."),
    ] = "medium",
    backend: Annotated[
        str,
        typer.Option("--backend", help="Render backend: cpu or gpu."),
    ] = "cpu",
    force_analysis: Annotated[
        bool,
        typer.Option("--force-analysis", help="Bypass analysis cache for every item."),
    ] = False,
    thumbnails: Annotated[
        bool,
        typer.Option(
            "--thumbnails/--no-thumbnails",
            help="Extract JPG thumbnails for batch items.",
        ),
    ] = True,
    thumbnail_at: Annotated[
        str,
        typer.Option(
            "--thumbnail-at",
            help="Thumbnail time: seconds, percent, best, or start/intro/middle/end.",
        ),
    ] = "50%",
    thumbnail_style: Annotated[
        str,
        typer.Option("--thumbnail-style", help="Thumbnail style: frame or poster."),
    ] = "frame",
    stop_on_error: Annotated[
        bool,
        typer.Option("--stop-on-error", help="Stop batch rendering after the first failure."),
    ] = False,
) -> None:
    """Render supported audio files from a folder."""
    try:
        load_preset(preset)
        width, height = parse_resolution(resolution)
        summary = run_batch(
            input_dir=input_dir,
            output_dir=output_dir,
            preset=preset,
            width=width,
            height=height,
            fps=fps,
            max_seconds=max_seconds,
            watermark=watermark,
            crf=crf,
            ffmpeg_preset=ffmpeg_preset,
            backend=backend,
            force_analysis=force_analysis,
            thumbnails=thumbnails,
            thumbnail_at=thumbnail_at,
            thumbnail_style=thumbnail_style,
            stop_on_error=stop_on_error,
        )
    except (ValueError, RenderOptionsError) as exc:
        console.print(f"[red]Invalid batch options:[/red] {exc}")
        raise typer.Exit(2) from exc
    except PresetError as exc:
        console.print(f"[red]Preset error:[/red] {exc}")
        raise typer.Exit(2) from exc

    console.print(
        f"[green]Batch complete:[/green] {summary.succeeded} succeeded, {summary.failed} failed"
    )
    console.print(f"summary={_compact_path(Path(summary.summary_path), keep=26)}")
    if summary.failed:
        raise typer.Exit(4)
