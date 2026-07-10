#backend\app\core\file_validation.py
"""
File-upload validation (Sprint 7 MVP-1 follow-up).

Every route that accepts an UploadFile must validate it here rather than
calling `await file.read()` directly. That naive pattern reads the entire
stream into memory before we know how big it is — a client can OOM the
backend with a 500MB POST. It also trusts the filename and content-type
verbatim, which lets a caller sneak a .exe past a "jpg only" check just
by renaming it, or use a filename like "../../../etc/passwd" to write
S3 keys outside the intended path.

Two public entry points (both async):

  read_image_upload(file)     — accepts jpg/jpeg/png/webp, up to 10 MB
  read_document_upload(file)  — accepts pdf + all image types, up to 25 MB

Both return a ValidatedUpload with:
  .content            — the raw bytes (safe to hand to upload_file())
  .safe_filename      — ASCII-only, path-separator-stripped, safe for S3 keys
  .display_filename   — control-char-stripped, capped at 200; safe for DB
                        storage and audit-log JSON

Validation steps (in order):
  1. Extension is in the allow-list
  2. Body reads without exceeding max_bytes (streamed, not buffered)
  3. First bytes of the body match a known "magic number" (JPEG/PNG/WebP/PDF)
  4. The detected magic type is consistent with the claimed extension
     (a PDF-in-a-jpg-wrapper fails here)
  5. Filename is sanitized for downstream use

On any failure, raises HTTPException(400) with a message the frontend can
show verbatim. Callers don't need their own try/except.
"""
import re
from fastapi import HTTPException, UploadFile


# ─── Public constants ─────────────────────────────────────────────────────

MAX_IMAGE_MB = 10
MAX_DOCUMENT_MB = 25

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
DOCUMENT_EXTENSIONS = IMAGE_EXTENSIONS | {"pdf"}


# ─── Internal magic-byte detection ────────────────────────────────────────
#
# We check the first bytes of the actual file content instead of trusting
# the client-supplied Content-Type header (which is trivially spoofable).

def _detect_magic(data: bytes) -> str:
    """Return the file type detected from magic bytes, or empty string.

    Recognises: 'jpeg', 'png', 'webp', 'pdf'. Anything else returns "".
    """
    if len(data) < 4:
        return ""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:4] == b"RIFF" and len(data) >= 12 and data[8:12] == b"WEBP":
        return "webp"
    if data.startswith(b"%PDF-"):
        return "pdf"
    return ""


# Which magic types are ACCEPTABLE for a given extension. `.jpg` and `.jpeg`
# both map to JPEG magic bytes; everything else is 1-to-1.
_EXT_TO_MAGIC = {
    "jpg": "jpeg",
    "jpeg": "jpeg",
    "png": "png",
    "webp": "webp",
    "pdf": "pdf",
}


# ─── Filename helpers ─────────────────────────────────────────────────────

_UNSAFE_S3_CHARS = re.compile(r"[^A-Za-z0-9._\-]")


def _extension_of(filename: str) -> str:
    """Lowercase file extension without the leading dot; empty if none."""
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower().strip()


def _basename(filename: str) -> str:
    """Strip any path components — defense against '../../evil' filenames.

    Handles both forward and back slashes so we don't rely on os.path (which
    behaves differently on Windows vs Linux).
    """
    if not filename:
        return ""
    return filename.replace("\\", "/").rsplit("/", 1)[-1]


def _safe_s3_filename(filename: str) -> str:
    """Sanitize a filename for use as part of an S3 key.

    Keeps only [A-Za-z0-9._-]; replaces anything else with underscore.
    Caps length at 100 chars. If the result would start with a dot or be
    empty, prepends 'file' so we always have a proper base.
    """
    base = _basename(filename)
    safe = _UNSAFE_S3_CHARS.sub("_", base)[:100]
    if not safe or safe.startswith("."):
        safe = "file" + safe
    return safe


