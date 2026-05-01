from typer.testing import CliRunner

from wavesmith.cli import app

runner = CliRunner()


def test_help_command_succeeds() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "WaveSmith" in result.output


def test_list_presets_shows_builtins() -> None:
    result = runner.invoke(app, ["list-presets"])

    assert result.exit_code == 0
    assert "neon_orb" in result.output
    assert "spectrum_ring" in result.output
    assert "waveform_ribbon" in result.output


def test_validate_preset_accepts_builtin_file() -> None:
    result = runner.invoke(app, ["validate-preset", "presets/neon_orb.yaml"])

    assert result.exit_code == 0
    assert "Valid preset" in result.output


def test_render_rejects_missing_input() -> None:
    result = runner.invoke(app, ["render", "missing.wav", "out.mp4"])

    assert result.exit_code == 2
    assert "Input audio file does not exist" in result.output


def test_render_rejects_invalid_output_extension(tmp_path) -> None:
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"not real audio yet")

    result = runner.invoke(app, ["render", str(audio), str(tmp_path / "out.mov")])

    assert result.exit_code == 2
    assert "Output video path must end with .mp4" in result.output


def test_render_rejects_invalid_resolution(tmp_path) -> None:
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"not real audio yet")

    result = runner.invoke(
        app,
        ["render", str(audio), str(tmp_path / "out.mp4"), "--resolution", "641x360"],
    )

    assert result.exit_code == 2
    assert "even numbers" in result.output
