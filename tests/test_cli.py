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
