from abc import ABC, abstractmethod
from contextlib import contextmanager
import datetime
import logging
import random
import requests
import time
import typing
import uuid


from faker import Faker
from faker.providers import lorem
import psycopg
from psycopg import sql

logger = logging.getLogger(__name__)


class DbClient:
    def __init__(self, dbname, user, password, host="localhost", port=5432):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None

    def connect(self):
        if self.conn is None or self.conn.closed:
            self.conn = psycopg.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
            )
            self.conn.autocommit = False

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()
            self.conn = None

    def cursor(self):
        return self.conn.cursor()

    @contextmanager
    def cursor(self, force_rollback=False):
        self.connect()
        cursor = self.conn.cursor()
        try:
            yield cursor
            if force_rollback:
                logger.info("TRANSACTION - ROLLBACK (forced)")
                self.conn.rollback()
            else:
                logger.info("TRANSACTION - COMMIT")
                self.conn.commit()
        except Exception as e:
            logger.info("TRANSACTION - ROLLBACK (exception)")
            self.conn.rollback()
            raise e
        finally:
            cursor.close()

    def execute(self, stmt: str, values: list[str] = None, rollback: bool = False, fetch: bool = False):
        with self.cursor(force_rollback=rollback) as cur:
            if values:
                cur.execute(stmt, values)
            else:
                cur.execute(stmt)
            
            result = None
            if fetch:
                result = cur.fetchall()
            
            return result

    def upsert(
        self,
        table_name: str,
        data: tuple[str | int],
        primary_key: list[str],
        random_rollback: float = 0,
    ):
        """
        Upsert data into the specified table.

        Args:
        - table_name (str): Name of the table to upsert data into.
        - data (dict): Dictionary containing the data to upsert.
        - primary_key (str): Name of the primary key column.
        - random_rollback (float): Probability of rolling back the transaction. Between 0 and 1 (inclusive)
        Returns:
        - None
        """
        columns = sql.SQL(", ").join([sql.Identifier(key) for key in data.keys()])

        upsert_query = sql.SQL(
            """
            INSERT INTO {table} ({columns})
            VALUES ({values})
            ON CONFLICT ({primary_key}) DO UPDATE
            SET {updates}
        """
        ).format(
            table=sql.Identifier(table_name),
            columns=columns,
            values=sql.SQL(", ").join(
                (
                    sql.SQL("({})").format(sql.Placeholder())
                )
                for key in data.keys()
            ),
            primary_key=sql.SQL(", ").join(
                [sql.Identifier(key) for key in primary_key]
            ),
            updates=sql.SQL(", ").join(
                sql.SQL("{0} = EXCLUDED.{0}").format(sql.Identifier(key))
                for key in data.keys()
                if key not in primary_key
            ),
        )

        if random.random() < random_rollback:
            self.execute(upsert_query, list(data.values()), rollback=True)
        else:
            self.execute(upsert_query, list(data.values()), rollback=False)


class Message(ABC):
    def __init__(self, generate_method: typing.Callable) -> dict[str, typing.Any]:
        self.generate_method = generate_method

    @abstractmethod
    def generate(self):
        raise NotImplementedError


class TextMessage(Message):

    def generate(self, **kwargs):
        created_at = datetime.datetime.now(datetime.timezone.utc) 
        message = self.generate_method(**kwargs)
        event_id: str = uuid.uuid4().hex
        return {"message": message, "created_at": created_at, "event_id": event_id}


class Generator(ABC):
    def __init__(self, client: DbClient) -> None:
        self.origin_id = uuid.uuid4().hex
        self.client = client

    @abstractmethod
    def send(self, message: Message):
        raise NotImplementedError
    


class DBWriter(Generator):
    def __init__(
        self,
        client: DbClient,
        table_name: str,
        primary_keys: list[str],
        schema: dict[str, str] = {},
        recreate_table: bool = False,
    ):
        super().__init__(client)
        self.client = client
        self.table_name: str = table_name
        self.schema: dict[str, str] = schema
        self.primary_keys: list[str] = primary_keys

        if recreate_table:
            self._drop_table()
        self._create_table()

    def _drop_table(self):
        query = sql.SQL(
            """
            DROP TABLE IF EXISTS {table};
        """
        ).format(
            table=sql.Identifier(self.table_name),
        )
        self.client.execute(query)

    def _create_table(self):
        if not self.schema:
            raise Exception("Schema is empty")

        columns = [
            sql.SQL("{} {}").format(sql.Identifier(key), sql.SQL(value))
            for key, value in self.schema.items()
            if key != "primary_key"
        ]
        primary_key_constraint = sql.SQL("PRIMARY KEY ({})").format(
            sql.SQL(", ").join([sql.Identifier(key) for key in self.primary_keys])
        )

        query = sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {table} (
                {columns},
                {primary_key_constraint},
                inserted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """
        ).format(
            table=sql.Identifier(self.table_name),
            columns=sql.SQL(", ").join(columns),
            primary_key_constraint=primary_key_constraint,
        )
        self.client.execute(query)

    def send(
        self,
        *,
        max_time: int,
        message: Message,
        message_params: dict[str, typing.Any] = {},
        random_rollback: float = 0,
    ):
        start_time = time.time()
        while time.time() - start_time < max_time:
            data = message.generate(**message_params)
            server_time = self.client.execute("SELECT NOW() AT TIME ZONE 'UTC'", fetch=True) # time skew fix
            created_at = server_time[0][0]
            data.update({"origin_id": self.origin_id, "created_at": created_at})
            logger.info(f"writing record- {data}")
            self.client.upsert(
                self.table_name,
                data,
                primary_key=["event_id"],
                random_rollback=random_rollback,
            )
            # sleep_time = random.uniform(0.1, 1.0)  # Sleep for 100-1000 milliseconds
            sleep_time = 1
            time.sleep(sleep_time)


if __name__ == "__main__":
    from unittest.mock import MagicMock

    client = MagicMock()
    generator = DBWriter(client=client)
    fake = Faker()
    fake.add_provider(lorem)
    generator.publish(
        topic="test",
        message=TextMessage(fake.sentence),
        message_params={"nb_words": 15},
        max_time=2,
    )
