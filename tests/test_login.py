# test_login.py
import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
from passlib.hash import bcrypt
from login_server import app, get_db

# Create a new SQLite database for testing
TEST_DATABASE_URL = "sqlite:///./test_users.db"

# Set up the database engine and session maker
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_db dependency to use the test database
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# Create the test database and tables
@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Insert sample users into the test database
@pytest.fixture(scope="module")
def sample_users():
    db = TestingSessionLocal()
    hashed_password_admin = bcrypt.hash("admin123")
    admin_user = User(
        username="adminuser", password=hashed_password_admin, role="admin"
    )

    hashed_password_user = bcrypt.hash("user123")
    regular_user = User(
        username="regularuser", password=hashed_password_user, role="user"
    )

    db.add(admin_user)
    db.add(regular_user)
    db.commit()
    db.close()


@pytest.mark.asyncio
async def test_login_admin(sample_users):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/login", data={"username": "adminuser", "password": "admin123"}
        )
    assert response.status_code == 200
    assert '<input type="hidden" name="role" value="admin">' in response.text


@pytest.mark.asyncio
async def test_login_user(sample_users):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/login", data={"username": "regularuser", "password": "user123"}
        )
    assert response.status_code == 200
    assert '<input type="hidden" name="role" value="user">' in response.text


@pytest.mark.asyncio
async def test_login_invalid_user(sample_users):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/login", data={"username": "invaliduser", "password": "invalidpass"}
        )
    assert response.status_code == 200
    assert "Invalid username or password" in response.text
