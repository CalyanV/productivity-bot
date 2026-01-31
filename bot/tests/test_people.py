import pytest
from datetime import datetime
from src.people import PeopleManager

@pytest.mark.asyncio
async def test_people_manager_initialization(tmp_path):
    """Test PeopleManager initializes correctly"""
    db_path = tmp_path / "test.db"

    manager = PeopleManager(
        db_path=str(db_path),
        vault_path="/tmp/vault"
    )

    assert manager.db_path == str(db_path)
    assert manager.vault_path == "/tmp/vault"

@pytest.mark.asyncio
async def test_create_person(tmp_path):
    """Test creating a person"""
    db_path = tmp_path / "test.db"

    manager = PeopleManager(
        db_path=str(db_path),
        vault_path=str(tmp_path / "vault")
    )

    await manager.initialize()

    person_data = {
        "name": "John Doe",
        "role": "Engineering Manager",
        "company": "Tech Corp",
        "email": "john@techcorp.com",
        "contact_frequency_days": 14
    }

    result = await manager.create_person(person_data)

    assert result is not None
    assert "person_id" in result
    assert result["name"] == "John Doe"

@pytest.mark.asyncio
async def test_get_person(tmp_path):
    """Test retrieving a person"""
    db_path = tmp_path / "test.db"

    manager = PeopleManager(
        db_path=str(db_path),
        vault_path=str(tmp_path / "vault")
    )

    await manager.initialize()

    # Create person
    person_data = {"name": "Jane Smith"}
    result = await manager.create_person(person_data)
    person_id = result["person_id"]

    # Retrieve person
    person = await manager.get_person(person_id)

    assert person is not None
    assert person["name"] == "Jane Smith"

@pytest.mark.asyncio
async def test_list_people(tmp_path):
    """Test listing all people"""
    db_path = tmp_path / "test.db"

    manager = PeopleManager(
        db_path=str(db_path),
        vault_path=str(tmp_path / "vault")
    )

    await manager.initialize()

    # Create multiple people
    await manager.create_person({"name": "Person A"})
    await manager.create_person({"name": "Person B"})

    # List all
    people = await manager.list_people()

    assert len(people) == 2

@pytest.mark.asyncio
async def test_search_people(tmp_path):
    """Test searching for people by name"""
    db_path = tmp_path / "test.db"

    manager = PeopleManager(
        db_path=str(db_path),
        vault_path=str(tmp_path / "vault")
    )

    await manager.initialize()

    # Create people
    await manager.create_person({"name": "John Doe"})
    await manager.create_person({"name": "Jane Smith"})

    # Search
    results = await manager.search_people("John")

    assert len(results) == 1
    assert results[0]["name"] == "John Doe"

@pytest.mark.asyncio
async def test_update_last_contact(tmp_path):
    """Test updating last contact date"""
    db_path = tmp_path / "test.db"

    manager = PeopleManager(
        db_path=str(db_path),
        vault_path=str(tmp_path / "vault")
    )

    await manager.initialize()

    # Create person
    result = await manager.create_person({"name": "Test Person"})
    person_id = result["person_id"]

    # Update last contact
    await manager.update_last_contact(person_id)

    # Verify
    person = await manager.get_person(person_id)
    assert person["last_contact"] is not None
