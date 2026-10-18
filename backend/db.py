"""
CartCompass-BI - Database Access Layer
Safely manages SQLite connections with foreign key enforcement and parameterized execution.
"""

import sqlite3
from flask import g, current_app
from backend.config import Config


def get_db_connection(db_path=None):
    """
    Establish a connection to the SQLite database.
    Enforces foreign keys and configures row factory for dictionary-like access.
    """
    if db_path is None:
        if current_app:
            db_path = current_app.config.get("DATABASE_PATH", Config.DATABASE_PATH)
        else:
            db_path = Config.DATABASE_PATH

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    """
    Get or create thread-local database connection stored on Flask's g object.
    """
    if "db" not in g:
        g.db = get_db_connection()
    return g.db


def close_db(e=None):
    """
    Close database connection at end of request.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False, conn=None):
    """
    Helper to execute parameterized SQL query and return dict or list of dicts.
    """
    close_after = False
    if conn is None:
        try:
            conn = get_db()
        except RuntimeError:
            # Outside request context
            conn = get_db_connection()
            close_after = True

    try:
        cursor = conn.cursor()
        cursor.execute(query, args)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        return (result[0] if result else None) if one else result
    finally:
        if close_after:
            conn.close()
