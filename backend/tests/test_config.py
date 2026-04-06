from app.config import settings


def test_default_database_url():
    assert "sqlite" in settings.database_url


def test_default_upload_dir():
    assert settings.upload_dir == "./uploads"
