"""db.py - privacy-first SQLite storage.

ONLY these things are stored (data minimisation):
  ASSESSMENTS      assessment_id, overall_score, risk_level, created_at (+ a hash of the delete token)
  CATEGORY_SCORES  one 0-100 score per category
  FINDINGS         finding types + severity + generic description (never the user's answers)
  RECOMMENDATIONS  a static catalogue keyed by finding_type (no per-user data)

NEVER stored: phone, e-mail, address, birth date, passwords, exact location, messages,
or the raw questionnaire answers.
"""
import hashlib
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import current_app, g

from backend.questionnaire import PRIORITY_BY_SEVERITY, QUESTIONS

SCHEMA = """
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id     TEXT PRIMARY KEY,
    overall_score     INTEGER NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
    risk_level        TEXT NOT NULL CHECK (risk_level IN ('LOW','MODERATE','HIGH','CRITICAL')),
    created_at        TEXT NOT NULL,
    delete_token_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS category_scores (
    category_score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id     TEXT NOT NULL REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    category          TEXT NOT NULL,
    score             REAL NOT NULL CHECK (score BETWEEN 0 AND 100)
);
CREATE TABLE IF NOT EXISTS findings (
    finding_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id TEXT NOT NULL REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    category      TEXT NOT NULL,
    finding_type  TEXT NOT NULL,
    severity      TEXT NOT NULL CHECK (severity IN ('HIGH','MEDIUM','LOW')),
    description   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_type      TEXT NOT NULL UNIQUE,
    recommendation    TEXT NOT NULL,
    priority          TEXT NOT NULL CHECK (priority IN ('IMMEDIATE','IMPORTANT','GOOD PRACTICE'))
);
CREATE INDEX IF NOT EXISTS idx_cat_assessment ON category_scores(assessment_id);
CREATE INDEX IF NOT EXISTS idx_find_assessment ON findings(assessment_id);
"""


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_PATH"])
    return g.db


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(path):
    """Create tables and seed the static recommendation catalogue."""
    conn = connect(path)
    conn.executescript(SCHEMA)
    for q in QUESTIONS:
        conn.execute(
            "INSERT OR REPLACE INTO recommendations(finding_type, recommendation, priority) VALUES (?,?,?)",
            (q.finding_type, q.recommendation, PRIORITY_BY_SEVERITY[q.severity]))
    conn.commit()
    conn.close()


def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def purge_expired(db, retention_days):
    """Retention limitation: delete assessments older than RETENTION_DAYS."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    db.execute("DELETE FROM assessments WHERE created_at < ?", (cutoff,))
    db.commit()


def save_assessment(db, result):
    """Persist ONLY scores + finding types. Returns (assessment_id, delete_token)."""
    assessment_id = uuid.uuid4().hex             # unguessable id (acts as a capability)
    delete_token = secrets.token_urlsafe(24)     # shown once to the creator
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.execute("INSERT INTO assessments VALUES (?,?,?,?,?)",
               (assessment_id, result["overall"]["score"], result["overall"]["level"], created_at,
                _hash_token(delete_token)))
    db.executemany("INSERT INTO category_scores(assessment_id, category, score) VALUES (?,?,?)",
                   [(assessment_id, k, v) for k, v in result["category_scores"].items()])
    db.executemany(
        "INSERT INTO findings(assessment_id, category, finding_type, severity, description) VALUES (?,?,?,?,?)",
        [(assessment_id, f["category"], f["finding_type"], f["severity"], f["description"])
         for f in result["findings"]["findings"]])
    db.commit()
    return assessment_id, delete_token, created_at


def load_assessment(db, assessment_id):
    row = db.execute("SELECT assessment_id, overall_score, risk_level, created_at FROM assessments WHERE assessment_id=?",
                     (assessment_id,)).fetchone()
    if row is None:
        return None
    cats = db.execute("SELECT category, score FROM category_scores WHERE assessment_id=? ORDER BY category_score_id",
                      (assessment_id,)).fetchall()
    finds = db.execute("""SELECT f.category, f.finding_type, f.severity, f.description, r.recommendation, r.priority
                          FROM findings f LEFT JOIN recommendations r ON r.finding_type = f.finding_type
                          WHERE f.assessment_id=? ORDER BY f.finding_id""", (assessment_id,)).fetchall()
    return {
        "assessment_id": row["assessment_id"], "overall_score": row["overall_score"],
        "risk_level": row["risk_level"], "created_at": row["created_at"],
        "category_scores": {c["category"]: c["score"] for c in cats},
        "findings": [dict(f) for f in finds],
    }


def delete_assessment(db, assessment_id, token):
    """Delete if the token matches. Returns True/False. Constant-time comparison."""
    row = db.execute("SELECT delete_token_hash FROM assessments WHERE assessment_id=?", (assessment_id,)).fetchone()
    if row is None:
        return None
    if not secrets.compare_digest(row["delete_token_hash"], _hash_token(token or "")):
        return False
    db.execute("DELETE FROM assessments WHERE assessment_id=?", (assessment_id,))
    db.commit()
    return True


def stored_assessment_count(db):
    return db.execute("SELECT COUNT(*) FROM assessments").fetchone()[0]
