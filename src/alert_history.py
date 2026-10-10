import pandas as pd
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "alert_history.db"


def initialize_alert_history():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_key TEXT UNIQUE NOT NULL,
                alert_type TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                summary TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def alert_exists(alert_key):
    with sqlite3.connect(DB_PATH) as conn:
        result = conn.execute(
            "SELECT 1 FROM alert_history WHERE alert_key = ?",
            (alert_key,)
        ).fetchone()

    return result is not None


def record_alert(alert_key, alert_type, start_date, end_date, summary, status):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO alert_history (
                alert_key, alert_type, start_date,
                end_date, summary, status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(alert_key) DO UPDATE SET
                summary = excluded.summary,
                status = excluded.status
        """, (
            alert_key,
            alert_type,
            str(start_date),
            str(end_date),
            summary,
            status
        ))

def send_alert_once(
    alert_key,
    alert_type,
    start_date,
    end_date,
    subject,
    summary,
):
    from src.email_alert import send_email_alert

    initialize_alert_history()

    if alert_exists(alert_key):
        print(f"Duplicate alert skipped: {alert_key}")
        return False

    # Record the attempt first, so a crash won't silently lose its history.
    record_alert(
        alert_key=alert_key,
        alert_type=alert_type,
        start_date=start_date,
        end_date=end_date,
        summary=summary,
        status="pending",
    )

    try:
        send_email_alert(subject=subject, body=summary)
    except Exception as exc:
        record_alert(
            alert_key=alert_key,
            alert_type=alert_type,
            start_date=start_date,
            end_date=end_date,
            summary=f"{summary}\n\nEmail error: {exc}",
            status="failed",
        )
        print(f"Email failed: {exc}")
        return False

    record_alert(
        alert_key=alert_key,
        alert_type=alert_type,
        start_date=start_date,
        end_date=end_date,
        summary=summary,
        status="sent",
    )

    print(f"Alert email sent and recorded: {alert_key}")
    return True

def get_alert_history():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT
                id,
                alert_type,
                start_date,
                end_date,
                status,
                created_at,
                summary
            FROM alert_history
            ORDER BY id DESC
        """).fetchall()

    columns = [
        "ID",
        "Alert Type",
        "Start Date",
        "End Date",
        "Status",
        "Created At",
        "Summary",
    ]

    return pd.DataFrame(rows, columns=columns)
