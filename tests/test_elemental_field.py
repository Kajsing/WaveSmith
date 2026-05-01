from PIL import Image, ImageChops, ImageDraw

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext
from wavesmith.visuals.elemental_field import draw_elemental_field


def test_draw_elemental_field_changes_image() -> None:
    image = Image.new("RGB", (160, 90), (0, 0, 0))
    before = image.copy()
    ctx = FrameContext(
        image=image,
        draw=ImageDraw.Draw(image),
        width=160,
        height=90,
        time_seconds=1.25,
        progress=0.5,
        features={
            "rms": 0.7,
            "bass_energy": 0.8,
            "treble_energy": 0.6,
            "beat": True,
        },
        preset_name="test",
        palette_base=(34, 214, 255),
        palette_accent=(255, 76, 64),
        palette_beat=(255, 246, 210),
    )
    module = PresetModule(
        type="elemental_field",
        id="fire",
        element="fire",
        density=18,
        bands=3,
        opacity=0.7,
    )

    draw_elemental_field(ctx, module)

    assert ImageChops.difference(before, image).getbbox() is not None


def test_draw_natural_fire_behavior_changes_image() -> None:
    image = Image.new("RGB", (160, 90), (0, 0, 0))
    before = image.copy()
    ctx = FrameContext(
        image=image,
        draw=ImageDraw.Draw(image),
        width=160,
        height=90,
        time_seconds=2.5,
        progress=0.4,
        features={
            "rms": 0.55,
            "bass_energy": 0.72,
            "treble_energy": 0.35,
            "beat": False,
        },
        preset_name="test",
        palette_base=(255, 44, 18),
        palette_accent=(255, 118, 20),
        palette_beat=(255, 230, 92),
    )
    module = PresetModule(
        type="elemental_field",
        id="natural_fire",
        element="fire",
        behavior="natural",
        density=20,
        bands=3,
        opacity=0.8,
    )

    draw_elemental_field(ctx, module)

    assert ImageChops.difference(before, image).getbbox() is not None


def test_draw_natural_fire_accepts_line_texture() -> None:
    image = Image.new("RGB", (160, 90), (0, 0, 0))
    before = image.copy()
    ctx = FrameContext(
        image=image,
        draw=ImageDraw.Draw(image),
        width=160,
        height=90,
        time_seconds=3.0,
        progress=0.5,
        features={
            "rms": 0.4,
            "bass_energy": 0.5,
            "slow_bass": 0.62,
            "slow_mid": 0.35,
            "slow_pulse": 0.78,
            "beat_decay": 0.45,
            "tempo_bpm": 92.0,
            "treble_energy": 0.25,
            "beat": False,
        },
        preset_name="test",
        palette_base=(255, 44, 18),
        palette_accent=(255, 118, 20),
        palette_beat=(255, 230, 92),
    )
    module = PresetModule(
        type="elemental_field",
        id="textured_fire",
        element="fire",
        behavior="natural",
        line_texture="filament",
        density=20,
        bands=3,
        opacity=0.8,
        intensity_feature="slow_pulse",
        bass_feature="slow_bass",
        motion_feature="slow_mid",
    )

    draw_elemental_field(ctx, module)

    assert ImageChops.difference(before, image).getbbox() is not None


def test_draw_dual_fire_lines_behavior_changes_image() -> None:
    image = Image.new("RGB", (160, 90), (0, 0, 0))
    before = image.copy()
    ctx = FrameContext(
        image=image,
        draw=ImageDraw.Draw(image),
        width=160,
        height=90,
        time_seconds=1.75,
        progress=0.2,
        features={
            "rms": 0.76,
            "bass_energy": 0.64,
            "treble_energy": 0.82,
            "beat": True,
        },
        preset_name="test",
        palette_base=(255, 44, 18),
        palette_accent=(255, 118, 20),
        palette_beat=(255, 235, 132),
    )
    module = PresetModule(
        type="elemental_field",
        id="dual_lines",
        element="fire",
        behavior="dual_lines",
        line_texture="plasma",
        density=20,
        bands=2,
        opacity=0.8,
    )

    draw_elemental_field(ctx, module)

    assert ImageChops.difference(before, image).getbbox() is not None


def test_draw_dual_fire_lines_accepts_direction_options() -> None:
    image = Image.new("RGB", (160, 90), (0, 0, 0))
    before = image.copy()
    ctx = FrameContext(
        image=image,
        draw=ImageDraw.Draw(image),
        width=160,
        height=90,
        time_seconds=1.75,
        progress=0.2,
        features={
            "rms": 0.76,
            "bass_energy": 0.64,
            "left_energy": 0.7,
            "right_energy": 0.45,
            "left_bass": 0.55,
            "right_bass": 0.36,
            "left_treble": 0.42,
            "right_treble": 0.74,
            "treble_energy": 0.82,
            "beat": True,
        },
        preset_name="test",
        palette_base=(255, 44, 18),
        palette_accent=(255, 118, 20),
        palette_beat=(255, 235, 132),
    )
    module = PresetModule(
        type="elemental_field",
        id="dual_lines",
        element="fire",
        behavior="dual_lines",
        line_texture="plasma",
        line_direction="random",
        line_direction_seed="unit-test",
        density=20,
        bands=2,
        opacity=0.8,
    )

    draw_elemental_field(ctx, module)

    assert ImageChops.difference(before, image).getbbox() is not None


def test_draw_cracked_ice_sheet_behavior_changes_image() -> None:
    image = Image.new("RGB", (160, 90), (0, 0, 0))
    before = image.copy()
    ctx = FrameContext(
        image=image,
        draw=ImageDraw.Draw(image),
        width=160,
        height=90,
        time_seconds=2.2,
        progress=0.4,
        features={
            "rms": 0.45,
            "bass_energy": 0.58,
            "slow_pulse": 0.7,
            "treble_energy": 0.68,
            "spectrum": [0.1, 0.4, 0.8, 0.3, 0.65, 0.25, 0.5, 0.9],
            "beat": True,
        },
        preset_name="test",
        palette_base=(45, 170, 255),
        palette_accent=(145, 238, 255),
        palette_beat=(232, 252, 255),
    )
    module = PresetModule(
        type="elemental_field",
        id="cracked_ice",
        element="ice",
        behavior="cracked_sheet",
        line_texture="grain",
        density=36,
        bands=4,
        opacity=0.8,
        intensity_feature="slow_pulse",
        bass_feature="bass_energy",
        motion_feature="treble_energy",
    )

    draw_elemental_field(ctx, module)

    assert ImageChops.difference(before, image).getbbox() is not None


def test_draw_lightning_element_changes_image() -> None:
    image = Image.new("RGB", (160, 90), (0, 0, 0))
    before = image.copy()
    ctx = FrameContext(
        image=image,
        draw=ImageDraw.Draw(image),
        width=160,
        height=90,
        time_seconds=1.25,
        progress=0.5,
        features={
            "rms": 0.7,
            "bass_energy": 0.8,
            "treble_energy": 0.9,
            "beat": True,
        },
        preset_name="test",
        palette_base=(34, 214, 255),
        palette_accent=(255, 76, 64),
        palette_beat=(255, 246, 210),
    )
    module = PresetModule(
        type="elemental_field",
        id="lightning",
        element="lightning",
        density=24,
        bands=5,
        opacity=0.8,
    )

    draw_elemental_field(ctx, module)

    assert ImageChops.difference(before, image).getbbox() is not None
