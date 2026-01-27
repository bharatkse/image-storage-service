from collections.abc import Mapping

MAGIC_BYTES: Mapping[bytes, str] = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF": "image/webp",
}


def detect_mime_type(file_data: bytes) -> str:
    for signature, mime in MAGIC_BYTES.items():
        if file_data.startswith(signature):
            return mime

    raise ValueError("Unsupported or unknown file type")
