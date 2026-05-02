from pathlib import Path

from typer.testing import CliRunner

from tests.audio_fixtures import write_test_tone
from wavesmith.cli import _compact_path, app
from wavesmith.render.pipeline import RenderResult

runner = CliRunner()


def test_help_command_succeeds() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "WaveSmith" in result.output


def test_list_presets_shows_builtins() -> None:
    result = runner.invoke(app, ["list-presets"])

    assert result.exit_code == 0
    assert "elemental_storm" in result.output
    assert "inferno_portal" in result.output
    assert "neon_orb" in result.output
    assert "shader_bloom" in result.output
    assert "spectrum_ring" in result.output
    assert "waveform_ribbon" in result.output


def test_list_presets_details_shows_descriptions() -> None:
    result = runner.invoke(app, ["list-presets", "--details"])

    assert result.exit_code == 0
    assert "Preset" in result.output
    assert "shader_bloom" in result.output
    assert "shader_field" in result.output
    assert "fields with bloom" in result.output


def test_list_presets_json_writes_metadata() -> None:
    result = runner.invoke(app, ["list-presets", "--json"])

    assert result.exit_code == 0
    assert '"name": "neon_orb"' in result.output
    assert '"modules"' in result.output


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


def test_lyrics_inspect_reports_timing_stats(tmp_path) -> None:
    lyrics = tmp_path / "song.lrc"
    lyrics.write_text("[00:01.00]one\n[00:04.50]two", encoding="utf-8")

    result = runner.invoke(app, ["lyrics-inspect", str(lyrics)])

    assert result.exit_code == 0
    assert "Lyrics loaded" in result.output
    assert "2 cues" in result.output
    assert "largest_gap" in result.output


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


def test_ai_prompt_command_writes_manifest(tmp_path) -> None:
    art_brief = tmp_path / "song.art.json"
    output = tmp_path / "song.ai.json"
    art_brief.write_text(
        '{"mood":["dark"],"imagery":["low light"],"palette":["cyan"],"motion":"slow"}',
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "ai-prompt",
            str(art_brief),
            "--target",
            "poster",
            "--provider",
            "openai",
            "--out",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert output.exists()
    assert "AI prompt manifest written" in result.output


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


def test_preview_uses_low_cost_defaults(monkeypatch, tmp_path) -> None:
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"not real audio yet")
    output = tmp_path / "preview.mp4"
    seen = {}

    def fake_render(options):
        seen["options"] = options
        return RenderResult(
            duration_seconds=20.0,
            cache_status="miss",
            cache_path=tmp_path / "analysis.json",
            log_path=tmp_path / "render.log",
            thumbnail_path=tmp_path / "thumb.jpg",
        )

    monkeypatch.setattr("wavesmith.cli.render_video", fake_render)

    result = runner.invoke(app, ["preview", str(audio), str(output), "--preset", "shader_bloom"])

    assert result.exit_code == 0
    assert "Rendered" in result.output
    assert seen["options"].width == 640
    assert seen["options"].height == 360
    assert seen["options"].fps == 15
    assert seen["options"].max_seconds == 20.0
    assert seen["options"].thumbnail is True
    assert seen["options"].thumbnail_at == "middle"


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
