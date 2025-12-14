"""
Database operations for entity storage
SQLite database with duplicate prevention
"""

import sqlite3
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EntityDatabase:
    """SQLite database for storing entities, facts, and questions"""

    def __init__(self, db_path: str = "data/entities.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._setup_database()

    def _setup_database(self):
        """Create tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return dict-like rows

        cursor = self.conn.cursor()

        # Entities table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wikidata_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                culture TEXT,
                country TEXT,
                wikipedia_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Facts table (Wikidata properties)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                property TEXT NOT NULL,
                value TEXT NOT NULL,
                value_label TEXT,
                FOREIGN KEY (entity_id) REFERENCES entities(id),
                UNIQUE(entity_id, property, value)
            )
        """
        )

        # Questions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                question_type TEXT NOT NULL,
                question_text TEXT NOT NULL,
                ground_truth TEXT NOT NULL,
                property TEXT NOT NULL,
                FOREIGN KEY (entity_id) REFERENCES entities(id),
                UNIQUE(entity_id, question_type)
            )
        """
        )

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_wikidata_id ON entities(wikidata_id)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_culture ON entities(culture)")

        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def entity_exists(self, wikidata_id: str) -> bool:
        """Check if entity already exists"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM entities WHERE wikidata_id = ?", (wikidata_id,))
        return cursor.fetchone() is not None

    def add_entity(
        self,
        wikidata_id: str,
        name: str,
        entity_type: str,
        culture: str = None,
        country: str = None,
        wikipedia_text: str = None,
    ) -> Optional[int]:
        """
        Add entity to database
        Returns entity_id if added, None if already exists
        """
        if self.entity_exists(wikidata_id):
            logger.warning(f"Entity {wikidata_id} already exists, skipping")
            return None

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO entities (wikidata_id, name, type, culture, country, wikipedia_text)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (wikidata_id, name, entity_type, culture, country, wikipedia_text),
        )

        self.conn.commit()
        entity_id = cursor.lastrowid
        logger.info(f"Added entity: {name} ({wikidata_id})")
        return entity_id

    def add_fact(
        self, entity_id: int, property_code: str, value: str, value_label: str = None
    ) -> bool:
        """Add fact to database, returns False if duplicate"""
        cursor = self.conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO facts (entity_id, property, value, value_label)
                VALUES (?, ?, ?, ?)
            """,
                (entity_id, property_code, value, value_label),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.debug(
                f"Duplicate fact for entity {entity_id}, property {property_code}"
            )
            return False

    def add_question(
        self,
        entity_id: int,
        question_type: str,
        question_text: str,
        ground_truth: str,
        property_code: str,
    ) -> bool:
        """Add question to database, returns False if duplicate"""
        cursor = self.conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO questions (entity_id, question_type, question_text, ground_truth, property)
                VALUES (?, ?, ?, ?, ?)
            """,
                (entity_id, question_type, question_text, ground_truth, property_code),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.debug(
                f"Duplicate question for entity {entity_id}, type {question_type}"
            )
            return False

    def get_entity(self, wikidata_id: str) -> Optional[Dict]:
        """Get entity by Wikidata ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entities WHERE wikidata_id = ?", (wikidata_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_entity_facts(self, entity_id: int) -> List[Dict]:
        """Get all facts for an entity"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM facts WHERE entity_id = ?", (entity_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_entity_questions(self, entity_id: int) -> List[Dict]:
        """Get all questions for an entity"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE entity_id = ?", (entity_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_all_entities(
        self, entity_type: str = None, culture: str = None
    ) -> List[Dict]:
        """Get all entities with optional filters"""
        cursor = self.conn.cursor()

        query = "SELECT * FROM entities WHERE 1=1"
        params = []

        if entity_type:
            query += " AND type = ?"
            params.append(entity_type)

        if culture:
            query += " AND culture = ?"
            params.append(culture)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()

        stats = {}

        # Total entities
        cursor.execute("SELECT COUNT(*) as count FROM entities")
        stats["total_entities"] = cursor.fetchone()["count"]

        # By type
        cursor.execute("SELECT type, COUNT(*) as count FROM entities GROUP BY type")
        stats["by_type"] = {row["type"]: row["count"] for row in cursor.fetchall()}

        # By culture
        cursor.execute(
            "SELECT culture, COUNT(*) as count FROM entities GROUP BY culture"
        )
        stats["by_culture"] = {
            row["culture"]: row["count"] for row in cursor.fetchall()
        }

        # Total questions
        cursor.execute("SELECT COUNT(*) as count FROM questions")
        stats["total_questions"] = cursor.fetchone()["count"]

        # Total facts
        cursor.execute("SELECT COUNT(*) as count FROM facts")
        stats["total_facts"] = cursor.fetchone()["count"]

        return stats

    def update_wikipedia_text(self, wikidata_id: str, text: str) -> bool:
        """Update Wikipedia text for an entity"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE entities
            SET wikipedia_text = ?
            WHERE wikidata_id = ?
        """,
            (text, wikidata_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
