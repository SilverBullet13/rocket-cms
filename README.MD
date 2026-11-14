# Rocket CMS

A small content management system (CMS) for publishing articles, built with **Python / Flask** and **SQLite**. Logged-in users can write articles in Markdown, schedule their publication date, edit them, and manage the other user accounts. Visitors can read and search published articles.

> Built solo as a school project. The user interface is in French.

## Features

- **Public site**: the 5 most recent published articles on the home page, a full article page with author and avatar, and keyword search over titles and content
- **Markdown articles**: content is stored as Markdown and converted to HTML when displayed
- **Scheduled publishing**: articles with a future publication date stay out of the home page, dashboard and search results until that date
- **Accounts and sessions**: sign-up, sign-in and sign-out with Flask sessions. Passwords are salted and hashed, never stored in plain text
- **Dashboard** for logged-in users: list all articles, create new ones, edit existing ones
- **User management**: list, add, modify and delete users
- **Form validation**: required fields, matching email confirmation, unique email and a password format rule (see below)
- **Random avatar** assigned to each new user
- **Custom 404 page** and a responsive layout (CSS only, mobile menu included)

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3.1 |
| Templates | Jinja2 |
| Database | SQLite (parameterized queries via `sqlite3`) |
| Content | Python-Markdown |
| Frontend | HTML, CSS, Font Awesome icons |

## Getting started

```bash
git clone <this-repo-url>
cd Rocket

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

flask --app app run
```

Then open <http://127.0.0.1:5000>. Run the app from the project folder, because the database path (`db/database.db`) is relative.

The repository includes `db/database.db` with sample articles and users, so it works straight away. The schema is in `db/db.sql`.

### Demo accounts

Sign in at `/admin` (or click **Connexion**):

| Username | Password |
|---|---|
| `prof` | `secret1234` |
| `nano` | `nano1234` |
| `rudolph` | `rudolph1234` |

### Password rule for new accounts

At least 8 characters, using letters, digits and `# $ % & ' * + / = ? @`.

## Routes

| Route | Access | Purpose |
|---|---|---|
| `/` | public | Latest 5 published articles |
| `/article/<id>` | public | Read an article |
| `/search?query=` | public | Search articles |
| `/admin` | public | Sign in |
| `/createaccount` | public | Create an account |
| `/dashboard` | logged in | All articles, links to admin actions |
| `/admin-nouveau` | logged in | Create an article |
| `/edit/<id>` | logged in | Edit an article |
| `/utilisateurs` | logged in | User management (add, modify, delete) |
| `/logout` | logged in | Sign out |

## Project structure

```
app.py            Flask routes, form handling and validation
database.py       Database access layer (all SQL lives here)
db/db.sql         Database schema
db/database.db    SQLite database with sample data
templates/        Jinja2 templates (base layout, navbar, footer, pages)
static/css/       Stylesheets split by concern (base, header, forms, buttons, footer, responsive)
static/def-avatar/ Avatar images assigned to users
```

## Known limitations and next steps

This was a learning project, and these are the things I would change before using it in production:

- **Password hashing**: uses SHA3-512 with a per-user salt. A deliberately slow algorithm (bcrypt, scrypt or Argon2, e.g. Werkzeug's `generate_password_hash`) would resist brute force much better.
- **HTML in articles**: Markdown output is rendered unescaped, so raw HTML in an article is executed. Sanitizing it (e.g. with `nh3` or `bleach`) would prevent stored XSS.
- **CSRF protection**: forms have no CSRF tokens. Flask-WTF would add them.
- **Roles**: every logged-in user has full admin rights. Separate author and admin roles would be the next step.
- **Error handling**: some invalid inputs on the user-management pages are not yet handled gracefully.
