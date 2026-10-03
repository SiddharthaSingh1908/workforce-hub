import re
import math
import sqlite3
from datetime import date

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os

from app.db import get_db_connection


load_dotenv()

app = Flask(__name__, template_folder="app/templates")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Enable CSRF protection for POST requests
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role


@login_manager.user_loader
def load_user(user_id):
    connection = get_db_connection()

    try:
        user = connection.execute(
            """
            SELECT user_id, username, role
            FROM users
            WHERE user_id = ? AND is_active = 1
            """,
            (user_id,)
        ).fetchone()
    finally:
        connection.close()

    if user:
        return User(user["user_id"], user["username"], user["role"])

    return None


def admin_required():
    if current_user.role != "Admin":
        flash("You do not have permission to perform that action.")
        return False

    return True


def validate_employee_form(connection, employee_id=None):
    """Validate employee form data. Returns (data, error_message)."""

    form = request.form

    employee_code = form.get("employee_code", "").strip()
    full_name = form.get("full_name", "").strip()
    email = form.get("email", "").strip().lower()
    phone = form.get("phone", "").strip()
    department_text = form.get("department_id", "").strip()
    designation = form.get("designation", "").strip()
    joining_date = form.get("joining_date", "").strip()
    salary_text = form.get("salary", "0").strip()
    status = form.get("status", "Active").strip()
    address = form.get("address", "").strip()

    # Required fields
    if not employee_code or not full_name or not email:
        return None, "Employee ID, Full Name, and Email are required."

    # Basic length checks
    if len(employee_code) > 30:
        return None, "Employee ID must be 30 characters or fewer."

    if len(full_name) > 100:
        return None, "Full Name must be 100 characters or fewer."

    if len(email) > 254:
        return None, "Email address is too long."

    # Email format
    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.fullmatch(email_pattern, email):
        return None, "Please enter a valid email address."

    # Phone length
    if len(phone) > 30:
        return None, "Phone number must be 30 characters or fewer."

    # Allowed status values
    allowed_statuses = {"Active", "On Leave", "Inactive"}

    if status not in allowed_statuses:
        return None, "Please select a valid employment status."

    # Salary validation
    try:
        salary = float(salary_text or "0")

        if not math.isfinite(salary) or salary < 0:
            return None, "Salary must be a valid non-negative number."

    except ValueError:
        return None, "Salary must be a valid non-negative number."

    # Joining date validation
    if joining_date:
        try:
            date.fromisoformat(joining_date)
        except ValueError:
            return None, "Please enter a valid joining date."

    # Department validation
    department_id = None

    if department_text:
        try:
            department_id = int(department_text)
        except ValueError:
            return None, "Please select a valid department."

        department = connection.execute(
            "SELECT department_id FROM departments WHERE department_id = ?",
            (department_id,)
        ).fetchone()

        if department is None:
            return None, "The selected department does not exist."

    # Check employee code/email uniqueness
    duplicate_query = """
        SELECT employee_id
        FROM employees
        WHERE (
            LOWER(employee_code) = LOWER(?)
            OR LOWER(email) = LOWER(?)
        )
    """

    duplicate_values = [employee_code, email]

    if employee_id is not None:
        duplicate_query += " AND employee_id != ?"
        duplicate_values.append(employee_id)

    duplicate = connection.execute(
        duplicate_query,
        duplicate_values
    ).fetchone()

    if duplicate:
        return None, "Employee ID or email already exists."

    data = {
        "employee_code": employee_code,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "department_id": department_id,
        "designation": designation,
        "joining_date": joining_date or None,
        "salary": salary,
        "status": status,
        "address": address
    }

    return data, None


# -------------------------
# LOGIN
# -------------------------

