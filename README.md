# Workforce Hub – Employee Management System

A web-based Employee Management System built using **Python, Flask, and SQLite** to manage employee records, departments, and administrative operations through a simple dashboard.

## Features

* **Admin Login:** Secure login with password hashing.
* **Dashboard:** Overview of total employees, active employees, departments, and recent employee records.
* **Employee Management:** Add, view, edit, delete, and search employee records.
* **Department Management:** Create, view, edit, and delete departments.
* **Input Validation:** Validation for employee details, email addresses, salary, and duplicate records.
* **Role-Based Access:** Admin access control for management operations.
* **CSRF Protection:** Protection for form submissions.
* **Database Integration:** Persistent data storage using SQLite.

## Technology Stack

| Technology    | Purpose                   |
| ------------- | ------------------------- |
| Python        | Backend programming       |
| Flask         | Web framework             |
| SQLite        | Database                  |
| HTML          | Page structure            |
| CSS           | Styling                   |
| JavaScript    | Frontend interactions     |
| Flask-Login   | User authentication       |
| Flask-WTF     | CSRF protection           |
| python-dotenv | Environment configuration |
| Git & GitHub  | Version control           |

## Project Structure

```text
workforce-hub/
│
├── app/
│   ├── static/
│   ├── templates/
│   ├── __init__.py
│   └── db.py
│
├── database/
│   └── schema.sql
│
├── instance/
│   └── workforce.db
│
├── tests/
│
├── .env
├── .gitignore
├── app.py
├── init_db.py
├── seed_db.py
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/SiddharthaSingh1908/workforce-hub.git
cd workforce-hub
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
```

Use a strong, randomly generated secret key.

### 6. Initialize the database

```bash
python init_db.py
```

### 7. Seed the database

```bash
python seed_db.py
```

### 8. Run the application

```bash
python app.py
```

Open your browser and visit:

http://127.0.0.1:5000

## Security

* Passwords are stored using password hashing.
* CSRF protection is enabled.
* Sensitive environment variables are stored in `.env`.
* Database and virtual environment files are excluded from Git.

## Project Status

The core employee and department management functionality has been implemented. Further improvements and testing are planned.

## Author

**Siddhartha Singh**

GitHub: [SiddharthaSingh1908](https://github.com/SiddharthaSingh1908)

Repository: [Workforce Hub](https://github.com/SiddharthaSingh1908/workforce-hub)
