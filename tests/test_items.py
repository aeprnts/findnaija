#tests/test_items.py
import pytest
from app import create_app, db
from app.models import LostItem, User
from app.extensions import bcrypt

@pytest.fixture
def client():
    app = create_app(testing=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        hashed_pw = bcrypt.generate_password_hash("plm1234").decode("utf-8")
        user = User(username="hihello", email="hihelloit6@gmail.com", password=hashed_pw)
        db.session.add(user)
        db.session.commit()

        client.post("/api/register", json={
            "username": "hihello",
            "email": "hihelloit6@gmail.com",
            "password": "plm1234"
        })
        res = client.post("/api/login", json={
            "email": "hihelloit6@gmail.com",
            "password": "plm1234"
        })
        assert res.status_code == 200

        yield app.test_client()
        db.session.remove()
        db.drop_all()

def test_create_item_success(client):
    """Positive: Create a lost item."""
    res = client.post("/api/items", json={
        "title": "Lost Wallet",
        "description": "Black leather wallet",
        "location": "Library",
        "contact_info": "hihelloit6@gmail.com",
        "user_id": 1
    })
    assert res.status_code == 201
    assert "item_id" in res.get_json()

def test_create_item_missing_fields(client):
    """Negative: Missing fields should fail."""
    res = client.post("/api/items", json={
        "title": "Wallet"
    })
    assert res.status_code == 400

def test_get_items(client):
    """Positive: Get all items."""
    client.post("/api/items", json={
        "title": "Lost Wallet",
        "description": "Black leather wallet",
        "location": "Library",
        "contact_info": "hihelloit6@gmail.com",
        "user_id": 1
    })
    res = client.get("/api/items")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)

def test_update_item_success(client):
    """Positive: Update an item."""
    post = client.post("/api/items", json={
        "title": "Lost Wallet",
        "description": "Black leather wallet",
        "location": "Library",
        "contact_info": "hihelloit6@gmail.com",
        "user_id": 1
    })
    item_id = post.get_json()["item_id"]

    res = client.put(f"/api/items/{item_id}", json={"title": "Updated Wallet"})
    assert res.status_code == 200

def test_delete_item_success(client):
    """Positive: Delete an item."""
    post = client.post("/api/items", json={
        "title": "Lost Wallet",
        "description": "Black leather wallet",
        "location": "Library",
        "contact_info": "hihelloit6@gmail.com",
        "user_id": 1
    })
    item_id = post.get_json()["item_id"]

    res = client.delete(f"/api/items/{item_id}")
    assert res.status_code == 200
