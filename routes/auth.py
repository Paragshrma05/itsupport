from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from extensions import db, bcrypt
from models.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    data = request.form if request.form else request.get_json()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "user")

    if not username or not email or not password:
        if request.is_json:
            return jsonify({"error": "All fields are required."}), 400
        flash("All fields are required.", "danger")
        return render_template("register.html"), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        if request.is_json:
            return jsonify({"error": "Username or email already exists."}), 409
        flash("Username or email already taken.", "danger")
        return render_template("register.html"), 409

    hashed = bcrypt.generate_password_hash(password).decode("utf-8")
    # Only allow admin role if no admin exists yet (first user)
    if role == "admin" and User.query.filter_by(role="admin").first():
        role = "user"
    user = User(username=username, email=email, password_hash=hashed, role=role)
    db.session.add(user)
    db.session.commit()

    if request.is_json:
        return jsonify({"message": "Registered successfully.", "user": user.to_dict()}), 201
    flash("Account created! Please log in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.form if request.form else request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        if request.is_json:
            return jsonify({"error": "Invalid credentials."}), 401
        flash("Invalid email or password.", "danger")
        return render_template("login.html"), 401

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "username": user.username})

    if request.is_json:
        return jsonify({"access_token": token, "user": user.to_dict()}), 200

    response = redirect(url_for("main.dashboard"))
    set_access_cookies(response, token)
    return response


@auth_bp.route("/logout")
def logout():
    response = redirect(url_for("auth.login"))
    unset_jwt_cookies(response)
    flash("Logged out successfully.", "info")
    return response


# ── REST API ──────────────────────────────────────────────────────────────────

@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():
    return register()


@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    return login()


@auth_bp.route("/api/auth/me", methods=["GET"])
@jwt_required()
def api_me():
    uid = get_jwt_identity()
    user = User.query.get_or_404(int(uid))
    return jsonify(user.to_dict()), 200
