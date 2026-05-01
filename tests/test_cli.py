from pathlib import Path

from typer.testing import CliRunner

from tests.audio_fixtures import write_test_tone
from wavesmith.cli import _compact_path, app

runner = CliRunner()


def test_help_command_succeeds() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "WaveSmith" in result.output


def test_list_presets_shows_builtins() -> None:
    result = runner.invoke(app, ["list-presets"])

    assert result.exit_code == 0
    assert "neon_orb" in result.output
    assert "shader_bloom" in result.output
    assert "spectrum_ring" in result.output
    assert "waveform_ribbon" in result.output


def test_validate_preset_accepts_builtin_file() -> None:
    result = runner.invoke(app, ["validate-preset", "presets/neon_orb.yaml"])

    assert result.exit_code == 0
    assert "Valid preset" in result.output


def test_art_brief_command_writes_json(tmp_path) -> None:
    lyrics = tmp_path / "song.lrc"
    output = tmp_path / "song.art.json"
    lyrics.write_text("[00:01.00]dark pressure under skin", encoding="utf-8")

    result = runner.invoke(app, ["art-brief", "--lyrics", str(lyrics), "--out", str(output)])

    assert result.exit_code == 0
    assert output.exists()
    assert "Art brief written" in result.output


def test_make_preset_command_writes_valid_yaml(tmp_path) -> None:
    output = tmp_path / "custom.yaml"

    result = runner.invoke(
        app,
        [
            "make-preset",
            "dark cyberpunk shader bloom",
            "--name",
            "dark cyber",
            "--out",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert output.exists()
    assert "Preset written" in result.output


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


def test_analyze_writes_json(tmp_path) -> None:
    audio = tmp_path / "tone.wav"
    output = tmp_path / "tone.analysis.json"
    write_test_tone(audio)

    result = runner.invoke(app, ["analyze", str(audio), "--out", str(output)])

    assert result.exit_code == 0
    assert output.exists()
    assert "Analysis written" in result.output


def test_analyze_accepts_feature_fps_option(tmp_path) -> None:
    audio = tmp_path / "tone.wav"
    output = tmp_path / "tone.analysis.json"
    write_test_tone(audio, seconds=2.0)

    result = runner.invoke(
        app,
        ["analyze", str(audio), "--out", str(output), "--feature-fps", "5"],
    )

    assert result.exit_code == 0
    assert output.exists()


def test_analyze_rejects_missing_input(tmp_path) -> None:
    result = runner.invoke(app, ["analyze", str(tmp_path / "missing.wav")])

    assert result.exit_code == 2
    assert "does not exist" in result.output


def test_compact_path_shortens_long_cache_names() -> None:
    path = (
        ".cache/analysis/"
        "b31c738b6c49a0b93adc3e41094ef031a4c1f1bad56b32c8f6de21a1a5d7fd78.analysis.json"
    )

    compact = _compact_path(Path(path))

    assert compact == ".cache/analysis/b31c738b6c49....json"