def _display_filename(filename: str) -> str:
    """Sanitize a filename for display / DB storage / audit-log JSON.

    Less aggressive than _safe_s3_filename: unicode is preserved so a
    tenant who uploaded 'contrato-María.pdf' still sees that in their UI.
    Only control characters (0x00-0x1F, 0x7F) are stripped, plus any path
    components. Capped at 200 chars.
    """
    base = _basename(filename)
    cleaned = "".join(ch for ch in base if ord(ch) >= 0x20 and ord(ch) != 0x7F)
    return cleaned[:200] or "file"


# ─── Bounded streaming reader ─────────────────────────────────────────────

async def _read_bounded(file: UploadFile, max_bytes: int) -> bytes:
    """Read the UploadFile in 64 KB chunks, aborting as soon as we exceed
    max_bytes. Prevents a large upload from being fully buffered into memory
    before we check its size."""
    chunks = []
    total = 0
    chunk_size = 64 * 1024
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File too large. Maximum size is "
                    f"{max_bytes // (1024 * 1024)} MB."
                ),
            )
        chunks.append(chunk)
    return b"".join(chunks)


# ─── Public result type ───────────────────────────────────────────────────

class ValidatedUpload:
    """Result of a successful file-upload validation.

    Attributes:
        content:          the raw file bytes; hand this to upload_file().
        safe_filename:    ASCII-only filename component for S3 keys.
        display_filename: gentler sanitization for user-facing display /
                          DB storage / audit-log JSON.
    """
    __slots__ = ("content", "safe_filename", "display_filename")

    def __init__(self, content: bytes, safe_filename: str, display_filename: str):
        self.content = content
        self.safe_filename = safe_filename
        self.display_filename = display_filename


# ─── The main validator ───────────────────────────────────────────────────

async def _validate_and_read(
    file: UploadFile,
    *,
    max_bytes: int,
    allowed_extensions: set,
) -> ValidatedUpload:
    filename = file.filename or ""

    # 1. Extension check — cheap; do this before reading bytes.
    ext = _extension_of(filename)
    if not ext or ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type. Allowed: "
                f"{', '.join(sorted(allowed_extensions))}."
            ),
        )

    # 2. Read bytes with the size cap enforced mid-stream.
    content = await _read_bounded(file, max_bytes)
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 3. Magic-byte check — catches a .exe renamed to .jpg (unknown magic)
    #    and a genuine PDF renamed to .jpg (magic doesn't match extension).
    magic = _detect_magic(content)
    if not magic:
        raise HTTPException(
            status_code=400,
            detail=(
                "File content is not a recognised image or PDF. "
                "Please upload a valid file."
            ),
        )

    # 4. Extension must be consistent with the actual content.
    expected_magic = _EXT_TO_MAGIC.get(ext)
    if expected_magic != magic:
        raise HTTPException(
            status_code=400,
            detail=(
                f"File extension '.{ext}' does not match the actual content "
                f"(detected {magic.upper()}). Upload rejected."
            ),
        )

    return ValidatedUpload(
        content=content,
        safe_filename=_safe_s3_filename(filename),
        display_filename=_display_filename(filename),
    )


# ─── Public entry points ──────────────────────────────────────────────────

async def read_image_upload(file: UploadFile) -> ValidatedUpload:
    """Validate + read an image upload (jpg/jpeg/png/webp, ≤10 MB)."""
    return await _validate_and_read(
        file,
        max_bytes=MAX_IMAGE_MB * 1024 * 1024,
        allowed_extensions=IMAGE_EXTENSIONS,
    )


async def read_document_upload(file: UploadFile) -> ValidatedUpload:
    """Validate + read a document upload (pdf + image types, ≤25 MB)."""
    return await _validate_and_read(
        file,
        max_bytes=MAX_DOCUMENT_MB * 1024 * 1024,
        allowed_extensions=DOCUMENT_EXTENSIONS,
    )