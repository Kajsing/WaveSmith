"""Local lyric-to-art-brief heuristics."""

from dataclasses import asdict, dataclass

from wavesmith.lyrics import LyricCue


@dataclass(frozen=True)
class ArtBrief:
    """Compact art direction extracted from lyrics."""

    mood: list[str]
    imagery: list[str]
    palette: list[str]
    motion: str
    intensity: str
    suggested_preset: str
    source_line_count: int

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable mapping."""
        return asdict(self)


MOOD_KEYWORDS = {
    "dark": {"dark", "black", "night", "shadow", "void", "alone", "cold"},
    "intimate": {"skin", "touch", "breath", "close", "under", "inside", "heart"},
    "restless": {"run", "rush", "break", "burn", "pressure", "fall", "rise"},
    "bright": {"light", "sun", "gold", "white", "shine", "glow"},
    "dreamlike": {"dream", "sleep", "float", "slow", "ghost", "memory"},
}

IMAGERY_KEYWORDS = {
    "low light": {"dark", "night", "shadow", "low"},
    "body pressure": {"skin", "under", "blood", "heart", "breath"},
    "electric signals": {"signal", "wire", "static", "pulse", "frequency"},
    "water motion": {"wave", "river", "rain", "sea", "underwater"},
    "fire bloom": {"fire", "burn", "spark", "flare", "heat"},
}

PALETTES = {
    "dark": ["deep violet", "cold cyan", "soft white"],
    "intimate": ["soft magenta", "skin amber", "warm white"],
    "restless": ["hot pink", "acid teal", "strobe white"],
    "bright": ["gold", "sky blue", "clean white"],
    "dreamlike": ["mist blue", "lavender", "moon white"],
}


def build_art_brief(cues: list[LyricCue]) -> ArtBrief:
    """Build a compact local art brief from timed lyrics."""
    words = _normalized_words(" ".join(cue.text for cue in cues))
    mood = _rank_matches(words, MOOD_KEYWORDS)[:3] or ["neutral"]
    imagery = _rank_matches(words, IMAGERY_KEYWORDS)[:4] or ["abstract audio geometry"]
    palette = _palette_for_mood(mood)
    intensity = _intensity(words, cues)
    motion = _motion_for(mood, imagery, intensity)
    if intensity != "low" or "restless" in mood:
        suggested_preset = "shader_bloom"
    else:
        suggested_preset = "waveform_ribbon"
    return ArtBrief(
        mood=mood,
        imagery=imagery,
        palette=palette,
        motion=motion,
        intensity=intensity,
        suggested_preset=suggested_preset,
        source_line_count=len(cues),
    )


def _normalized_words(text: str) -> list[str]:
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in text)
    return [word for word in cleaned.split() if word]


def _rank_matches(words: list[str], groups: dict[str, set[str]]) -> list[str]:
    word_set = set(words)
    scored = [
        (label, len(word_set & keywords))
        for label, keywords in groups.items()
        if len(word_set & keywords)
    ]
    return [label for label, _ in sorted(scored, key=lambda item: (-item[1], item[0]))]


def _palette_for_mood(mood: list[str]) -> list[str]:
    for item in mood:
        if item in PALETTES:
            return PALETTES[item]
    return ["deep blue", "neon teal", "soft white"]


def _intensity(words: list[str], cues: list[LyricCue]) -> str:
    strong_words = {"burn", "break", "rush", "pressure", "fire", "pulse", "rise", "fall"}
    score = len(set(words) & strong_words)
    if len(cues) >= 24:
        score += 1
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _motion_for(mood: list[str], imagery: list[str], intensity: str) -> str:
    if intensity == "high":
        return "fast pulses with sharp bloom hits and rotating spectrum pressure"
    if "water motion" in imagery:
        return "slow ribbon waves with bass-driven swell"
    if "intimate" in mood:
        return "close, slow pressure waves with soft glow breathing"
    return "steady reactive orbit with gentle shader-field drift"
