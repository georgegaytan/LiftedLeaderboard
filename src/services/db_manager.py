import logging
import os
import sqlite3
from typing import Iterable, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'data', 'wellness.db'
)


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

    def execute(self, query: str, params: Iterable | None = None) -> None:
        '''Execute a write operation (INSERT, UPDATE, DELETE).'''
        if not self.conn:
            raise RuntimeError(
                'DBManager is not in a context. Use "with DBManager() as db:"'
            )
        try:
            self.conn.execute(query, tuple(params or ()))
        except sqlite3.Error as e:
            logger.error(
                f'SQLite execute() error: {e}\nQuery: {query}\nParams: {params}'
            )
            raise

    def fetchall(self, query: str, params: Iterable | None = None) -> List[sqlite3.Row]:
        '''Fetch all rows from a SELECT query.'''
        if not self.conn:
            raise RuntimeError(
                'DBManager is not in a context. Use "with DBManager() as db:"'
            )
        cur = self.conn.execute(query, tuple(params or ()))
        return cur.fetchall()

    def fetchone(
        self, query: str, params: Iterable | None = None
    ) -> Optional[sqlite3.Row]:
        '''Fetch a single row from a SELECT query.'''
        rows = self.fetchall(query, params)
        return rows[0] if rows else None
