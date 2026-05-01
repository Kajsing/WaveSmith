"""Build local prompt manifests for optional AI workflows."""

from typing import Any, Literal

AiTarget = Literal["preset", "poster", "lyrics_timing"]


def build_ai_prompt_manifest(
    *,
    art_brief: dict[str, Any],
    target: AiTarget,
    provider: str = "generic",
) -> dict[str, Any]:
    """Build a local manifest that can be sent to an AI provider later by explicit opt-in."""
    if target not in {"preset", "poster", "lyrics_timing"}:
        raise ValueError("AI target must be preset, poster, or lyrics_timing.")

    return {
        "provider": provider,
        "target": target,
        "privacy": {
            "upload_required": False,
            "user_must_opt_in_before_sending": True,
            "recommendation": "Send art briefs or summaries instead of raw audio or full lyrics.",
        },
        "art_brief": art_brief,
        "prompt": _prompt_for(target, art_brief),
        "expected_output": _expected_output_for(target),
    }


def _prompt_for(target: AiTarget, art_brief: dict[str, Any]) -> str:
    mood = ", ".join(_list_value(art_brief.get("mood"))) or "unspecified mood"
    imagery = ", ".join(_list_value(art_brief.get("imagery"))) or "abstract audio visuals"
    palette = ", ".join(_list_value(art_brief.get("palette"))) or "reactive neon palette"
    motion = str(art_brief.get("motion") or "audio-reactive motion")
    if target == "preset":
        return (
            "Create a WaveSmith preset concept using only schema-safe module ideas. "
            f"Mood: {mood}. Imagery: {imagery}. Palette: {palette}. Motion: {motion}. "
            "Return compact YAML-compatible parameter suggestions, not Python code."
        )
    if target == "poster":
        return (
            "Create a poster thumbnail concept for a music visualizer. "
            f"Mood: {mood}. Imagery: {imagery}. Palette: {palette}. Motion: {motion}. "
            "Return visual composition notes and a short image prompt."
        )
    return (
        "Suggest timing cleanup notes for lyric display. "
        f"Mood: {mood}. Motion: {motion}. Return offset and readability suggestions only."
    )


def _expected_output_for(target: AiTarget) -> dict[str, Any]:
    if target == "preset":
        return {
            "format": "json",
            "fields": ["preset_name", "palette", "modules", "motion_notes"],
        }
    if target == "poster":
        return {
            "format": "json",
            "fields": ["composition", "image_prompt", "negative_prompt", "palette"],
        }
    return {
        "format": "json",
        "fields": ["lyrics_offset", "line_length_notes", "placement_notes"],
    }


def _list_value(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
