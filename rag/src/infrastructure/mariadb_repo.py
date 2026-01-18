from config import settings


class MariaDBRepository:
    def __init__(self, dsn: str = "") -> None:
        self.dsn = dsn or self._build_dsn()

    def fetch_metadata(self, doc_id: str) -> dict:
        _ = doc_id
        # Stub: replace with read-only MariaDB queries.
        return {}

    def _build_dsn(self) -> str:
        return (
            f"mariadb://{settings.mariadb_user}:{settings.mariadb_password}"
            f"@{settings.mariadb_host}:{settings.mariadb_port}/{settings.mariadb_database}"
        )
