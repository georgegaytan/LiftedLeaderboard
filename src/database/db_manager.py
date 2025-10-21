import logging
import os
from functools import wraps
from typing import Any, Callable, Iterable, List, Optional, Sequence, Tuple, TypeVar

T = TypeVar('T')

logger = logging.getLogger(__name__)

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # pragma: no cover
    psycopg = None  # type: ignore
    dict_row = None  # type: ignore

try:
    from psycopg_pool import ConnectionPool  # type: ignore
except Exception:  # pragma: no cover
    ConnectionPool = None  # type: ignore


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

    def __init__(self) -> None:
        self.engine: str = 'postgres'
        self._connected: bool = False
        # Any to avoid importing psycopg types at type-check time; guarded by asserts
        self._pg_conn: Any | None = None
        self._from_pool: bool = False

    # Shared pool across the process
    _pool: Any | None = None

    @classmethod
    def init_pool(
        cls,
        db_url: Optional[str] = None,
        min_size: int = 1,
        max_size: int = 10,
    ) -> None:
        '''Initialize a global connection pool for reuse across requests.'''
        if cls._pool is not None:
            return
        if psycopg is None:
            raise RuntimeError(
                'psycopg is not installed. Run: pip install "psycopg[binary,pool]"'
            )
        if ConnectionPool is None:
            raise RuntimeError(
                'psycopg_pool is not available. Run: pip install "psycopg[binary,pool]"'
            )

        conninfo = db_url or os.getenv('DATABASE_URL')
        if not conninfo:
            raise RuntimeError(
                'DATABASE_URL is not set. This project now requires Postgres.'
            )
        # Ensure row_factory is applied to connections from the pool
        cls._pool = ConnectionPool(
            conninfo=conninfo,
            min_size=min_size,
            max_size=max_size,
            kwargs={'row_factory': dict_row},
        )
        logger.info('Initialized Postgres connection pool')

    @classmethod
    def close_pool(cls) -> None:
        '''Close the global connection pool if it exists.'''
        if cls._pool is not None:
            try:
                cls._pool.close()
            finally:
                cls._pool = None

    def __enter__(self) -> 'DBManager':
        db_url = os.getenv('DATABASE_URL')
        if psycopg is None:
            raise RuntimeError(
                'psycopg is not installed. Run: pip install "psycopg[binary,pool]"'
            )
        if self.__class__._pool is not None:
            # Acquire from pool
            self._pg_conn = self.__class__._pool.getconn()
            self._from_pool = True
        else:
            if not db_url:
                raise RuntimeError(
                    'DATABASE_URL is not set. This project now requires Postgres.'
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
            if self._from_pool and self.__class__._pool is not None:
                try:
                    self.__class__._pool.putconn(self._pg_conn)
                finally:
                    self._pg_conn = None
                    self._from_pool = False
            else:
                self._pg_conn.close()
                self._pg_conn = None
        self._connected = False

    def _reconnect(self) -> None:
        '''Close current connection and open a new one.'''
        assert psycopg is not None

        try:
            if self._pg_conn is not None:
                if self._from_pool and self.__class__._pool is not None:
                    try:
                        # if conn is broken, pool will discard on put
                        self.__class__._pool.putconn(self._pg_conn)
                    finally:
                        self._pg_conn = None
                        self._from_pool = False
                else:
                    try:
                        self._pg_conn.close()
                    finally:
                        self._pg_conn = None
                        self._from_pool = False
        except Exception as e:  # best-effort close
            logger.warning(f'Error while closing connection during reconnect: {e}')

        # Open new connection
        if self.__class__._pool is not None:
            self._pg_conn = self.__class__._pool.getconn()
            self._from_pool = True
        else:
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise RuntimeError(
                    'DATABASE_URL is not set. This project now requires Postgres.'
                )
            self._pg_conn = psycopg.connect(db_url, row_factory=dict_row)

    def _run_with_retry(self, fn: Callable[[], T]) -> T:
        '''Run DB exec, reconn on OperationalError/InterfaceError, and retry once'''
        assert psycopg is not None
        try:
            return fn()
        except (psycopg.OperationalError, psycopg.InterfaceError) as e:
            logger.warning(
                f'DB operation failed due to connection issue: {e}. '
                f'Reconnecting and retrying once...'
            )
            self._reconnect()
            return fn()
        except Exception:
            logger.exception('Unexpected error during DB operation')
            raise

    def _exec_pg(self, query: str, params: Iterable[Any] | None) -> None:
        '''Execute a statement that does not return rows (INSERT, UPDATE, DELETE).'''
        assert self._pg_conn is not None
        with self._pg_conn.cursor() as cur:
            cur.execute(query, tuple(params or ()))

    def _select_pg(
        self, query: str, params: Iterable[Any] | None
    ) -> Tuple[List[dict[str, Any]], List[str]]:
        '''Execute a SELECT query and return (rows, column_names).'''
        assert self._pg_conn is not None
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
            self._run_with_retry(lambda: self._exec_pg(query, params))
        except Exception as e:
            logger.error(
                f'Postgres execute() error: {e}\nQuery: {query}\nParams: {params}'
            )
            raise

    @require_connection
    def executemany(self, query: str, param_list: Iterable[Sequence[Any]]) -> None:
        '''Execute a SQL statement against a sequence of parameter sets.'''

        def _do() -> None:
            assert self._pg_conn is not None
            with self._pg_conn.cursor() as cur:
                cur.executemany(query, list(param_list))

        try:
            self._run_with_retry(_do)
        except Exception as e:
            logger.error(f'Postgres executemany() error: {e}\nQuery: {query}')
            raise

    @require_connection
    def fetchall(
        self, query: str, params: Iterable[Any] | None = None
    ) -> List[dict[str, Any]]:
        '''Return all rows as a list of dictionaries.'''
        try:
            rows, _ = self._run_with_retry(lambda: self._select_pg(query, params))
            return rows
        except Exception as e:
            logger.error(
                f'Postgres fetchall() error: {e}\nQuery: {query}\nParams: {params}'
            )
            raise

    @require_connection
    def fetchone(
        self, query: str, params: Iterable[Any] | None = None
    ) -> Optional[dict[str, Any]]:
        '''Return a single row as a dictionary, or None if no result.'''
        try:
            rows, _ = self._run_with_retry(lambda: self._select_pg(query, params))
            return rows[0] if rows else None
        except Exception as e:
            logger.error(
                f'Postgres fetchone() error: {e}\nQuery: {query}\nParams: {params}'
            )
            raise
