import pytest
from app import create_app, db
from app.models import ClaimRequest, LostItem, User
from app.extensions import bcrypt

@pytest.fixture
def client():
    app = create_app(testing=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        # Create test user
        hashed_pw = bcrypt.generate_password_hash("123456").decode("utf-8")
        user = User(username="hihello", email="hihelloit6@gmail.com", password=hashed_pw)
        db.session.add(user)
        # Create a lost item
        item = LostItem(title="Lost Wallet", description="Black leather wallet",
                        location="Library", contact_info="hihelloit6@gmail.com", user_id=1)
        db.session.add(item)
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def login(client):
    """Helper function to log in the test user."""
    client.post("/api/login", json={
        "email": "hihelloit6@gmail.com",
        "password": "123456"
    })

def test_create_claim_success(client):
    """Positive: Create a claim."""
    login(client)
    res = client.post("/api/claims", data={
        "message": "I found it",
        "item_id": 1
    })
    assert res.status_code == 201
    data = res.get_json()
    assert "claim_id" in data
    assert data["message"] == "Claim created"

def test_create_claim_missing_fields(client):
    """Negative: Missing fields should fail."""
    login(client)
    res = client.post("/api/claims", data={"message": "I found it"})
    assert res.status_code == 400

def test_get_claims(client):
    """Positive: Get claims."""
    login(client)
    client.post("/api/claims", data={"message": "I found it", "item_id": 1})
    res = client.get("/api/claims")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_update_claim_success(client):
    """Positive: Update claim."""
    login(client)
    post = client.post("/api/claims", data={"message": "I found it", "item_id": 1})
    claim_id = post.get_json()["claim_id"]

    res = client.put(f"/api/claims/{claim_id}", json={"status": "Approved"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["message"] == "Claim updated"

def test_delete_claim_success(client):
    """Positive: Delete claim."""
    login(client)
    post = client.post("/api/claims", data={"message": "I found it", "item_id": 1})
    claim_id = post.get_json()["claim_id"]

    res = client.delete(f"/api/claims/{claim_id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["message"] == "Claim deleted"
