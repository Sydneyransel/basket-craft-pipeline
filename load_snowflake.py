import sys
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas

from db import get_pg_engine, get_snowflake_connection

TABLES = ["orders", "order_items", "products"]


def main():
    try:
        pg_engine = get_pg_engine()
        conn = get_snowflake_connection()

        for table in TABLES:
            with pg_engine.connect() as pg_conn:
                df = pd.read_sql(f"SELECT * FROM raw.{table}", pg_conn)
            df.columns = df.columns.str.upper()
            write_pandas(
                conn,
                df,
                table_name=table.upper(),
                overwrite=True,
                auto_create_table=True,
                quote_identifiers=False,
            )
            print(f"  {table}: {len(df)} rows loaded")

        conn.close()
        print("Snowflake load complete.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
