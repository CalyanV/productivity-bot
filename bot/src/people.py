import aiosqlite
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path
from .database import Database
from .obsidian_sync import ObsidianSync

logger = logging.getLogger(__name__)


class PeopleManager:
    """Manage people (Personal CRM)"""

    def __init__(self, db_path: str, vault_path: str):
        self.db_path = db_path
        self.vault_path = vault_path
        self.db = Database(db_path)
        self.vault_sync = ObsidianSync(vault_path)

    async def initialize(self):
        """Initialize database"""
        await self.db.initialize()

    async def create_person(self, person_data: Dict) -> Dict:
        """
        Create a new person

        Args:
            person_data: Dictionary with name, role, company, email, etc.

        Returns:
            Created person info with person_id
        """
        person_id = f"person-{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        # Extract data
        name = person_data.get("name")
        if not name:
            raise ValueError("Name is required")

        role = person_data.get("role")
        company = person_data.get("company")
        email = person_data.get("email")
        phone = person_data.get("phone")
        contact_frequency_days = person_data.get("contact_frequency_days", 14)

        # Create in database
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT INTO people (
                    id, name, role, company, email, phone,
                    created_at, updated_at, contact_frequency_days, file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                person_id,
                name,
                role,
                company,
                email,
                phone,
                now,
                now,
                contact_frequency_days,
                f"03-people/person-{person_id}.md"
            ))
            await conn.commit()

        # Create Obsidian file
        await self._create_person_file(person_id, person_data)

        logger.info(f"Created person: {person_id} ({name})")

        return {
            "person_id": person_id,
            "name": name,
            "role": role,
            "company": company
        }

    async def get_person(self, person_id: str) -> Optional[Dict]:
        """Get person by ID"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT * FROM people
                WHERE id = ?
            """, (person_id,))
            row = await cursor.fetchone()

            if row:
                return dict(row)
            return None

    async def list_people(self, limit: int = 100) -> List[Dict]:
        """List all people"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT * FROM people
                ORDER BY name
                LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()

            return [dict(row) for row in rows]

    async def search_people(self, query: str) -> List[Dict]:
        """Search people by name, company, or role"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT * FROM people
                WHERE name LIKE ?
                   OR company LIKE ?
                   OR role LIKE ?
                ORDER BY name
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            rows = await cursor.fetchall()

            return [dict(row) for row in rows]

    async def update_person(self, person_id: str, updates: Dict) -> Dict:
        """Update person information"""
        now = datetime.now().isoformat()
        updates["updated_at"] = now

        # Build UPDATE query
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(person_id)

        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                f"UPDATE people SET {set_clause} WHERE id = ?",
                values
            )
            await conn.commit()

        # Update Obsidian file
        await self._update_person_file(person_id, updates)

        logger.info(f"Updated person: {person_id}")

        return await self.get_person(person_id)

    async def update_last_contact(self, person_id: str, contact_date: Optional[datetime] = None):
        """Update last contact date for a person"""
        if not contact_date:
            contact_date = datetime.now()

        await self.update_person(person_id, {
            "last_contact": contact_date.isoformat()
        })

        logger.info(f"Updated last contact for {person_id}")

    async def get_people_to_contact(self) -> List[Dict]:
        """Get people who should be contacted based on frequency"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT *,
                    julianday('now') - julianday(last_contact) as days_since_contact
                FROM people
                WHERE last_contact IS NOT NULL
                  AND contact_frequency_days IS NOT NULL
                  AND (julianday('now') - julianday(last_contact)) >= contact_frequency_days
                ORDER BY days_since_contact DESC
            """)
            rows = await cursor.fetchall()

            return [dict(row) for row in rows]

    async def _create_person_file(self, person_id: str, person_data: Dict):
        """Create Obsidian person file"""
        vault_path = Path(self.vault_path)
        people_dir = vault_path / "03-people"
        people_dir.mkdir(parents=True, exist_ok=True)

        file_path = people_dir / f"person-{person_id}.md"

        name = person_data.get("name", "Unknown")
        role = person_data.get("role", "")
        company = person_data.get("company", "")
        email = person_data.get("email", "")
        phone = person_data.get("phone", "")
        contact_frequency_days = person_data.get("contact_frequency_days", 14)

        content = f"""---
id: {person_id}
type: person
name: "{name}"
role: {role}
company: {company}
email: {email}
phone: {phone}
created_at: {datetime.now().isoformat()}
updated_at: {datetime.now().isoformat()}
last_contact:
contact_frequency_days: {contact_frequency_days}
tags: []
---

# {name}

## Quick Info
- **Role**: {role}
- **Company**: {company}
- **Email**: {email}
- **Phone**: {phone}

## Interaction History


## Related Tasks
```dataview
LIST
FROM "01-tasks"
WHERE contains(people_ids, "{person_id}")
SORT due_date
```

## Notes

"""

        with open(file_path, 'w') as f:
            f.write(content)

        logger.info(f"Created person file: {file_path}")

    async def _update_person_file(self, person_id: str, updates: Dict):
        """Update person file in Obsidian"""
        # This would update the Obsidian file frontmatter
        # For now, basic implementation
        pass
