from pathlib import Path

from app.config import settings


def _upload_dir() -> Path:
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_file(content: bytes, filename: str) -> str:
    """Save bytes to upload dir. Returns absolute path string."""
    dest = _upload_dir() / filename
    dest.write_bytes(content)
    return str(dest.resolve())


def delete_file(path: str) -> None:
    """Delete a file if it exists. Silently ignores missing files."""
    p = Path(path)
    if p.exists():
        p.unlink()


def read_file(path: str) -> bytes:
    """Read a stored file by path."""
    return Path(path).read_bytes()
