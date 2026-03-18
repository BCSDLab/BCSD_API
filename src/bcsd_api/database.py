from collections.abc import Iterator

from sqlalchemy import Connection, MetaData, create_engine as _create_engine

metadata = MetaData()


def create_engine(url: str):
    return _create_engine(url, pool_size=5, max_overflow=10)


def get_connection(engine) -> Iterator[Connection]:
    with engine.connect() as conn:
        yield conn
        conn.commit()
