import logging
import os
from functools import wraps
from typing import Any, Callable, Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # pragma: no cover
    psycopg = None  # type: ignore
    dict_row = None  # type: ignore


def require_connection(func: Callable) -> Callable:
    '''Decorator to ensure DBManager is used within a context manager.'''

    @wraps(func)
    def wrapper(self: 'DBManager', *args, **kwargs) -> Any:
        if not self._connected:
            raise RuntimeError(
                'DBManager is not in a context. Use "with DBManager() as db:"'
            )
        return func(self, *args, **kwargs)

    return wrapper


class DBManager:
    '''Postgres DB manager'''

    def __init__(self):
        self.engine: str = 'postgres'
        self._connected = False
        self._pg_conn = None

    def __enter__(self) -> 'DBManager':
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise RuntimeError(
                'DATABASE_URL is not set. This project now requires Postgres.'
            )
        if psycopg is None:
            raise RuntimeError(
                'psycopg is not installed. Run: pip install "psycopg[binary,pool]"'
            )
        # autocommit off to mimic transaction behavior
        self._pg_conn = psycopg.connect(db_url, row_factory=dict_row)
        self._connected = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._connected:
            return
        try:
            if exc_type is None:
                self._pg_conn.commit()
            else:
                self._pg_conn.rollback()
        finally:
            self._pg_conn.close()
            self._pg_conn = None
        self._connected = False

    def _exec_pg(self, query: str, params: Iterable[Any] | None) -> None:
        '''Execute a statement that does not return rows (INSERT, UPDATE, DELETE).'''
        with self._pg_conn.cursor() as cur:
            cur.execute(query, tuple(params or ()))

    def _select_pg(
        self, query: str, params: Iterable[Any] | None
    ) -> Tuple[List[dict[str, Any]], List[str]]:
        '''Execute a SELECT query and return (rows, column_names).'''
        with self._pg_conn.cursor() as cur:
            cur.execute(query, tuple(params or ()))
            rows: List[dict[str, Any]] = cur.fetchall()
            cols: List[str] = (
                [d.name for d in cur.description] if cur.description else []
            )
            return rows, cols

    @require_connection
    def execute(self, query: str, params: Iterable[Any] | None = None) -> None:
        '''Execute a single SQL statement.'''
        try:
            self._exec_pg(query, params)
        except Exception as e:
            logger.error(
                f'Postgres execute() error: {e}\nQuery: {query}\nParams: {params}'
            )
            raise

    @require_connection
    def executemany(self, query: str, param_list: Iterable[Sequence[Any]]) -> None:
        '''Execute a SQL statement against a sequence of parameter sets.'''
        try:
            with self._pg_conn.cursor() as cur:
                cur.executemany(query, list(param_list))
        except Exception as e:
            logger.error(f'Postgres executemany() error: {e}\nQuery: {query}')
            raise

    @require_connection
    def fetchall(
        self, query: str, params: Iterable[Any] | None = None
    ) -> List[dict[str, Any]]:
        '''Return all rows as a list of dictionaries.'''
        rows, _ = self._select_pg(query, params)
        return rows

    @require_connection
    def fetchone(
        self, query: str, params: Iterable[Any] | None = None
    ) -> Optional[dict[str, Any]]:
        '''Return a single row as a dictionary, or None if no result.'''
        rows, _ = self._select_pg(query, params)
        return rows[0] if rows else None
