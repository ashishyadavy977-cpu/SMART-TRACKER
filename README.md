# SMART TRACKER

Smart Tracker is a Flask-based student productivity and life-management application. It combines academic planning, study tracking, exams, assignments, habits, focus sessions, budgets, analytics, notifications, quizzes, and profile customization in one workspace.

## Implemented Features

### Core application

- Student registration, login/logout, secure password hashing, sessions, and authentication-protected routes.
- Student and administrator roles with admin user management and announcements.
- Responsive Bootstrap interface with existing light/dark theme support.
- Dashboard with tasks, study time, attendance, expenses, goals, exams, assignments, focus time, and habit streak signals.

### Phase 1

- Exam preparation tracker with exam CRUD, date/time, priority, syllabus, notes, topics, topic completion, automatic preparation percentage, and days remaining.
- Assignment tracker with CRUD, upload, download, replacement, deletion, safe filenames, allowed file types, size validation, and per-user access control.
- Habit tracker with create/edit/delete, daily completion, weekly/monthly history, current streak, longest streak, and completion percentage.
- Monthly budget with spending percentage, remaining balance, and 50%, 75%, 90%, and 100% notification thresholds.

### Phase 2

- Pomodoro focus mode with 25-minute focus, 5-minute short break, 15-minute long break, custom durations, start, pause, resume, reset, and skip controls.
- Focus sessions optionally linked to a subject, task, assignment, or goal.
- Daily, weekly, and total focus statistics with completion notifications.
- Unified productivity streaks for completed tasks, study sessions, habits, and focus sessions without duplicate day counting.
- Central calendar feed containing tasks, goals, study sessions, exams, assignments, habits, and reminders.
- Calendar reminder CRUD with monthly, weekly, and daily views.
- Smart notifications for exams, assignments, habits, study reminders, budget warnings, and completed focus sessions.

### Phase 3

- Real-data analytics dashboard with summary cards, line charts, bar charts, and doughnut charts.
- Weekly, monthly, yearly, and custom date-range analytics.
- Analytics for study hours, task completion, assignment completion, exam preparation, attendance, habit consistency, focus minutes, expenses, goals, and productivity score.
- Subject-wise analytics with subject filters. Tasks can now optionally be assigned to subjects for accurate task completion percentages.
- Local AI-style quiz generator with subject, topic, question count, and easy/medium/hard difficulty selection.
- Quiz submission, score percentage, correct/incorrect review, and quiz history.
- Profile customization for name, email, bio, course, semester, subjects, preferences, profile photo, and password changes.
- Final responsive pass for dashboard, analytics, quiz, profile, calendar, forms, tables, and charts.

## Technology

- Python 3.12+
- Flask
- Flask-SQLAlchemy and SQLAlchemy ORM
- SQLite by default, with optional MySQL/PyMySQL configuration
- Jinja2 templates
- Bootstrap 5 and Bootstrap Icons via CDN
- Chart.js via CDN
- HTML, CSS, and JavaScript
- Optional external AI assistant configuration through environment variables

## Complete Project File Structure

The following is the current source file inventory. Runtime files such as `__pycache__`, the local SQLite database, and uploaded user files are intentionally not listed as application source.

```text
SMART-TRACKER/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── app.py
├── ai_assistant.py
├── analytics_service.py
├── common.py
├── config.py
├── services.py
├── test_gemini.py
├── database/
│   └── init_db.py
├── models/
│   ├── __init__.py
│   └── models.py
├── routes/
│   ├── __init__.py
│   ├── admin.py
│   ├── analytics.py
│   ├── assistant.py
│   ├── attendance.py
│   ├── exams.py
│   ├── expenses.py
│   ├── goals.py
│   ├── habits.py
│   ├── notes.py
│   ├── quiz.py
│   ├── smart.py
│   ├── study.py
│   ├── tasks.py
│   └── timetable.py
├── static/
│   ├── css/
│   │   ├── analytics.css
│   │   └── style.css
│   └── js/
│       ├── analytics.js
│       └── script.js
└── templates/
	├── base.html
	├── index.html
	├── login.html
	├── register.html
	├── dashboard.html
	├── analytics.html
	├── assistant.html
	├── budget.html
	├── calendar.html
	├── calendar_event_form.html
	├── focus.html
	├── notifications.html
	├── productivity.html
	├── profile.html
	├── quiz.html
	├── recommendations.html
	├── reports.html
	├── study_targets.html
	├── admin/
	│   ├── announcements.html
	│   ├── dashboard.html
	│   ├── records.html
	│   └── users.html
	├── assignments/
	│   ├── form.html
	│   └── index.html
	├── attendance/
	│   ├── form.html
	│   └── list.html
	├── exams/
	│   ├── form.html
	│   └── index.html
	├── expenses/
	│   ├── form.html
	│   └── list.html
	├── goals/
	│   ├── form.html
	│   └── list.html
	├── habits/
	│   ├── form.html
	│   └── index.html
	├── notes/
	│   ├── form.html
	│   └── index.html
	├── study/
	│   ├── form.html
	│   └── list.html
	├── tasks/
	│   ├── form.html
	│   └── list.html
	└── timetable/
		├── form.html
		└── index.html
```

