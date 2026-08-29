import sqlite3
from config import settings
# from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP

mcp = FastMCP("sql-server")



@mcp.tool()
def get_all_schemas() ->str:
    """ Get all the table schemas from the CRM database"""
    con = sqlite3.connect(settings.db_path)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cur.fetchall()]

    schemas = []
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        cols = cur.fetchall()
        schema = f"{table}({', '.join(col[1] for col in cols)})"
        schemas.append(schema)
    con.close()
    return "\n".join(schemas)

@mcp.tool()
def run_sql(query:str) ->str:
    """ Execute a read-only SQL query on the CRM database."""
    con = sqlite3.connect(settings.db_path)
    try:
        rows = con.execute(query).fetchall()
        return str(rows)
    except Exception as e:
        return f"Error: {e}"
    finally:
        con.close()

if __name__ == "__main__":
    mcp.run(transport="stdio")