from app.infrastructure.database import _engine_configuration


def test_remote_asyncpg_defaults_to_tls():
    url, connect_args = _engine_configuration(
        "postgresql+asyncpg://user:password@db.example.com:5432/app"
    )
    assert url.host == "db.example.com"
    assert "sslmode" not in url.query
    assert connect_args == {"ssl": "require"}


def test_remote_asyncpg_translates_libpq_sslmode():
    url, connect_args = _engine_configuration(
        "postgresql+asyncpg://user:password@db.example.com:6543/app?sslmode=verify-full"
    )
    assert "sslmode" not in url.query
    assert connect_args == {"ssl": "verify-full"}


def test_remote_asyncpg_does_not_allow_tls_downgrade():
    _, connect_args = _engine_configuration(
        "postgresql+asyncpg://user:password@db.example.com:5432/app?sslmode=disable"
    )
    assert connect_args == {"ssl": "require"}


def test_local_asyncpg_does_not_force_tls():
    _, connect_args = _engine_configuration(
        "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/app"
    )
    assert connect_args == {}
