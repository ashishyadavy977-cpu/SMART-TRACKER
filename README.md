# SMART TRACKER

Intelligent Student Life Tracking & Management System, built as a production-style TYBSc Computer Science final-year major project.

## Features

- Student registration, secure login, sessions, profile, and role-based admin access.
- Dashboard metrics and Chart.js study visualization with rule-based recommendations.
- CRUD task tracker with search, status/priority filters, due dates, and overdue highlighting.
- Study, attendance, expense, and goal trackers with validation and progress views.
- Printable reports for study, attendance, expenses, tasks, and goals.
- Admin dashboard, student activation/deactivation, and system-wide record views.

## Smart Tracker 2.0 Features

- Smart calendar API and activity view for tasks, study sessions, and goal deadlines.
- In-app notifications with unread counts, read-all, delete, and rule-based reminders.
- Productivity score from task completion, study time, attendance, goal progress, and consistency.
- Study targets, activity streaks, achievements, points, smart recommendations, and budget tracking.
- Responsive analytics endpoints, Chart.js-ready trend data, PDF reports, and admin announcements.

## Technology

Python 3.12+, Flask, Flask-SQLAlchemy, SQLAlchemy ORM, MySQL/PyMySQL, Jinja2, Bootstrap 5, Chart.js, HTML5, CSS3, and JavaScript.

## Requirements

Install Python 3.12 or newer and MySQL 8.0 or newer. On Windows, use PowerShell or the VS Code integrated terminal.

## Installation

```powershell
cd path\to\SMART-TRACKER
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process Bypass` in that terminal.

## MySQL setup

```sql
CREATE DATABASE smart_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'smart_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON smart_tracker.* TO 'smart_user'@'localhost';
FLUSH PRIVILEGES;
```

Set `DATABASE_URL=mysql+pymysql://smart_user:strong_password@localhost/smart_tracker` in `.env`. The default example uses SQLite for a zero-configuration evaluation run.

## Initialize and run

```powershell
python database\init_db.py
python app.py
```

Open `http://127.0.0.1:5000`.

## Demo credentials

- Admin: `admin@smarttracker.local` / `Admin@12345`
- Student: `student@smarttracker.local` / `Student@12345`

## Folder structure

```text
app.py, config.py, requirements.txt, .env.example
models/                 SQLAlchemy entities and relationships
routes/                 Feature and admin blueprints
templates/              Jinja pages and CRUD forms
static/css, static/js/  Responsive styles and Chart.js integration
database/init_db.py     Schema creation and sample data
services.py             Productivity, streak, recommendation, and notification logic
routes/smart.py         Smart Tracker 2.0 routes, APIs, PDF exports, and announcements
```

## Reports and Downloads

After signing in, PDF reports are available at `/reports/overall.pdf`, `/reports/tasks.pdf`, `/reports/study.pdf`, `/reports/attendance.pdf`, `/reports/expenses.pdf`, `/reports/goals.pdf`, and `/reports/productivity.pdf`.

## Testing

The project can be checked with:

```powershell
python -m py_compile app.py common.py services.py routes\*.py models\*.py database\init_db.py
python database\init_db.py
python app.py
```

The application preserves existing data because initialization uses `create_all()` and never drops tables. New Smart Tracker 2.0 tables are created additively.

## Screenshots

The responsive landing page, authenticated dashboard, Smart Calendar, Productivity Score, Notifications, Study Targets, Budget, and Admin Announcements views are available after running the application. Capture screenshots from the browser at desktop and mobile widths for the final project report.

## Future enhancements

Add CSRF protection with Flask-WTF, Alembic migrations, email reminders, recurring tasks, calendar integrations, and richer export formats.