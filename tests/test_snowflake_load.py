def test_snowflake_connection(sf_conn):
    cur = sf_conn.cursor()
    cur.execute("SELECT 1")
    assert cur.fetchone()[0] == 1
