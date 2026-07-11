# RTK Rural Market

A mobile-first Flask web application for a rural startup selling pre-booked village
products (milk, ghee, paneer, curd, butter, vegetables, jaggery, honey, pickles and
seasonal produce). Customers pre-book online; the business owner travels to the city
for supplies once enough confirmed orders come in for a delivery run.

## Tech Stack

Flask · SQLAlchemy · SQLite · Flask-Login · Flask-WTF · Flask-Limiter · SMTP · Bootstrap 5
· Jinja2 · Vanilla JS · PWA (manifest + service worker)

## 1. Setup

```bash
python3 -m venv venv
source venv/bin/activate          # on Termux: source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env — at minimum set SECRET_KEY and ADMIN_PASSWORD
```

The database, admin account, and default categories (Milk, Ghee, Paneer, Curd, Butter,
Honey, Vegetables, Jaggery, Pickles, Seasonal Products) are created automatically the
first time the app starts — no manual migration step is required.

## 2. Run (development)

```bash
export FLASK_ENV=development
python3 app.py
```

Visit `http://127.0.0.1:5000`. Log into the admin panel at `/admin` using the mobile
number and password set as `ADMIN_MOBILE` / `ADMIN_PASSWORD` in `.env`.

## 3. Run (production, including Termux)

```bash
export FLASK_ENV=production
pip install gunicorn   # not required on Termux; Termux typically runs the dev server directly
gunicorn -w 2 -b 0.0.0.0:5000 "app:create_app()"
```

On Termux (no gunicorn), simply run:

```bash
export FLASK_ENV=production
python3 app.py
```

`app.py` reads `PORT` from the environment (defaults to 5000) and binds to `0.0.0.0` so
it's reachable from other devices on the same network.

## 4. SMS OTP — important

No SMS gateway account/API key was available when this project was generated. By
default (`SMS_PROVIDER=console` in `.env`), OTPs are logged to `logs/otp.log` and
printed to the console instead of being texted, so you can fully test signup, login and
password reset locally. To send real SMS, sign up with a provider (Twilio, MSG91,
Fast2SMS, etc.), add your credentials to `.env`, and implement the corresponding branch
in `services/sms_service.py` (each is stubbed with a clear TODO).

## 5. Email (SMTP)

Fill in the `SMTP_*` values in `.env` to enable welcome emails, order confirmations,
status updates, password-change alerts and contact-form notifications. Without SMTP
credentials, emails are skipped (logged as a warning) rather than raising errors, so the
rest of the app keeps working.

## 6. Project Structure

```
app.py                 Flask application factory
config/                Environment-driven configuration
models/                SQLAlchemy models
routes/                Blueprints (auth, customer, products, cart, checkout, orders,
                        notifications, contact, legal, admin)
forms/                 Flask-WTF forms
services/               Email, SMS, OTP, notifications, audit log, order status service
utils/                  Decorators and helper functions
templates/              Jinja2 templates (mirrors the blueprint structure)
static/                 CSS, JS, icons, uploaded product images
database/               SQLite file lives here by default
backups/                Admin-triggered SQLite backups are written here
logs/                   Rotating app log + OTP simulation log
```

## 7. Known Scope Notes

- **SMS delivery** is simulated by default (see section 4) — this is the only piece
  that cannot be made "live" without a paid third-party account.
- **SMTP settings saved in the admin panel** are stored for reference; the values
  actually used to send mail at runtime come from `.env` (documented on that settings
  page). Wiring live-reload of SMTP config without an app restart was out of scope.
- **PostgreSQL migration**: the app defaults to SQLite but reads `DATABASE_URL` from
  the environment, so pointing it at a PostgreSQL URI works without code changes beyond
  installing a driver (e.g. `psycopg2-binary`). The one-click "Backup" feature in the
  admin panel is SQLite-specific; for PostgreSQL, use `pg_dump` on the server instead.
