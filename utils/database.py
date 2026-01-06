import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(__file__), "jobs.db")

def init_db():
    """Initializes the database and creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seen_jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            url TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_job(job):
    """Adds a job to the database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO seen_jobs (job_id, title, company, url)
            VALUES (?, ?, ?, ?)
        ''', (job['id'], job['title'], job['company'], job['job_url']))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding job: {e}")
        return False

def is_job_seen(job_id):
    """Checks if a job has already been seen."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM seen_jobs WHERE job_id = ?', (job_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def setup_leetcode_tracking():
    """Initializes the table for tracking visited LeetCode posts."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visited_leetcode_posts (
            uuid TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def is_leetcode_post_visited(uuid):
    """Checks if a LeetCode post has already been processed."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM visited_leetcode_posts WHERE uuid = ?', (uuid,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_leetcode_post_visited(uuid):
    """Marks a LeetCode post as processed."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO visited_leetcode_posts (uuid) VALUES (?)', (uuid,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error marking post as visited: {e}")
        return False
