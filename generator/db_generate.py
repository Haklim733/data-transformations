import argparse
import logging
import os
import sys

from faker import Faker
from faker.providers import lorem
from generator.models import DbClient, DBWriter, TextMessage


RUNTIME_ENV = os.getenv("RUNTIME_ENV", "local")
DB_NAME = os.getenv("SUPABASE_DB_NAME", "postgres")
DB_USER = os.getenv("SUPABASE_DB_USER", "admin")
DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", "admin")
DB_HOST = os.getenv("SUPABASE_DB_HOST", "localhost")
DB_PORT = os.getenv("SUPABASE_DB_PORT", "5432")

logger = logging.getLogger(__name__)


def main(table: str, max_time: int):
    if not max_time:
        max_time = 120

    schema = {'origin_id':'varchar',  'event_id': 'varchar', 'message': 'text', 'created_at': 'timestamptz'}
    client = DbClient(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    generator = DBWriter(
        client=client,
        table_name=table,
        primary_keys=["event_id"],
        create_table=True,
        schema=schema
    )
    fake = Faker()
    fake.add_provider(lorem)
    generator.send(
        message=TextMessage(fake.sentence),
        message_params={"nb_words": 15},
        max_time=max_time,
        random_rollback=0,
    )


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--table",
        dest="table",
        required=True,
        help="table name",
    )
    parser.add_argument(
        "--max-time",
        dest="max_time",
        required=False,
        help="max time (sec) to generate messages",
    )

    argv = sys.argv[1:]
    known_args, _ = parser.parse_known_args(argv)

    max_time = 60
    if known_args.max_time:
        max_time = int(known_args.max_time)
    main(table=known_args.table, max_time=max_time)
