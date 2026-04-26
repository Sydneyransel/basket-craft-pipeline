import sys
import pandas as pd
from sqlalchemy import text
from snowflake.connector.pandas_tools import write_pandas

from db import get_pg_engine, get_snowflake_connection


def _get_tables(pg_conn):
    result = pg_conn.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'raw' ORDER BY table_name")
    )
    return [row[0] for row in result]


def main():
    try:
        pg_engine = get_pg_engine()
        with get_snowflake_connection() as conn:
            with pg_engine.connect() as pg_conn:
                for table in _get_tables(pg_conn):
                    snowflake_name = "customers" if table == "users" else table
                    df = pd.read_sql(f"SELECT * FROM raw.{table}", pg_conn)
                    df.columns = df.columns.str.upper()
                    if table == "users":
                        df.rename(columns={"USER_ID": "CUSTOMER_ID"}, inplace=True)
                    write_pandas(
                        conn,
                        df,
                        table_name=snowflake_name.upper(),
                        overwrite=True,
                        auto_create_table=True,
                        quote_identifiers=False,
                    )
                    print(f"  {table} -> {snowflake_name.upper()}: {len(df)} rows loaded")
        print("Snowflake load complete.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
