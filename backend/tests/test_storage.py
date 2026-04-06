from pathlib import Path

import pytest

import app.storage as storage_module
from app.storage import delete_file, read_file, save_file


@pytest.fixture(autouse=True)
def tmp_upload(tmp_path, monkeypatch):
    """Point storage at a temp directory for each test."""
    monkeypatch.setattr(storage_module, "_upload_dir", lambda: tmp_path)


def test_save_and_read_file():
    path = save_file(b"hello world", "test.txt")
    assert Path(path).exists()
    assert read_file(path) == b"hello world"


def test_delete_file():
    path = save_file(b"data", "del.txt")
    delete_file(path)
    assert not Path(path).exists()


def test_delete_missing_file_is_silent():
    delete_file("/nonexistent/path/file.txt")  # should not raise
