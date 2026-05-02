"""GPU capability probing for the optional ModernGL backend."""

from dataclasses import dataclass
from typing import Any

GPU_INSTALL_HINT = "Install GPU support with: pip install -e .[gpu]"


@dataclass(frozen=True)
class GpuCapability:
    """Result of probing the local GPU renderer."""

    available: bool
    backend: str
    renderer: str | None = None
    version: str | None = None
    error: str | None = None


def probe_gpu() -> GpuCapability:
    """Return whether ModernGL can create an offscreen rendering context."""
    try:
        ctx = create_standalone_context()
    except Exception as exc:
        return GpuCapability(
            available=False,
            backend="moderngl",
            error=str(exc),
        )

    try:
        renderer = _ctx_info(ctx, "GL_RENDERER")
        version = _ctx_info(ctx, "GL_VERSION")
    finally:
        ctx.release()

    return GpuCapability(
        available=True,
        backend="moderngl",
        renderer=renderer,
        version=version,
    )


def create_standalone_context() -> Any:
    """Create a standalone ModernGL context, preferring EGL in WSL/Linux."""
    try:
        import moderngl
    except ImportError as exc:
        raise RuntimeError(f"ModernGL is not installed. {GPU_INSTALL_HINT}") from exc

    errors: list[str] = []
    for backend in ("egl", None):
        try:
            if backend is None:
                return moderngl.create_standalone_context()
            return moderngl.create_standalone_context(backend=backend)
        except Exception as exc:
            errors.append(f"{backend or 'default'}: {exc}")
    details = "; ".join(errors)
    raise RuntimeError(f"Could not create a ModernGL context ({details}). {GPU_INSTALL_HINT}")


def _ctx_info(ctx: Any, key: str) -> str | None:
    info = getattr(ctx, "info", {})
    value = info.get(key) if isinstance(info, dict) else None
    return str(value) if value is not None else None
