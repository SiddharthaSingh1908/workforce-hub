import sqlite3
from pathlib import Path

database_path = Path(__file__).parent / "instance" / "workforce.db"

connection = sqlite3.connect(database_path)

tables = connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("Tables found:")
for table in tables:
    print("-", table[0])

connection.close()