import sys
import pandas as pd
from sqlalchemy import text

from db import get_mysql_engine, get_pg_engine

TABLES = ["orders", "order_items", "products"]


def main():
    try:
        mysql_engine = get_mysql_engine()
        pg_engine = get_pg_engine()

        for table in TABLES:
            with mysql_engine.connect() as conn:
                df = pd.read_sql(f"SELECT * FROM {table}", conn)
            df.to_sql(table, pg_engine, schema="public", if_exists="replace", index=False)
            print(f"  {table}: {len(df)} rows loaded")

        print("Extraction complete.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
