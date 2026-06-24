import hashlib

from visual_underwriting.schemas import ImageValidationResult


class ImageValidationError(ValueError):
    pass


def detect_image_mime_type(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    if content.startswith(b"BM"):
        return "image/bmp"
    if content.startswith((b"II*\x00", b"MM\x00*")):
        return "image/tiff"
    return None


def validate_image_upload(content: bytes, max_image_bytes: int) -> ImageValidationResult:
    if not content:
        raise ImageValidationError("image file is required")
    if len(content) > max_image_bytes:
        raise ImageValidationError(f"image file exceeds {max_image_bytes} byte limit")

    mime_type = detect_image_mime_type(content)
    if mime_type is None:
        raise ImageValidationError("uploaded file is not a supported image")

    return ImageValidationResult(
        content=content,
        sha256=hashlib.sha256(content).hexdigest(),
        mime_type=mime_type,  # type: ignore[arg-type]
        size_bytes=len(content),
    )
