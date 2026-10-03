from app.db import get_db_connection

connection = get_db_connection()

result = connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("Database connection successful!")
print("Tables:", [row["name"] for row in result])

connection.close()