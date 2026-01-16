class MariaDBRepository:
    def __init__(self, dsn: str = "") -> None:
        self.dsn = dsn

    def fetch_metadata(self, doc_id: str) -> dict:
        _ = doc_id
        # Stub: replace with read-only MariaDB queries.
        return {}
