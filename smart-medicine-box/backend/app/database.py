"""
数据库层 - 使用 Python 内置 sqlite3（零依赖）
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "smart_medicine_box.db")

# 线程本地存储，每个请求独立的连接
import threading
_local = threading.local()


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_db():
    """获取当前请求的数据库连接（由中间件注入到 _local.conn）"""
    if not hasattr(_local, 'conn') or _local.conn is None:
        _local.conn = get_connection()
    return _local.conn


def close_db():
    """关闭当前请求的数据库连接"""
    if hasattr(_local, 'conn') and _local.conn is not None:
        _local.conn.close()
        _local.conn = None


def init_db():
    """初始化数据库表"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        -- 用户表
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            openid TEXT UNIQUE NOT NULL,
            unionid TEXT,
            nickname TEXT,
            avatar_url TEXT,
            phone TEXT,
            age INTEGER,
            gender INTEGER DEFAULT 0,
            emergency_contact TEXT,
            emergency_contact_name TEXT,
            is_elderly INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            last_login_at TEXT,
            remark TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            specification TEXT,
            dosage TEXT NOT NULL,
            unit TEXT DEFAULT '片',
            frequency TEXT DEFAULT 'daily',
            start_date TEXT,
            end_date TEXT,
            total_stock INTEGER DEFAULT 0,
            remaining_stock INTEGER DEFAULT 0,
            stock_alert_threshold INTEGER DEFAULT 5,
            box_position TEXT,
            image_url TEXT,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS medicine_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            period TEXT NOT NULL,
            time_label TEXT NOT NULL,
            reminder_time TEXT NOT NULL,
            dosage_at_time TEXT NOT NULL,
            days_of_week TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS medicine_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER REFERENCES medicine_schedules(id) ON DELETE SET NULL,
            medicine_id INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            scheduled_time TEXT NOT NULL,
            actual_time TEXT,
            status TEXT DEFAULT 'missed',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS family_bindings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            elderly_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            family_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            relationship TEXT NOT NULL,
            is_primary INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_users_openid ON users(openid);
        CREATE INDEX IF NOT EXISTS idx_medicines_user_id ON medicines(user_id);
        CREATE INDEX IF NOT EXISTS idx_schedules_user_id ON medicine_schedules(user_id);
        CREATE INDEX IF NOT EXISTS idx_schedules_medicine_id ON medicine_schedules(medicine_id);
        CREATE INDEX IF NOT EXISTS idx_records_user_id ON medicine_records(user_id);
        CREATE INDEX IF NOT EXISTS idx_records_schedule_id ON medicine_records(schedule_id);
        CREATE INDEX IF NOT EXISTS idx_records_scheduled_time ON medicine_records(scheduled_time);
        CREATE INDEX IF NOT EXISTS idx_family_elderly ON family_bindings(elderly_user_id);
        CREATE INDEX IF NOT EXISTS idx_family_family ON family_bindings(family_user_id);
    """)

    conn.commit()
    conn.close()


def row_to_dict(row):
    """将 sqlite3.Row 转为 dict"""
    if row is None:
        return None
    return dict(row)
