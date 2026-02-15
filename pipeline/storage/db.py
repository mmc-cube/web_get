"""SQLite 存储封装"""

import sqlite3
import json
import os
from datetime import datetime


class Database:
    def __init__(self, db_path: str = "pipeline.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS tweets (
                id TEXT PRIMARY KEY,
                author_name TEXT,
                author_handle TEXT,
                text TEXT,
                lang TEXT,
                created_at TEXT,
                likes INTEGER DEFAULT 0,
                reposts INTEGER DEFAULT 0,
                replies INTEGER DEFAULT 0,
                bookmarks INTEGER DEFAULT 0,
                urls TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                is_ad_suspect INTEGER DEFAULT 0,
                cluster_id TEXT,
                heat_score REAL DEFAULT 0,
                collected_date TEXT
            );

            CREATE TABLE IF NOT EXISTS repos (
                name TEXT PRIMARY KEY,
                owner TEXT,
                description TEXT,
                stars INTEGER DEFAULT 0,
                forks INTEGER DEFAULT 0,
                stars_24h INTEGER DEFAULT 0,
                created_at TEXT,
                language TEXT,
                topics TEXT DEFAULT '[]',
                readme_summary TEXT DEFAULT '',
                relevance_tags TEXT DEFAULT '[]',
                is_new INTEGER DEFAULT 0,
                collected_date TEXT
            );

            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT,
                title TEXT,
                task_type TEXT,
                cost_tag TEXT,
                risk_tag TEXT,
                deadline TEXT,
                url TEXT,
                note TEXT,
                collected_date TEXT
            );

            CREATE TABLE IF NOT EXISTS markets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                summary TEXT,
                volume TEXT,
                odds_change TEXT,
                url TEXT,
                collected_date TEXT
            );

            CREATE TABLE IF NOT EXISTS daily_meta (
                date TEXT PRIMARY KEY,
                generated_at TEXT,
                meta TEXT DEFAULT '{}'
            );
        """)
        self.conn.commit()

    def save_tweets(self, tweets: list, date: str):
        cursor = self.conn.cursor()
        for t in tweets:
            cursor.execute("""
                INSERT OR REPLACE INTO tweets
                (id, author_name, author_handle, text, lang, created_at,
                 likes, reposts, replies, bookmarks, urls, tags,
                 is_ad_suspect, cluster_id, heat_score, collected_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t.id, t.author_name, t.author_handle, t.text, t.lang,
                t.created_at.isoformat() if isinstance(t.created_at, datetime) else t.created_at,
                t.likes, t.reposts, t.replies, t.bookmarks,
                json.dumps(t.urls), json.dumps(t.tags),
                int(t.is_ad_suspect), t.cluster_id, t.heat_score, date,
            ))
        self.conn.commit()

    def save_repos(self, repos: list, date: str):
        cursor = self.conn.cursor()
        for r in repos:
            cursor.execute("""
                INSERT OR REPLACE INTO repos
                (name, owner, description, stars, forks, stars_24h,
                 created_at, language, topics, readme_summary,
                 relevance_tags, is_new, collected_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.name, r.owner, r.description, r.stars, r.forks, r.stars_24h,
                r.created_at.isoformat() if isinstance(r.created_at, datetime) else r.created_at,
                r.language, json.dumps(r.topics), r.readme_summary,
                json.dumps(r.relevance_tags), int(r.is_new), date,
            ))
        self.conn.commit()

    def close(self):
        self.conn.close()
