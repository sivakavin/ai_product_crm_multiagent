import sqlite3
from config import settings

def get_all_schemas() ->str:
    con = sqlite3.connect(settings.db_path)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_sequence")
    tables = [row[0] for row in cur.fetchall()]

    schemas = []

    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        cols = cur.fetchall()
        schema = f"{table}({', '.join(col[1] for col in cols)})"
        schemas.append(schema)
    con.close()

    return "\n".join(schemas)

def run_sql(query:str) ->str:
    con = sqlite3.connect(settings.db_path)

    try:
        rows = con.execute(query).fetchall()
        return str(rows)
    except Exception as e:
        return f"Error: {e}"
    finally:
        con.close()
