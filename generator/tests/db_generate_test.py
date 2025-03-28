import os
import duckdb
from faker import Faker
from faker.providers import lorem
import pytest
from generator.models import DbClient, DBWriter, TextMessage




SUPABASE_DB_HOST = os.getenv("SUPABASE_DB_HOST", "localhost")
SUPABASE_DB_PORT = os.getenv("SUPABASE_DB_PORT", "5432")
SUPABASE_DB_USER = os.getenv("SUPABASE_DB_USER", "postgres")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", "postgres")
TABLE = 'test'

@pytest.mark.dependency(name='a')
def test_connection():
    # supervisor transaction connection
    client = DbClient(dbname="postgres", user=SUPABASE_DB_USER, password=SUPABASE_DB_PASSWORD, host=SUPABASE_DB_HOST, port=SUPABASE_DB_PORT)
    with client.cursor() as cur:
        cur.execute("SELECT 1;")
        values = cur.fetchone()
        assert values

@pytest.mark.dependency(name='b', depends=["a"])
def test_db_generate():
    client = DbClient(dbname="postgres", user=SUPABASE_DB_USER, password=SUPABASE_DB_PASSWORD, host=SUPABASE_DB_HOST, port=SUPABASE_DB_PORT)
    schema = {'origin_id':'varchar',  'event_id': 'varchar', 'message': 'text', 'created_at': 'timestamptz'}
    # inserted_at, updated_at autogenerated
    generator = DBWriter(client=client, table_name=TABLE, primary_keys=["event_id"], create_table=True, schema=schema)
    fake = Faker()
    fake.add_provider(lorem)
    generator.send(
        message=TextMessage(fake.sentence),
        message_params={"nb_words": 15},
        max_time=1,
        random_rollback=0,
    )
@pytest.mark.dependency(name='c', depends=["b"])
def test_duckdb_connection():
    con = duckdb.connect()
    con.execute('INSTALL postgres; LOAD postgres;')
    postgres_con = f"dbname=postgres user={SUPABASE_DB_USER} host={SUPABASE_DB_HOST} password={SUPABASE_DB_PASSWORD} port={SUPABASE_DB_PORT}"
    stmt = f"""
        ATTACH '{postgres_con}'
        AS db (TYPE postgres, READ_ONLY, SCHEMA 'public');
    """
    con.execute(stmt)
    values = con.execute(f"""SELECT * FROM db.public.{TABLE};""").fetchall()
    assert values


@pytest.mark.dependency(depends=["c"])
def test_cleanup():
    client = DbClient(dbname="postgres", user=SUPABASE_DB_USER, password=SUPABASE_DB_PASSWORD, host=SUPABASE_DB_HOST, port=SUPABASE_DB_PORT)
    with client.cursor() as cur:
        cur.execute("DELETE FROM public.{}".format(TABLE))