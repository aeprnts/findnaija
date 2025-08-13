# routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import os
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import HiddenField

# Models
from app.models import User, LostItem, ClaimRequest

# Forms
from app.forms import RegistrationForm, LoginForm, LostItemForm, ClaimForm

# Extensions
from app.extensions import db, bcrypt, login_manager, csrf

main = Blueprint('main', __name__)

# ------------------- HOME -------------------
@main.route('/')
def home():
    return redirect(url_for('main.login'))

# ------------------- REGISTER -------------------
@csrf.exempt
@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.email == form.email.data) | (User.username == form.username.data)
        ).first()
        if existing_user:
            flash('⚠️ Email or username already taken.', 'danger')
            return render_template('register.html', form=form)

        try:
            hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
            db.session.add(user)
            db.session.commit()
            flash('✅ Account created! You can now log in.', 'success')
            return redirect(url_for('main.login'))
        except IntegrityError:
            db.session.rollback()
            flash('❌ Email already exists. Try another one.', 'danger')
        except SQLAlchemyError:
            db.session.rollback()
            flash('🚫 Database error. Try again later.', 'danger')
    return render_template('register.html', form=form)

# ------------------- LOGIN -------------------
@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('main.dashboard'))
            else:
                flash('Login failed. Check email and password.', 'danger')
        except SQLAlchemyError:
            flash('⚠️ Unable to connect. Try again.', 'danger')
    return render_template('login.html', form=form)

# ------------------- DASHBOARD -------------------
@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# ------------------- LOGOUT -------------------
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You’ve been logged out.", "success")
    return redirect(url_for('main.login'))

# ------------------- POST LOST ITEM -------------------
@main.route('/post-item', methods=['GET', 'POST'])
@login_required
def post_item():
    form = LostItemForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image_file.data:
            image = form.image_file.data
            image_filename = secure_filename(image.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            image.save(os.path.join(upload_folder, image_filename))

        item = LostItem(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            contact_info=form.contact_info.data,
            image_file=image_filename,
            user_id=current_user.id
        )
        try:
            db.session.add(item)
            db.session.commit()
            flash('Item posted successfully!', 'success')
            return redirect(url_for('main.view_items'))
        except SQLAlchemyError:
            db.session.rollback()
            flash('🚫 Error saving item.', 'danger')

    return render_template('post_item.html', form=form)

# ------------------- VIEW LOST ITEMS -------------------
@main.route('/items')
def view_items():
    items = LostItem.query.order_by(LostItem.date_posted.desc()).all()
    return render_template('items.html', items=items)

# ------------------- VIEW MY ITEMS -------------------
class DummyForm(FlaskForm):
    pass

@main.route('/my-items')
@login_required
def my_items():
    items = LostItem.query.filter_by(user_id=current_user.id).order_by(LostItem.date_posted.desc()).all()
    form = DummyForm()
    return render_template('my_items.html', items=items, form=form)

# ------------------- DELETE ITEM -------------------
@main.route('/delete-item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = LostItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("⛔ Not authorized.", "danger")
        return redirect(url_for('main.my_items'))

    try:
        # Delete associated claims first
        ClaimRequest.query.filter_by(item_id=item.id).delete()
        db.session.delete(item)
        db.session.commit()
        flash("✅ Item deleted.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"⚠️ Error deleting item: {e}", "danger")

    return redirect(url_for('main.my_items'))
# ------------------- EDIT ITEM -------------------
@main.route('/edit-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = LostItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("⛔ Not authorized.", "danger")
        return redirect(url_for('main.my_items'))

    form = LostItemForm(obj=item)
    if form.validate_on_submit():
        item.title = form.title.data
        item.description = form.description.data
        item.location = form.location.data
        item.contact_info = form.contact_info.data

        if form.image_file.data and hasattr(form.image_file.data, 'filename'):
            image = form.image_file.data
            image_filename = secure_filename(image.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            image.save(os.path.join(upload_folder, image_filename))
            item.image_file = image_filename

        try:
            db.session.commit()
            flash('✅ Item updated.', 'success')
            return redirect(url_for('main.my_items'))
        except SQLAlchemyError:
            db.session.rollback()
            flash('🚫 Error updating item.', 'danger')

    return render_template('edit_item.html', form=form, item=item)

# ------------------- CLAIM ITEM -------------------
@main.route('/claim-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def claim_item(item_id):
    item = LostItem.query.get_or_404(item_id)
    user_claim = ClaimRequest.query.filter_by(user_id=current_user.id, item_id=item.id).first()

    if item.user_id == current_user.id:
        flash("⛔ You cannot claim your own item.", "danger")
        return redirect(url_for('main.view_items'))

    if request.method == "POST":
        if user_claim:
            flash("⚠️ You have already claimed this item.", "warning")
            return redirect(url_for('main.claim_item', item_id=item.id))

        message = request.form.get("message")
        claim_image = request.files.get("claim_image")
        image_filename = None

        if claim_image and claim_image.filename != "":
            image_filename = secure_filename(claim_image.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'claims')
            os.makedirs(upload_folder, exist_ok=True)
            claim_image.save(os.path.join(upload_folder, image_filename))

        claim = ClaimRequest(
            message=message,
            image_file=image_filename,
            user_id=current_user.id,
            item_id=item.id
        )

        db.session.add(claim)
        db.session.commit()
        flash("✅ Claim request sent!", "success")
        return redirect(url_for('main.view_items'))

    return render_template('claim_item.html', item=item, user_claim=user_claim)

# ------------------- MANAGE CLAIMS -------------------
@main.route('/manage-claims/<int:item_id>')
@login_required
def manage_claims(item_id):
    item = LostItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("⛔ Not authorized.", "danger")
        return redirect(url_for('main.dashboard'))

    claims = ClaimRequest.query.filter_by(item_id=item_id).all()
    return render_template('manage_claims.html', item=item, claims=claims)

# ------------------- UPDATE CLAIM -------------------
@main.route('/update-claim/<int:claim_id>/<string:status>')
@login_required
def update_claim(claim_id, status):
    claim = ClaimRequest.query.get_or_404(claim_id)
    if claim.item.user_id != current_user.id:
        flash("⛔ Not authorized.", "danger")
        return redirect(url_for('main.dashboard'))

    claim.status = status
    db.session.commit()
    flash(f"✅ Claim {status.lower()}!", "success")
    return redirect(url_for('main.manage_claims', item_id=claim.item_id))

# ------------------- DELETE CLAIM -------------------
@main.route("/delete-claim/<int:claim_id>", methods=["GET", "POST"])
@login_required
def delete_claim(claim_id):
    claim = ClaimRequest.query.get_or_404(claim_id)
    if claim.user_id != current_user.id and claim.item.user_id != current_user.id:
        flash("⛔ Not authorized.", "danger")
        return redirect(url_for('main.dashboard'))

    db.session.delete(claim)
    db.session.commit()
    flash("🗑️ Claim deleted!", "success")

    if current_user.id == claim.user_id:
        return redirect(url_for('main.view_items'))
    else:
        return redirect(url_for('main.manage_claims', item_id=claim.item_id))
