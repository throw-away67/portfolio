from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

import psycopg
from psycopg import Connection

from .config import DbConfig


class DbError(Exception):
    pass


@dataclass(frozen=True)
class Db:
    cfg: DbConfig

    def connect(self) -> Connection:
        try:
            return psycopg.connect(
                host=self.cfg.host,
                port=self.cfg.port,
                dbname=self.cfg.name,
                user=self.cfg.user,
                password=self.cfg.password,
                sslmode=self.cfg.sslmode,
            )
        except Exception as e:
            raise DbError(
                "Cannot connect to database. Check config.toml [db] and that PostgreSQL is running."
            ) from e

    @contextmanager
    def session(self) -> Connection:
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Connection:
        conn = self.connect()
        try:
            conn.execute("BEGIN;")
            yield conn
            conn.execute("COMMIT;")
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()