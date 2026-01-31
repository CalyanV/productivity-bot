import aiosqlite
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for productivity system"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        """Initialize database with schema"""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Read schema
        schema_path = Path(__file__).parent.parent / "migrations" / "001_initial_schema.sql"
        with open(schema_path) as f:
            schema = f.read()

        # Execute schema
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.executescript(schema)
            await conn.commit()

        logger.info(f"Database initialized at {self.db_path}")

    async def connect(self) -> aiosqlite.Connection:
        """Get database connection"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
        return self._connection

    async def close(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
