"""
Database module for evaluation system.

Tables:
- tasks: Task requests sent to students
- repos: Repository submissions from students
- results: Evaluation results

Author: Evaluation System
Date: 2025-10-16
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import json

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent / "evaluation.db"


class Database:
    """Database manager for evaluation system."""
    
    def __init__(self, db_path: Path = DB_PATH):
        """Initialize database connection."""
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    def init_db(self):
        """Initialize database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tasks table - stores task requests sent to students
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                email TEXT NOT NULL,
                task TEXT NOT NULL,
                round INTEGER NOT NULL,
                nonce TEXT NOT NULL UNIQUE,
                brief TEXT NOT NULL,
                attachments TEXT,
                checks TEXT,
                evaluation_url TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                statuscode INTEGER,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(email, task, round)
            )
        """)
        
        # Repos table - stores repository submissions from students
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                email TEXT NOT NULL,
                task TEXT NOT NULL,
                round INTEGER NOT NULL,
                nonce TEXT NOT NULL,
                repo_url TEXT NOT NULL,
                commit_sha TEXT NOT NULL,
                pages_url TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (nonce) REFERENCES tasks(nonce),
                UNIQUE(email, task, round)
            )
        """)
        
        # Results table - stores evaluation results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                email TEXT NOT NULL,
                task TEXT NOT NULL,
                round INTEGER NOT NULL,
                repo_url TEXT NOT NULL,
                commit_sha TEXT NOT NULL,
                pages_url TEXT NOT NULL,
                "check" TEXT NOT NULL,
                score REAL,
                reason TEXT,
                logs TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (repo_url) REFERENCES repos(repo_url)
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_email_round 
            ON tasks(email, round)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_nonce 
            ON tasks(nonce)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_repos_email_round 
            ON repos(email, round)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_results_email_task_round 
            ON results(email, task, round)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    # === TASKS TABLE ===
    
    def task_exists(self, email: str, task: str, round: int) -> bool:
        """Check if a task already exists for this email and round."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM tasks WHERE email = ? AND task = ? AND round = ?",
            (email, task, round)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def insert_task(self, task_data: Dict[str, Any]) -> int:
        """Insert a new task request."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks (
                timestamp, email, task, round, nonce, brief, attachments, 
                checks, evaluation_url, endpoint, statuscode, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_data.get('timestamp', datetime.utcnow().isoformat()),
            task_data['email'],
            task_data['task'],
            task_data['round'],
            task_data['nonce'],
            task_data['brief'],
            json.dumps(task_data.get('attachments', [])),
            json.dumps(task_data.get('checks', [])),
            task_data['evaluation_url'],
            task_data['endpoint'],
            task_data.get('statuscode'),
            task_data.get('error')
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Inserted task {task_id}: {task_data['email']} - {task_data['task']} (Round {task_data['round']})")
        return task_id
    
    def get_task_by_nonce(self, nonce: str) -> Optional[Dict[str, Any]]:
        """Get task by nonce."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE nonce = ?", (nonce,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_tasks_by_round(self, round: int) -> List[Dict[str, Any]]:
        """Get all tasks for a specific round."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE round = ? ORDER BY created_at", (round,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # === REPOS TABLE ===
    
    def repo_exists(self, email: str, task: str, round: int) -> bool:
        """Check if a repo submission exists for this email, task, and round."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM repos WHERE email = ? AND task = ? AND round = ?",
            (email, task, round)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def insert_repo(self, repo_data: Dict[str, Any]) -> int:
        """Insert a new repository submission."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO repos (
                timestamp, email, task, round, nonce, 
                repo_url, commit_sha, pages_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            repo_data.get('timestamp', datetime.utcnow().isoformat()),
            repo_data['email'],
            repo_data['task'],
            repo_data['round'],
            repo_data['nonce'],
            repo_data['repo_url'],
            repo_data['commit_sha'],
            repo_data['pages_url']
        ))
        
        repo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Inserted repo {repo_id}: {repo_data['email']} - {repo_data['repo_url']}")
        return repo_id
    
    def get_repos_to_evaluate(self, round: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all repos that need evaluation."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if round is not None:
            cursor.execute("""
                SELECT * FROM repos 
                WHERE round = ?
                ORDER BY created_at
            """, (round,))
        else:
            cursor.execute("SELECT * FROM repos ORDER BY created_at")
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_repo_by_nonce(self, nonce: str) -> Optional[Dict[str, Any]]:
        """Get repo by nonce."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repos WHERE nonce = ?", (nonce,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    # === RESULTS TABLE ===
    
    def result_exists(self, email: str, task: str, round: int) -> bool:
        """Check if evaluation results exist for this email, task, and round."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM results WHERE email = ? AND task = ? AND round = ?",
            (email, task, round)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def insert_result(self, result_data: Dict[str, Any]) -> int:
        """Insert an evaluation result."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO results (
                timestamp, email, task, round, repo_url, commit_sha, pages_url,
                check, score, reason, logs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result_data.get('timestamp', datetime.utcnow().isoformat()),
            result_data['email'],
            result_data['task'],
            result_data['round'],
            result_data['repo_url'],
            result_data['commit_sha'],
            result_data['pages_url'],
            result_data['check'],
            result_data.get('score'),
            result_data.get('reason'),
            result_data.get('logs')
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Inserted result {result_id}: {result_data['email']} - {result_data['check']}")
        return result_id
    
    def get_results(self, email: Optional[str] = None, round: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get evaluation results with optional filters."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM results WHERE 1=1"
        params = []
        
        if email:
            query += " AND email = ?"
            params.append(email)
        
        if round is not None:
            query += " AND round = ?"
            params.append(round)
        
        query += " ORDER BY created_at"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # === UTILITY METHODS ===
    
    def get_submissions_without_tasks(self, submissions: List[Dict[str, Any]], round: int) -> List[Dict[str, Any]]:
        """Filter submissions that don't have tasks yet for the given round."""
        result = []
        for submission in submissions:
            if not self.task_exists(submission['email'], submission.get('task', ''), round):
                result.append(submission)
        return result
    
    def get_repos_without_results(self, round: int) -> List[Dict[str, Any]]:
        """Get repos that haven't been evaluated yet for the given round."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.* FROM repos r
            LEFT JOIN results res ON r.email = res.email AND r.task = res.task AND r.round = res.round
            WHERE r.round = ? AND res.id IS NULL
            ORDER BY r.created_at
        """, (round,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def export_results_csv(self, output_path: Path):
        """Export results table to CSV."""
        import csv
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM results ORDER BY email, task, round")
        rows = cursor.fetchall()
        
        if rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))
            
            logger.info(f"Exported {len(rows)} results to {output_path}")
        else:
            logger.warning("No results to export")
        
        conn.close()


# Singleton instance
_db_instance = None


def get_db() -> Database:
    """Get database singleton instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


if __name__ == "__main__":
    # Test database
    logging.basicConfig(level=logging.INFO)
    db = get_db()
    print(f"Database initialized at {db.db_path}")
    print("Schema created successfully!")
