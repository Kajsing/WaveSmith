import pytest

from wavesmith.ai import build_ai_prompt_manifest


def test_build_ai_prompt_manifest_is_local_and_structured() -> None:
    manifest = build_ai_prompt_manifest(
        art_brief={
            "mood": ["dark", "restless"],
            "imagery": ["low light"],
            "palette": ["deep violet", "cold cyan"],
            "motion": "slow pressure waves",
        },
        target="poster",
        provider="openai",
    )

    assert manifest["privacy"]["user_must_opt_in_before_sending"] is True
    assert manifest["provider"] == "openai"
    assert manifest["target"] == "poster"
    assert "image_prompt" in manifest["expected_output"]["fields"]


def test_build_ai_prompt_manifest_rejects_unknown_target() -> None:
    with pytest.raises(ValueError, match="AI target"):
        build_ai_prompt_manifest(art_brief={}, target="unknown")  # type: ignore[arg-type]
