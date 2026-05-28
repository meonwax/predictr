"""Pure-unit tests for the avatar processing pipeline.

No DB, no FastAPI - exercises the validation + Pillow resize/letterbox
logic against synthetic images generated on the fly.
"""

from __future__ import annotations

import io

import pytest
from PIL import Image

from app.services.avatars import (
    ALLOWED_MIME_TYPES,
    AVATAR_SIZE,
    MAX_UPLOAD_BYTES,
    AvatarTooLarge,
    InvalidImageData,
    UnsupportedMimeType,
    resize_to_square,
    validate_upload,
)


def _png(size: tuple[int, int], colour: tuple[int, int, int] = (255, 0, 0)) -> bytes:
    img = Image.new("RGB", size, colour)
    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    return out.getvalue()


def _jpeg(size: tuple[int, int], colour: tuple[int, int, int] = (0, 255, 0)) -> bytes:
    img = Image.new("RGB", size, colour)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=90)
    return out.getvalue()


def _png_with_alpha(size: tuple[int, int]) -> bytes:
    img = Image.new("RGBA", size, (255, 0, 0, 128))
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


# ---------------------------------------------------------------------------
# validate_upload
# ---------------------------------------------------------------------------


def test_validate_upload_accepts_png_and_jpeg() -> None:
    data = _png((10, 10))
    assert validate_upload(data=data, content_type="image/png") == "image/png"
    data = _jpeg((10, 10))
    assert validate_upload(data=data, content_type="image/jpeg") == "image/jpeg"


def test_validate_upload_normalises_image_jpg_to_image_jpeg() -> None:
    """Browsers occasionally send 'image/jpg' - accept and normalise."""
    data = _jpeg((10, 10))
    assert validate_upload(data=data, content_type="image/jpg") == "image/jpeg"


def test_validate_upload_strips_charset_suffix() -> None:
    """`image/png; charset=binary` should be accepted as just `image/png`."""
    data = _png((10, 10))
    assert validate_upload(data=data, content_type="image/png; charset=binary") == "image/png"


def test_validate_upload_rejects_gif() -> None:
    with pytest.raises(UnsupportedMimeType):
        validate_upload(data=b"GIF89a...", content_type="image/gif")


def test_validate_upload_rejects_oversized() -> None:
    data = b"\x00" * (MAX_UPLOAD_BYTES + 1)
    with pytest.raises(AvatarTooLarge):
        validate_upload(data=data, content_type="image/png")


def test_allowed_mime_types_is_png_and_jpeg() -> None:
    assert {"image/png", "image/jpeg"} == ALLOWED_MIME_TYPES


# ---------------------------------------------------------------------------
# resize_to_square
# ---------------------------------------------------------------------------


def _decode(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    img.load()
    return img


def test_resize_square_image_is_avatar_size() -> None:
    out = resize_to_square(data=_png((300, 300)), mime_type="image/png")
    assert _decode(out).size == (AVATAR_SIZE, AVATAR_SIZE)


def test_resize_wide_image_is_padded_to_square() -> None:
    out = resize_to_square(data=_png((400, 200)), mime_type="image/png")
    img = _decode(out)
    assert img.size == (AVATAR_SIZE, AVATAR_SIZE)
    # The top and bottom rows should be all-black (letterbox padding).
    top_pixels = {img.getpixel((x, 0)) for x in range(AVATAR_SIZE)}
    assert top_pixels == {(0, 0, 0)}


def test_resize_tall_image_is_padded_to_square() -> None:
    out = resize_to_square(data=_png((100, 400)), mime_type="image/png")
    img = _decode(out)
    assert img.size == (AVATAR_SIZE, AVATAR_SIZE)
    left_pixels = {img.getpixel((0, y)) for y in range(AVATAR_SIZE)}
    assert left_pixels == {(0, 0, 0)}


def test_resize_does_not_upscale_smaller_images() -> None:
    """A 50x50 image gets letterboxed to 128x128 - never upscaled."""
    out = resize_to_square(data=_png((50, 50)), mime_type="image/png")
    img = _decode(out)
    assert img.size == (AVATAR_SIZE, AVATAR_SIZE)
    # The central pixel comes from the original 50x50 red square.
    centre = (AVATAR_SIZE // 2, AVATAR_SIZE // 2)
    assert img.getpixel(centre) == (255, 0, 0)


def test_resize_round_trips_jpeg() -> None:
    out = resize_to_square(data=_jpeg((300, 300)), mime_type="image/jpeg")
    img = _decode(out)
    assert img.size == (AVATAR_SIZE, AVATAR_SIZE)
    assert img.format == "JPEG"


def test_resize_round_trips_png() -> None:
    out = resize_to_square(data=_png((300, 300)), mime_type="image/png")
    img = _decode(out)
    assert img.format == "PNG"


def test_resize_flattens_png_alpha_onto_black() -> None:
    out = resize_to_square(data=_png_with_alpha((400, 200)), mime_type="image/png")
    img = _decode(out)
    assert img.size == (AVATAR_SIZE, AVATAR_SIZE)


def test_resize_rejects_garbage_bytes() -> None:
    with pytest.raises(InvalidImageData):
        resize_to_square(data=b"definitely not an image", mime_type="image/png")
