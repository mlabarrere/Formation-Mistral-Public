"""Serveur MCP local — base Chinook en lecture seule.

Usage (stdio, lancé automatiquement par le notebook) :
    python mcp_chinook.py
"""
from pathlib import Path
import sqlite3

from mcp.server.fastmcp import FastMCP

DB_PATH = Path(__file__).parent / "data" / "Chinook.db"

mcp = FastMCP("chinook")


@mcp.tool()
def list_tables() -> list[str]:
    """Return the sorted list of tables available in the Chinook database."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    return [row[0] for row in rows]


@mcp.tool()
def query_chinook(sql: str) -> str:
    """Execute a read-only SELECT (or WITH) query on Chinook and return up to 10 rows.

    Tables: Album, Artist, Customer, Employee, Genre, Invoice,
    InvoiceLine, MediaType, Playlist, PlaylistTrack, Track.
    Only SELECT or WITH queries are accepted.
    """
    stmt = sql.strip()
    if not stmt.upper().startswith(("SELECT", "WITH")):
        return "Erreur : seules les requêtes SELECT ou WITH sont autorisées."
    if ";" in stmt.rstrip(";"):
        return "Erreur : une seule instruction SQL est autorisée."
    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
        try:
            cursor = conn.execute(stmt)
            cols = [d[0] for d in cursor.description]
            rows = cursor.fetchmany(10)
            return str([dict(zip(cols, row)) for row in rows])
        except Exception as exc:
            return f"Erreur SQL : {exc}"


if __name__ == "__main__":
    mcp.run()