@app.route("/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = get_db_connection()

        try:
            user = connection.execute(
                """
                SELECT user_id, username, password_hash, role
                FROM users
                WHERE username = ? AND is_active = 1
                """,
                (username,)
            ).fetchone()
        finally:
            connection.close()

        if user and check_password_hash(user["password_hash"], password):
            login_user(User(user["user_id"], user["username"], user["role"]))
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.")

    return render_template("login.html")


# -------------------------
# DASHBOARD
# -------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    connection = get_db_connection()

    try:
        total_employees = connection.execute(
            "SELECT COUNT(*) FROM employees"
        ).fetchone()[0]

        active_employees = connection.execute(
            "SELECT COUNT(*) FROM employees WHERE status = 'Active'"
        ).fetchone()[0]

        total_departments = connection.execute(
            "SELECT COUNT(*) FROM departments"
        ).fetchone()[0]

        department_stats = connection.execute(
            """
            SELECT departments.department_name,
                   COUNT(employees.employee_id) AS employee_count
            FROM departments
            LEFT JOIN employees
                ON departments.department_id = employees.department_id
            GROUP BY departments.department_id, departments.department_name
            ORDER BY employee_count DESC, departments.department_name
            """
        ).fetchall()

        recent_employees = connection.execute(
            """
            SELECT employees.employee_code,
                   employees.full_name,
                   employees.designation,
                   employees.status,
                   departments.department_name
            FROM employees
            LEFT JOIN departments
                ON employees.department_id = departments.department_id
            ORDER BY employees.employee_id DESC
            LIMIT 5
            """
        ).fetchall()

    finally:
        connection.close()

    return render_template(
        "dashboard.html",
        username=current_user.username,
        role=current_user.role,
        total_employees=total_employees,
        active_employees=active_employees,
        total_departments=total_departments,
        department_stats=department_stats,
        recent_employees=recent_employees
    )


# -------------------------
# EMPLOYEE DIRECTORY
# -------------------------

@app.route("/employees")
@login_required
def employees():
    search = request.args.get("search", "").strip()

    connection = get_db_connection()

    try:
        employee_list = connection.execute(
            """
            SELECT employees.*, departments.department_name
            FROM employees
            LEFT JOIN departments
                ON employees.department_id = departments.department_id
            WHERE employees.full_name LIKE ?
               OR employees.employee_code LIKE ?
               OR employees.email LIKE ?
            ORDER BY employees.employee_id DESC
            """,
            (f"%{search}%", f"%{search}%", f"%{search}%")
        ).fetchall()

    finally:
        connection.close()

    return render_template(
        "employees.html",
        employees=employee_list,
        search=search
    )


# -------------------------
# ADD EMPLOYEE
# -------------------------

@app.route("/employees/add", methods=["GET", "POST"])
@login_required
def add_employee():
    if not admin_required():
        return redirect(url_for("employees"))

    connection = get_db_connection()

    try:
        departments = connection.execute(
            "SELECT * FROM departments ORDER BY department_name"
        ).fetchall()

        if request.method == "POST":
            data, error = validate_employee_form(connection)

            if error:
                flash(error)

            else:
                try:
                    connection.execute(
                        """
                        INSERT INTO employees
                        (
                            employee_code, full_name, email, phone,
                            department_id, designation, joining_date,
                            salary, status, address
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            data["employee_code"],
                            data["full_name"],
                            data["email"],
                            data["phone"],
                            data["department_id"],
                            data["designation"],
                            data["joining_date"],
                            data["salary"],
                            data["status"],
                            data["address"]
                        )
                    )

                    connection.commit()
                    flash("Employee added successfully.")
                    return redirect(url_for("employees"))

                except sqlite3.IntegrityError:
                    flash("Employee ID or email already exists.")

    finally:
        connection.close()

    return render_template(
        "employee_form.html",
        employee=None,
        departments=departments
    )


# -------------------------
# EDIT EMPLOYEE
# -------------------------

@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    if not admin_required():
        return redirect(url_for("employees"))

    connection = get_db_connection()

    try:
        employee = connection.execute(
            "SELECT * FROM employees WHERE employee_id = ?",
            (employee_id,)
        ).fetchone()

        departments = connection.execute(
            "SELECT * FROM departments ORDER BY department_name"
        ).fetchall()

        if employee is None:
            flash("Employee not found.")
            return redirect(url_for("employees"))

        if request.method == "POST":
            data, error = validate_employee_form(connection, employee_id)

            if error:
                flash(error)

            else:
                try:
                    connection.execute(
                        """
                        UPDATE employees
                        SET employee_code = ?, full_name = ?, email = ?,
                            phone = ?, department_id = ?, designation = ?,
                            joining_date = ?, salary = ?, status = ?, address = ?
                        WHERE employee_id = ?
                        """,
                        (
                            data["employee_code"],
                            data["full_name"],
                            data["email"],
                            data["phone"],
                            data["department_id"],
                            data["designation"],
                            data["joining_date"],
                            data["salary"],
                            data["status"],
                            data["address"],
                            employee_id
                        )
                    )

                    connection.commit()
                    flash("Employee updated successfully.")
                    return redirect(url_for("employees"))

                except sqlite3.IntegrityError:
                    flash("Employee ID or email already exists.")

    finally:
        connection.close()

    return render_template(
        "employee_form.html",
        employee=employee,
        departments=departments
    )


# -------------------------
# DELETE EMPLOYEE
# -------------------------

@app.route("/employees/<int:employee_id>/delete", methods=["POST"])
@login_required
def delete_employee(employee_id):
    if not admin_required():
        return redirect(url_for("employees"))

    connection = get_db_connection()

    try:
        connection.execute(
            "DELETE FROM employees WHERE employee_id = ?",
            (employee_id,)
        )
        connection.commit()

    finally:
        connection.close()

    flash("Employee deleted.")
    return redirect(url_for("employees"))


# -------------------------
# DEPARTMENT DIRECTORY
# -------------------------

@app.route("/departments", methods=["GET", "POST"])
@login_required
def departments():
    if not admin_required():
        return redirect(url_for("dashboard"))

    connection = get_db_connection()

    try:
        if request.method == "POST":
            department_name = request.form.get(
                "department_name", ""
            ).strip()

            description = request.form.get(
                "description", ""
            ).strip()

            if not department_name:
                flash("Department name is required.")

            else:
                try:
                    connection.execute(
                        """
                        INSERT INTO departments
                        (department_name, description)
                        VALUES (?, ?)
                        """,
                        (department_name, description)
                    )

                    connection.commit()
                    flash("Department added successfully.")
                    return redirect(url_for("departments"))

                except sqlite3.IntegrityError:
                    flash("That department name already exists.")

        department_list = connection.execute(
            """
            SELECT departments.*,
                   COUNT(employees.employee_id) AS employee_count
            FROM departments
            LEFT JOIN employees
                ON departments.department_id = employees.department_id
            GROUP BY departments.department_id
            ORDER BY departments.department_name
            """
        ).fetchall()

    finally:
        connection.close()

    return render_template(
        "departments.html",
        departments=department_list
    )


# -------------------------
# EDIT DEPARTMENT
# -------------------------

@app.route("/departments/<int:department_id>/edit", methods=["GET", "POST"])
@login_required
def edit_department(department_id):
    if not admin_required():
        return redirect(url_for("dashboard"))

    connection = get_db_connection()

    try:
        department = connection.execute(
            "SELECT * FROM departments WHERE department_id = ?",
            (department_id,)
        ).fetchone()

        if department is None:
            flash("Department not found.")
            return redirect(url_for("departments"))

        if request.method == "POST":
            department_name = request.form.get(
                "department_name", ""
            ).strip()

            description = request.form.get(
                "description", ""
            ).strip()

            if not department_name:
                flash("Department name is required.")

            else:
                try:
                    connection.execute(
                        """
                        UPDATE departments
                        SET department_name = ?, description = ?
                        WHERE department_id = ?
                        """,
                        (department_name, description, department_id)
                    )

                    connection.commit()
                    flash("Department updated successfully.")
                    return redirect(url_for("departments"))

                except sqlite3.IntegrityError:
                    flash("A department with that name already exists.")

    finally:
        connection.close()

    return render_template(
        "department_edit.html",
        department=department
    )


# -------------------------
# DELETE DEPARTMENT
# -------------------------

@app.route("/departments/<int:department_id>/delete", methods=["POST"])
@login_required
def delete_department(department_id):
    if not admin_required():
        return redirect(url_for("dashboard"))

    connection = get_db_connection()

    try:
        employee_count = connection.execute(
            "SELECT COUNT(*) FROM employees WHERE department_id = ?",
            (department_id,)
        ).fetchone()[0]

        if employee_count > 0:
            flash("Cannot delete a department that has employees assigned.")

        else:
            connection.execute(
                "DELETE FROM departments WHERE department_id = ?",
                (department_id,)
            )
            connection.commit()
            flash("Department deleted.")

    finally:
        connection.close()

    return redirect(url_for("departments"))


# -------------------------
# LOGOUT
# -------------------------

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run()