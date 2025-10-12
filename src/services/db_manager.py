import logging
import os
import sqlite3
from functools import wraps
from typing import Any, Callable, Iterable, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'data', 'wellness.db'
)


def require_connection(func: Callable) -> Callable:
    '''Decorator to ensure DBManager is used within a context manager.'''

    @wraps(func)
    def wrapper(self: 'DBManager', *args, **kwargs) -> Any:
        if not self.conn:
            raise RuntimeError(
                'DBManager is not in a context. Use "with DBManager() as db:"'
            )
        return func(self, *args, **kwargs)

    return wrapper


class DBManager:
    '''SQLite DB manager'''

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> 'DBManager':
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys = ON;')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()
            self.conn = None

    @require_connection
    def execute(self, query: str, params: Iterable | None = None) -> None:
        '''Execute a write operation (INSERT, UPDATE, DELETE).'''
        try:
            self.conn.execute(query, tuple(params or ()))  # type: ignore[union-attr]
        except sqlite3.Error as e:
            logger.error(
                f'SQLite execute() error: {e}\nQuery: {query}\nParams: {params}'
            )
            raise

    @require_connection
    def fetchall(self, query: str, params: Iterable | None = None) -> List[sqlite3.Row]:
        '''Fetch all rows from a SELECT query.'''
        cur = self.conn.execute(query, tuple(params or ()))  # type: ignore[union-attr]
        return cur.fetchall()

    @require_connection
    def fetchone(
        self, query: str, params: Iterable | None = None
    ) -> Optional[sqlite3.Row]:
        '''Fetch a single row from a SELECT query.'''
        cur = self.conn.execute(query, tuple(params or ()))  # type: ignore[union-attr]
        return cur.fetchone()  # type: ignore[no-any-return]