### Runtime directories

```text
instance/smart_tracker.db       Local SQLite database created at runtime
static/uploads/notes/            Uploaded note files
static/uploads/assignments/      User-specific assignment files
static/uploads/profile-*         Uploaded profile photos
__pycache__/                     Python bytecode generated by Python
```

## Setup

### Linux/macOS

```bash
cd SMART-TRACKER
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python database/init_db.py
python app.py
```

### Windows PowerShell

```powershell
cd path\to\SMART-TRACKER
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python database\init_db.py
python app.py
```

Open `http://127.0.0.1:5000` in a browser.

If port 5000 is already in use:

```bash
flask --app app run --port 5001
```

## Database

The default database is SQLite. Set `DATABASE_URL` in `.env` to use another supported SQLAlchemy database.

```env
DATABASE_URL=sqlite:///smart_tracker.db
SECRET_KEY=replace-this-in-production
```

The application runs `db.create_all()` and additive startup migrations. Existing tables and user data are preserved. Current Phase 3 additions include:

- `quiz_attempt` table
- `user.bio` column
- `user.subjects` column
- `user.preferences` column
- `task.subject` column

Phase 1 and Phase 2 tables include exams, assignments, habits, habit completions, focus sessions, calendar events, budgets, and notifications.

## Demo Accounts

Created by `python database/init_db.py` if they do not already exist:

- Admin: `admin@smarttracker.local` / `Admin@12345`
- Student: `student@smarttracker.local` / `Student@12345`

Change demo passwords before using the application outside local evaluation.

## Important Routes

- `/dashboard` - student overview
- `/analytics` - advanced real-data analytics
- `/quiz` - local AI-style quiz generator
- `/focus` - Pomodoro focus mode
- `/calendar` - centralized calendar
- `/habits` - habit tracker
- `/exams` - exam preparation
- `/assignments` - assignment tracker and files
- `/budget` - monthly budget
- `/notifications` - smart notification center
- `/profile` - profile and account settings

## File Uploads

- Notes are stored under `static/uploads/notes/`.
- Profile photos are stored under `static/uploads/`.
- Assignment files are stored under user-specific directories under `static/uploads/assignments/`.
- Assignment downloads are filtered by the authenticated user and use generated stored filenames.

Do not commit `.env`, production secrets, or private uploaded files.

## Reports and Backups

Authenticated users can download PDF and CSV reports from the Reports page. Personal JSON backup and restore tools are available from the Profile page.

## Validation

The current implementation has been checked with:

```bash
python -m compileall -q .
python database/init_db.py
python -m py_compile app.py common.py services.py analytics_service.py routes/*.py models/*.py
```

Validated behavior includes:

- Authentication-protected routes
- Phase 1 and Phase 2 CRUD flows
- Focus session persistence and notifications
- Streak union calculations and notification deduplication
- Calendar event CRUD and feed generation
- Analytics date ranges and subject filters
- Quiz generation, scoring, review, and history
- Profile updates and database migrations
- Internal link checks
- Mobile overflow checks
- Browser console and page-error checks

## Remaining Limitations

- Existing tasks created before subject support have no subject and are shown as unlinked in subject analytics.
- The quiz system uses a deterministic local fallback generator. It is designed so an external AI provider can be added later without changing the quiz workflow.
- Bootstrap, Bootstrap Icons, Chart.js, and configured fonts are loaded from CDNs and require network access unless vendored locally.
- Startup migrations are intentionally lightweight. Alembic should be added before production deployment with frequent schema changes.
- CSRF protection, email reminders, recurring tasks, calendar provider synchronization, and richer export formats remain future enhancements.

## Not Implemented Yet

Phase 4 and any features beyond the Phase 1, Phase 2, and Phase 3 scope have not been implemented.
