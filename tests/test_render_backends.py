import pytest

from wavesmith.render.backends import CpuRenderBackend, RenderBackendError, get_render_backend


def test_get_render_backend_returns_cpu() -> None:
    backend = get_render_backend("cpu")

    assert isinstance(backend, CpuRenderBackend)
    assert backend.name == "cpu"


def test_gpu_backend_fails_explicitly_when_iterated() -> None:
    backend = get_render_backend("gpu")

    with pytest.raises(RenderBackendError, match="not implemented"):
        next(
            backend.generate_frames(
                options=None,  # type: ignore[arg-type]
                duration_seconds=1.0,
                timeline=None,  # type: ignore[arg-type]
                preset=None,  # type: ignore[arg-type]
                lyrics=[],
                watermark_text=None,
            )
        )
