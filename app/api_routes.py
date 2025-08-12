import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.extensions import db, bcrypt, csrf
from app.models import User, LostItem, ClaimRequest
from flask_login import current_user, login_required, login_user, logout_user
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

# Create Blueprint
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Disable CSRF for API routes
csrf.exempt(api_bp)

# Allowed image extensions for upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------------
# REGISTER
# --------------------------
@api_bp.route("/register", methods=["POST"])
def api_register():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password") or not data.get("username"):
        return jsonify({"error": "Username, email, and password are required"}), 400

    existing_user = User.query.filter(
        (User.email == data["email"]) | (User.username == data["username"])
    ).first()
    if existing_user:
        return jsonify({"error": "User with that email or username already exists"}), 400

    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    user = User(username=data["username"], email=data["email"], password=hashed_pw)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

# --------------------------
# LOGIN
# --------------------------
@api_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if user and bcrypt.check_password_hash(user.password, data["password"]):
        login_user(user)
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# --------------------------
# LOGOUT
# --------------------------
@api_bp.route("/logout", methods=["POST"])
@login_required
def api_logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

# --------------------------
# LOST ITEMS HELPERS
# --------------------------
def validate_item_data(data, require_all=True):
    """Validate incoming data for LostItem."""
    required_fields = ["title", "description", "location", "contact_info"]
    missing_fields = [f for f in required_fields if not data.get(f)]

    if require_all and missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    return True, None

# --------------------------
# CREATE ITEM (with image upload)
# --------------------------
# @login_required
@api_bp.route("/items", methods=["POST"])
def create_item():
    # Extract data from form-data
    title = request.form.get("title")
    description = request.form.get("description")
    location = request.form.get("location")
    contact_info = request.form.get("contact_info")
    print("request.form:", request.form)
    print("request.files:", request.files)

    if not title or not description or not location or not contact_info:
        return jsonify({"error": "Missing required fields"}), 400

    image_file = None
    file = request.files.get("image_file") or request.files.get("image-file")
    if file:
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, "static/uploads")
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            image_file = filename
        else:
            return jsonify({"error": "Invalid image format"}), 400

    try:
        new_item = LostItem(
            title=title,
            description=description,
            location=location,
            contact_info=contact_info,
            image_file=image_file,
            date_posted=datetime.utcnow(),
            user_id=current_user.id
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"message": "Item created successfully", "id": new_item.id}), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
        
# --------------------------
# GET ALL ITEMS
# --------------------------
@api_bp.route("/items", methods=["GET"])
def get_items():
    items = LostItem.query.all()
    return jsonify([
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "location": item.location,
            "contact_info": item.contact_info,
            "image_file": item.image_file,
            "date_posted": item.date_posted.isoformat(),
            "user_id": item.user_id
        }
        for item in items
    ]), 200

# --------------------------
# GET SINGLE ITEM
# --------------------------
@api_bp.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = LostItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    return jsonify({
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "location": item.location,
        "contact_info": item.contact_info,
        "image_file": item.image_file,
        "date_posted": item.date_posted.isoformat(),
        "user_id": item.user_id
    }), 200

# --------------------------
# UPDATE ITEM
# --------------------------
@api_bp.route("/items/<int:item_id>", methods=["PUT"])
@login_required
def update_item(item_id):
    item = LostItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    if item.user_id != current_user.id:
        return jsonify({"error": "You can only update your own items"}), 403

    data = request.get_json() or {}
    valid, error = validate_item_data(data, require_all=False)
    if not valid:
        return jsonify({"error": error}), 400

    item.title = data.get("title", item.title)
    item.description = data.get("description", item.description)
    item.location = data.get("location", item.location)
    item.contact_info = data.get("contact_info", item.contact_info)
    item.image_file = data.get("image_file", item.image_file)

    db.session.commit()
    return jsonify({"message": "Item updated successfully"}), 200

# --------------------------
# DELETE ITEM
# --------------------------
@api_bp.route("/items/<int:item_id>", methods=["DELETE"])
@login_required
def delete_item(item_id):
    item = LostItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    if item.user_id != current_user.id:
        return jsonify({"error": "You can only delete your own items"}), 403

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted successfully"}), 200

# --------------------------
# CLAIMS
# --------------------------
@api_bp.route("/claims", methods=["POST"])
def create_claim():
    data = request.get_json()
    if not data or not data.get("message") or not data.get("user_id") or not data.get("item_id"):
        return jsonify({"error": "Missing required fields"}), 400

    claim = ClaimRequest(
        message=data["message"],
        user_id=data["user_id"],
        item_id=data["item_id"]
    )
    db.session.add(claim)
    db.session.commit()
    return jsonify({"message": "Claim created", "claim_id": claim.id}), 201

@api_bp.route("/claims", methods=["GET"])
def get_claims():
    claims = ClaimRequest.query.all()
    return jsonify([
        {
            "claim_id": c.id,
            "message": c.message,
            "user_id": c.user_id,
            "item_id": c.item_id,
            "status": getattr(c, "status", None)
        } for c in claims
    ]), 200

@api_bp.route("/claims/<int:claim_id>", methods=["PUT"])
def update_claim(claim_id):
    claim = ClaimRequest.query.get_or_404(claim_id)
    data = request.get_json()
    if not data or not data.get("status"):
        return jsonify({"error": "Missing status"}), 400
    claim.status = data["status"]
    db.session.commit()
    return jsonify({"message": "Claim updated"}), 200

@api_bp.route("/claims/<int:claim_id>", methods=["DELETE"])
def delete_claim(claim_id):
    claim = ClaimRequest.query.get_or_404(claim_id)
    db.session.delete(claim)
    db.session.commit()
    return jsonify({"message": "Claim deleted"}), 200
