from werkzeug.security import generate_password_hash
from app.db import get_db_connection

connection = get_db_connection()

# Add departments if they don't already exist
departments = ["Human Resources", "Engineering", "Sales", "Finance"]

for department in departments:
    connection.execute(
        "INSERT OR IGNORE INTO departments (department_name) VALUES (?)",
        (department,)
    )

# Create the initial Admin account
connection.execute(
    """
    INSERT OR IGNORE INTO users (username, password_hash, role)
    VALUES (?, ?, ?)
    """,
    (
        "admin",
        generate_password_hash("Admin@12345"),
        "Admin"
    )
)

connection.commit()
connection.close()

print("Initial data added successfully!")
print("Username: admin")
print("Password: Admin@12345")