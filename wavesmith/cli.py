"""Command line interface for WaveSmith."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from wavesmith import __version__
from wavesmith.audio.analyzer import DEFAULT_FEATURE_FPS, AudioAnalysisError, analyze_audio
from wavesmith.presets.loader import PresetError, list_builtin_presets, load_preset
from wavesmith.render.ffmpeg import FfmpegMissingError, FfmpegRenderError
from wavesmith.render.options import RenderOptionsError, build_render_options
from wavesmith.render.pipeline import render_video

app = typer.Typer(
    help="Local-first audio-reactive video generation for music visualizers.",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"WaveSmith {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, help="Show the WaveSmith version."),
    ] = False,
) -> None:
    """WaveSmith command group."""


@app.command("list-presets")
def list_presets() -> None:
    """List built-in visual presets."""
    for preset in list_builtin_presets():
        console.print(preset)


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
    force_analysis: Annotated[
        bool,
        typer.Option("--force-analysis", help="Bypass any future analysis cache."),
    ] = False,
) -> None:
    """Render one audio file to one MP4 video."""
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
            force_analysis=force_analysis,
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
    except AudioAnalysisError as exc:
        console.print(f"[red]Audio analysis failed:[/red] {exc}")
        raise typer.Exit(4) from exc

    console.print(f"[green]Rendered:[/green] {output_video} ({result.duration_seconds:.2f}s)")
    console.print(f"analysis_cache={result.cache_status} ({result.cache_path})")
    console.print(f"render_log={result.log_path}")


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
) -> None:
    """Placeholder for batch rendering."""
    console.print(
        "[yellow]Batch rendering is planned for M6 and is not implemented in M0.[/yellow]"
    )
    console.print(f"input_dir={input_dir}")
    console.print(f"output_dir={output_dir}")
    console.print(f"preset={preset}, resolution={resolution}, fps={fps}")
    raise typer.Exit(1)
