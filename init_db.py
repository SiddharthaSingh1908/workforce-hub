import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "instance"
DATABASE_PATH = DATABASE_DIR / "workforce.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"

DATABASE_DIR.mkdir(exist_ok=True)

connection = sqlite3.connect(DATABASE_PATH)

with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
    connection.executescript(schema_file.read())

connection.close()

print("Database initialized successfully!")
print(f"Database location: {DATABASE_PATH}")