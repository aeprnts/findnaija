#test/test_users.py
import pytest
from app import create_app, db
from app.models import User
from app.extensions import bcrypt

@pytest.fixture
def client():
    """Setup Flask test client with in-memory DB."""
    app = create_app(testing=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def test_register_success(client):
    """Positive: Successfully register a user."""
    res = client.post("/api/register", json={
        "username": "hihello",
        "email": "hihelloit6@gmail.com",
        "password": "plm1234"
    })
    assert res.status_code == 201
    assert "user_id" in res.get_json()

def test_register_missing_fields(client):
    """Negative: Missing fields should fail."""
    res = client.post("/api/register", json={
        "username": "hihello"
    })
    assert res.status_code == 400

def test_login_success(client):
    """Positive: Login works with correct credentials."""
    hashed_pw = bcrypt.generate_password_hash("123456").decode("utf-8")
    user = User(username="hihello", email="hihelloit6@gmail.com", password=hashed_pw)
    db.session.add(user)
    db.session.commit()

    res = client.post("/api/login", json={
        "email": "hihelloit6@gmail.com",
        "password": "plm1234"
    })
    assert res.status_code == 200
    assert res.get_json()["message"] == "Login successful"

def test_login_invalid_credentials(client):
    """Negative: Invalid password should fail."""
    res = client.post("/api/login", json={
        "email": "exist@gmail.com",
        "password": "nopenope"
    })
    assert res.status_code == 401
