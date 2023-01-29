from core.Constants import GLSL_MINIMAL_VERSION, GLSL_TARGET_VERSION, GL_API_MINIMAL_MAJOR_VERSION
from core.Exceptions import CompatibilityError
ENCODING = 'utf-8'


__all__ = [
    "get_version_API",
    "get_version_GLSL"
]


def get_version_API() -> [int, int]:
    import OpenGL.GL as GL

    GL_VERSION = GL.glGetString(GL.GL_VERSION)[:3].decode(ENCODING)
    GL_VERSION = [int(v) for v in GL_VERSION.split('.')]

    if GL_VERSION[0] < GL_API_MINIMAL_MAJOR_VERSION:
        raise CompatibilityError(
            f"Your major version of OpenGL API: {GL_VERSION[0]}\n"
            f"Required: {GL_API_MINIMAL_MAJOR_VERSION}"
        )

    return GL_VERSION


def get_version_GLSL() -> int:
    import OpenGL.GL as GL

    GLSL_VERSION = GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION)
    GLSL_VERSION = int( GLSL_VERSION.decode(ENCODING).split()[0][:5].replace('.', '') )

    if GLSL_VERSION < GLSL_MINIMAL_VERSION:
        raise CompatibilityError(
            f"Your GL Shading Language version: {GLSL_VERSION},"
            f"Minimal required: {GLSL_MINIMAL_VERSION}"
        )

    return min( GLSL_VERSION, GLSL_TARGET_VERSION )
