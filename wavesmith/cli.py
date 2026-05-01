"""Command line interface for WaveSmith."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from wavesmith import __version__
from wavesmith.presets.loader import PresetError, list_builtin_presets, load_preset

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
    """Placeholder for rendering one audio file to one video file."""
    console.print("[yellow]Render is planned for M1+ and is not implemented in M0.[/yellow]")
    console.print(f"input={input_audio}")
    console.print(f"output={output_video}")
    console.print(f"preset={preset}")
    console.print(f"resolution={resolution}, fps={fps}, max_seconds={max_seconds}")
    console.print(f"watermark={watermark}, crf={crf}, ffmpeg_preset={ffmpeg_preset}")
    console.print(f"force_analysis={force_analysis}")
    raise typer.Exit(1)


@app.command()
def analyze(
    input_audio: Annotated[Path, typer.Argument(help="Input MP3 or WAV file.")],
    out: Annotated[Path | None, typer.Option("--out", help="Optional analysis JSON path.")] = None,
    force: Annotated[bool, typer.Option("--force", help="Force analysis refresh.")] = False,
) -> None:
    """Placeholder for audio analysis."""
    console.print("[yellow]Audio analysis is planned for M2 and is not implemented in M0.[/yellow]")
    console.print(f"input={input_audio}")
    console.print(f"out={out}")
    console.print(f"force={force}")
    raise typer.Exit(1)


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
