import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


VALID_STATUSES = ("queued", "running", "done", "failed", "canceled")


@dataclass
class BenchmarkJob:
    job_id: int
    status: str
    payload: Dict[str, Any]
    created_at: str
    started_at: Optional[str]
    finished_at: Optional[str]
    worker_id: Optional[str]
    attempts: int
    max_attempts: int
    last_error: Optional[str]
    result: Optional[Dict[str, Any]]


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


class BenchmarkQueue:
    def __init__(self, db_path: str = "data/benchmark_jobs.sqlite3"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS benchmark_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    worker_id TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 1,
                    last_error TEXT,
                    result_json TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_benchmark_jobs_status ON benchmark_jobs(status)")
            conn.commit()

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> BenchmarkJob:
        return BenchmarkJob(
            job_id=int(row["id"]),
            status=row["status"],
            payload=json.loads(row["payload_json"]),
            created_at=row["created_at"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            worker_id=row["worker_id"],
            attempts=int(row["attempts"]),
            max_attempts=int(row["max_attempts"]),
            last_error=row["last_error"],
            result=json.loads(row["result_json"]) if row["result_json"] else None,
        )

    def enqueue(self, payload: Dict[str, Any], max_attempts: int = 1) -> int:
        now = _utc_now_iso()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO benchmark_jobs (status, payload_json, created_at, max_attempts)
                VALUES (?, ?, ?, ?)
                """,
                ("queued", json.dumps(payload), now, int(max_attempts)),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def list_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[BenchmarkJob]:
        query = "SELECT * FROM benchmark_jobs"
        params: List[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(int(limit))
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [self._row_to_job(r) for r in rows]

    def status_counts(self) -> Dict[str, int]:
        counts = {s: 0 for s in VALID_STATUSES}
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT status, COUNT(*) AS cnt
                FROM benchmark_jobs
                GROUP BY status
                """
            ).fetchall()
        for row in rows:
            status = row["status"]
            if status in counts:
                counts[status] = int(row["cnt"])
        return counts

    def claim_next(self, worker_id: str) -> Optional[BenchmarkJob]:
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT * FROM benchmark_jobs
                WHERE status = 'queued'
                ORDER BY id ASC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                conn.commit()
                return None

            now = _utc_now_iso()
            updated = conn.execute(
                """
                UPDATE benchmark_jobs
                SET status='running', started_at=?, worker_id=?, attempts=attempts+1, last_error=NULL
                WHERE id=? AND status='queued'
                """,
                (now, worker_id, int(row["id"])),
            )
            conn.commit()
            if updated.rowcount != 1:
                return None

        # reload committed state
        with self._connect() as conn:
            fresh = conn.execute("SELECT * FROM benchmark_jobs WHERE id=?", (int(row["id"]),)).fetchone()
            return self._row_to_job(fresh) if fresh else None

    def mark_done(self, job_id: int, result: Dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE benchmark_jobs
                SET status='done', finished_at=?, result_json=?
                WHERE id=?
                """,
                (_utc_now_iso(), json.dumps(result), int(job_id)),
            )
            conn.commit()

    def mark_failed(self, job_id: int, error_message: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE benchmark_jobs
                SET status='failed', finished_at=?, last_error=?
                WHERE id=?
                """,
                (_utc_now_iso(), str(error_message), int(job_id)),
            )
            conn.commit()

    def cancel(self, job_id: int) -> bool:
        with self._connect() as conn:
            updated = conn.execute(
                """
                UPDATE benchmark_jobs
                SET status='canceled', finished_at=?
                WHERE id=? AND status IN ('queued', 'running')
                """,
                (_utc_now_iso(), int(job_id)),
            )
            conn.commit()
            return updated.rowcount == 1
