from typing import Any, ClassVar, Iterable, Optional, Sequence, cast

from psycopg.types.json import Json

from src.database.db_manager import DBManager


class BaseModel:
    table: ClassVar[str]
    pk: ClassVar[str] = 'id'

    @classmethod
    def get(cls, id_value: Any) -> Optional[dict[str, Any]]:
        with DBManager() as db:
            row = db.fetchone(
                f'SELECT * FROM {cls.table} WHERE {cls.pk} = %s', (id_value,)
            )
        return cast(Optional[dict[str, Any]], row)

    @classmethod
    def get_one(
        cls, where: str, params: Iterable[Any] = ()
    ) -> Optional[dict[str, Any]]:
        where_clause = f' WHERE {where}' if where else ''
        with DBManager() as db:
            row = db.fetchone(f'SELECT * FROM {cls.table}{where_clause}', tuple(params))
        return cast(Optional[dict[str, Any]], row)

    @classmethod
    def get_many(
        cls,
        where: str = '',
        params: Iterable[Any] = (),
        order_by: str = '',
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        query_parts: list[str] = [f'SELECT * FROM {cls.table}']
        parameters: tuple[Any, ...] = tuple(params)

        if where:
            query_parts.append(f'WHERE {where}')
        if order_by:
            query_parts.append(f'ORDER BY {order_by}')
        if limit is not None:
            query_parts.append('LIMIT %s')
            parameters = (*parameters, limit)

        query = ' '.join(query_parts)

        with DBManager() as db:
            rows = db.fetchall(query, parameters)
        return cast(list[dict[str, Any]], rows)

    @classmethod
    def create(cls, values: dict[str, Any]) -> dict[str, Any]:
        cols = list(values.keys())
        placeholders = ', '.join(['%s'] * len(cols))
        col_list = ', '.join(cols)
        sql_query = (
            f'INSERT INTO {cls.table} ({col_list}) VALUES ({placeholders}) RETURNING *'
        )

        # Convert dicts to JSON for Postgres JSON/JSONB columns
        params = [
            Json(values[c]) if isinstance(values[c], dict) else values[c] for c in cols
        ]

        with DBManager() as db:
            rows = db.fetchall(sql_query, tuple(params))
        rows = cast(list[dict[str, Any]], rows)
        return cast(dict[str, Any], rows[0]) if rows else cast(dict[str, Any], {})

    @classmethod
    def update(cls, id_value: Any, values: dict[str, Any]) -> dict[str, Any]:
        if not values:
            current = cls.get(id_value)
            return current if current is not None else cast(dict[str, Any], {})
        sets = ', '.join([f'{k} = %s' for k in values.keys()])
        sql = f'UPDATE {cls.table} SET {sets} WHERE {cls.pk} = %s RETURNING *'
        params = [*values.values(), id_value]
        with DBManager() as db:
            rows = db.fetchall(sql, tuple(params))
        rows = cast(list[dict[str, Any]], rows)
        return cast(dict[str, Any], rows[0]) if rows else cast(dict[str, Any], {})

    @classmethod
    def delete(cls, id_value: Any) -> None:
        with DBManager() as db:
            db.execute(f'DELETE FROM {cls.table} WHERE {cls.pk} = %s', (id_value,))

    @classmethod
    def exists(cls, where: str, params: Iterable[Any] = ()) -> bool:
        where_clause = f' WHERE {where}' if where else ''
        with DBManager() as db:
            row = db.fetchone(
                f'SELECT 1 FROM {cls.table}{where_clause} LIMIT 1', tuple(params)
            )
        return row is not None

    @classmethod
    def upsert(
        cls, conflict_cols: Sequence[str], values: dict[str, Any]
    ) -> dict[str, Any]:
        cols = list(values.keys())
        col_list = ', '.join(cols)
        placeholders = ', '.join(['%s'] * len(cols))
        conflict = ', '.join(conflict_cols)
        # Update all provided columns on conflict
        set_clause = ', '.join(
            [f'{c} = EXCLUDED.{c}' for c in cols if c not in conflict_cols]
        )
        if not set_clause:
            # If every column is in conflict set, just do nothing and return existing
            set_clause = f'{cls.pk} = {cls.table}.{cls.pk}'
        sql = (
            f'INSERT INTO {cls.table} ({col_list}) VALUES ({placeholders}) '
            f'ON CONFLICT ({conflict}) DO UPDATE SET {set_clause} RETURNING *'
        )
        params = tuple(values[c] for c in cols)
        with DBManager() as db:
            rows = db.fetchall(sql, params)
        rows = cast(list[dict[str, Any]], rows)
        return cast(dict[str, Any], rows[0]) if rows else cast(dict[str, Any], {})
