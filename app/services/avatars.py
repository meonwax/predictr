"""Avatar storage + image processing.

User-uploaded images are normalised before being persisted:

1. **Validated** for size (<= 200 KiB) and mime type (PNG or JPEG only).
2. **Resized** to fit inside a 128x128 box, preserving the original aspect
   ratio.
3. **Padded** to an exact 128x128 square with a black background, so the
   downstream <img> tags in templates don't have to fight with variable
   aspect ratios.
4. **Re-encoded** with the same mime type - Pillow guarantees we ship valid
   image bytes even if the upload was subtly malformed (which is also a
   tiny piece of defence-in-depth: the round-trip strips most embedded
   payloads).

Storage is via the existing ``avatar`` table (BLOB column + mime type). A
1:1 link lives on the ``users.avatar_id`` foreign key.
"""

from __future__ import annotations

import io
import logging
from typing import Final

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.models import Avatar, User

LOGGER = logging.getLogger(__name__)

# Maximum accepted upload size, in bytes. Anything bigger is rejected before
# the image is even decoded.
MAX_UPLOAD_BYTES: Final[int] = 200 * 1024

# Mime types the UI accepts.
ALLOWED_MIME_TYPES: Final[frozenset[str]] = frozenset({"image/png", "image/jpeg"})

# Output canvas: every avatar ends up at this exact square pixel size.
AVATAR_SIZE: Final[int] = 128

# Background colour used when the source isn't square and we need to letterbox.
_BG_COLOUR: Final[tuple[int, int, int]] = (0, 0, 0)


class AvatarTooLarge(ValueError):
    """Raised when the uploaded file exceeds :data:`MAX_UPLOAD_BYTES`."""


class UnsupportedMimeType(ValueError):
    """Raised when the uploaded file is not a PNG or JPEG."""


class InvalidImageData(ValueError):
    """Raised when the uploaded bytes cannot be decoded as an image."""


# ---------------------------------------------------------------------------
# Validation + processing
# ---------------------------------------------------------------------------


def validate_upload(*, data: bytes, content_type: str) -> str:
    """Validate *data* and return the normalised mime type.

    Normalises ``image/jpg`` -> ``image/jpeg`` (browsers occasionally send
    the former, but Pillow only knows the canonical one).
    """
    if len(data) > MAX_UPLOAD_BYTES:
        raise AvatarTooLarge(f"Avatar must be no larger than {MAX_UPLOAD_BYTES // 1024} KiB.")
    ct = content_type.split(";", 1)[0].strip().lower()
    if ct == "image/jpg":
        ct = "image/jpeg"
    if ct not in ALLOWED_MIME_TYPES:
        raise UnsupportedMimeType("Only PNG and JPEG avatars are supported.")
    return ct


def resize_to_square(*, data: bytes, mime_type: str) -> bytes:
    """Decode *data*, resize it to fit, letterbox to a square, return new bytes.

    The output is encoded with the same image format the client uploaded
    (PNG or JPEG) so the stored mime type stays accurate.
    """
    try:
        with Image.open(io.BytesIO(data)) as src:
            src.load()
            # JPEGs may carry an EXIF orientation flag - apply it now so the
            # stored bytes already look "right way up". We move from the
            # ``ImageFile`` returned by ``Image.open`` onto an ``Image.Image``
            # here so the rest of the function works with the broader type.
            img: Image.Image = ImageOps.exif_transpose(src)

            # Pillow's ``thumbnail`` scales in-place, preserves aspect ratio,
            # only shrinks (never enlarges), and keeps the largest of (w, h)
            # at AVATAR_SIZE.
            img.thumbnail((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)

            # Letterbox onto a black square.
            if img.size != (AVATAR_SIZE, AVATAR_SIZE):
                canvas = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), _BG_COLOUR)
                offset = (
                    (AVATAR_SIZE - img.size[0]) // 2,
                    (AVATAR_SIZE - img.size[1]) // 2,
                )
                # If the source has alpha, composite it onto the canvas so
                # transparent regions reveal the black background instead of
                # showing up as white squares in JPEG output.
                if img.mode in ("RGBA", "LA"):
                    canvas.paste(img, offset, mask=img.split()[-1])
                else:
                    canvas.paste(img.convert("RGB"), offset)
                img = canvas
            elif img.mode != "RGB":
                img = img.convert("RGB")

            out = io.BytesIO()
            pil_format = "PNG" if mime_type == "image/png" else "JPEG"
            # PIL's save() takes a heterogenous mix of bool / int / str kwargs
            # depending on the format, so type the dict as ``object`` rather
            # than narrowing it to the type of the first inserted value.
            save_kwargs: dict[str, object] = {"optimize": True}
            if pil_format == "JPEG":
                save_kwargs["quality"] = 90
            img.save(out, format=pil_format, **save_kwargs)
            return out.getvalue()
    except UnidentifiedImageError as exc:
        raise InvalidImageData("Could not decode the uploaded file as an image.") from exc


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def set_avatar(
    db: Session,
    user: User,
    *,
    data: bytes,
    content_type: str,
) -> Avatar:
    """Replace (or create) the avatar attached to *user*.

    The returned :class:`Avatar` is bound to the session and refreshed, so
    callers can use ``avatar.id`` immediately after this call returns.
    """
    mime_type = validate_upload(data=data, content_type=content_type)
    resized = resize_to_square(data=data, mime_type=mime_type)

    if user.avatar is None:
        avatar = Avatar(data=resized, mime_type=mime_type)
        db.add(avatar)
        db.flush()
        user.avatar = avatar
    else:
        user.avatar.data = resized
        user.avatar.mime_type = mime_type
    db.commit()
    db.refresh(user)
    LOGGER.info("Avatar updated for user id=%d (%d bytes)", user.id, len(resized))
    return user.avatar


def delete_avatar(db: Session, user: User) -> None:
    """Remove the avatar attached to *user*, if any.

    No-op when the user has no avatar. The underlying ``avatar`` row is
    deleted along with the link.
    """
    if user.avatar is None:
        return
    avatar = user.avatar
    user.avatar = None
    db.flush()
    db.delete(avatar)
    db.commit()
    LOGGER.info("Avatar deleted for user id=%d", user.id)


def get_avatar(db: Session, user_id: int) -> Avatar | None:
    """Return the avatar for *user_id*, or ``None`` if either user or avatar is missing."""
    user = db.get(User, user_id)
    if user is None or user.avatar is None:
        return None
    return user.avatar


__all__ = [
    "MAX_UPLOAD_BYTES",
    "ALLOWED_MIME_TYPES",
    "AVATAR_SIZE",
    "AvatarTooLarge",
    "UnsupportedMimeType",
    "InvalidImageData",
    "validate_upload",
    "resize_to_square",
    "set_avatar",
    "delete_avatar",
    "get_avatar",
]
