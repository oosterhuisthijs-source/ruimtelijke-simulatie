import pandas as pd
import duckdb


async def load_dataset(delta_table_path: str) -> pd.DataFrame:
    """Load the Delta table into a pandas DataFrame via DuckDB."""
    con = duckdb.connect()
    con.execute("INSTALL delta; LOAD delta;")
    df = con.execute(
        f"SELECT * FROM delta_scan('{delta_table_path}')"
    ).df()
    con.close()
    return df
