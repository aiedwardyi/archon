"""
JWT Authentication routes for Archon.
Phase 16.5 — register, login, forgot-password, reset-password, /me
"""
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
import bcrypt
import secrets
from datetime import datetime, timedelta, timezone
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from models import User, Project, get_session

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


def init_jwt(app):
    """Call this from app.py to wire JWT into Flask."""
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "archon-dev-secret-change-in-prod")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
    return JWTManager(app)


# ── Register ──────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    db = get_session()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({"error": "An account with this email already exists"}), 409

        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(email=email, name=name or email.split("@")[0], password_hash=pw_hash)
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(identity=str(user.id))
        return jsonify({
            "token": token,
            "user": {"id": user.id, "email": user.email, "name": user.name},
        }), 201
    finally:
        db.close()


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = get_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.password_hash:
            return jsonify({"error": "Invalid email or password"}), 401

        if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            return jsonify({"error": "Invalid email or password"}), 401

        token = create_access_token(identity=str(user.id))
        return jsonify({
            "token": token,
            "user": {"id": user.id, "email": user.email, "name": user.name},
        }), 200
    finally:
        db.close()


# ── Google OAuth ─────────────────────────────────────────────────────────────

@auth_bp.route("/google", methods=["POST"])
def google_login():
    data = request.get_json()
    credential = (data or {}).get("token") or ""
    if not credential:
        return jsonify({"error": "No Google token provided"}), 400

    try:
        idinfo = id_token.verify_oauth2_token(
            credential, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        return jsonify({"error": "Invalid Google token"}), 401

    email = idinfo.get("email", "").lower()
    name = idinfo.get("name", email.split("@")[0])

    if not email:
        return jsonify({"error": "Google account has no email"}), 400

    db = get_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, name=name, password_hash=None)
            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_access_token(identity=str(user.id))
        return jsonify({
            "access_token": token,
            "user": {"id": user.id, "email": user.email, "name": user.name},
        }), 200
    finally:
        db.close()


# ── Me (current user) ─────────────────────────────────────────────────────────

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    db = get_session()
    try:
        user = db.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"id": user.id, "email": user.email, "name": user.name}), 200
    finally:
        db.close()


# ── Forgot Password ───────────────────────────────────────────────────────────

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = (data.get("email") or "").strip().lower() if data else ""
    if not email:
        return jsonify({"error": "Email is required"}), 400

    db = get_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        # Always return success (don't leak whether email exists)
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
            db.commit()
            # In production: send email. For now, return token in response (dev mode)
            print(f"[DEV] Password reset token for {email}: {token}")
            return jsonify({
                "message": "If that email exists, a reset link has been sent.",
                "_dev_token": token,  # Remove in production
            }), 200
        return jsonify({"message": "If that email exists, a reset link has been sent."}), 200
    finally:
        db.close()


# ── Reset Password ────────────────────────────────────────────────────────────

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    token = data.get("token") or ""
    password = data.get("password") or ""

    if not token or not password:
        return jsonify({"error": "Token and new password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    db = get_session()
    try:
        user = db.query(User).filter(User.reset_token == token).first()
        if not user:
            return jsonify({"error": "Invalid or expired reset token"}), 400
        if user.reset_token_expires and datetime.now(timezone.utc) > user.reset_token_expires.replace(tzinfo=timezone.utc):
            return jsonify({"error": "Reset token has expired"}), 400

        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user.password_hash = pw_hash
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()

        return jsonify({"message": "Password reset successfully. You can now log in."}), 200
    finally:
        db.close()
