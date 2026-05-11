from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt, jwt_required
from extensions import db
from models.models import Ticket, User
from services.ai_service import analyze_log

main_bp = Blueprint("main", __name__)


def _current_user():
    verify_jwt_in_request(locations=["cookies", "headers"])
    uid = get_jwt_identity()
    claims = get_jwt()
    return User.query.get(int(uid)), claims.get("role", "user")


@main_bp.route("/")
def index():
    try:
        _current_user()
        return redirect(url_for("main.dashboard"))
    except Exception:
        return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
def dashboard():
    try:
        user, role = _current_user()
    except Exception:
        return redirect(url_for("auth.login"))

    if role == "admin":
        total = Ticket.query.count()
        open_count = Ticket.query.filter_by(status="Open").count()
        in_progress = Ticket.query.filter_by(status="In Progress").count()
        resolved = Ticket.query.filter_by(status="Resolved").count()
        critical = Ticket.query.filter_by(priority="Critical").count()
        recent_tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(8).all()
        total_users = User.query.count()
        return render_template("dashboard_admin.html",
                               user=user, role=role,
                               total=total, open_count=open_count,
                               in_progress=in_progress, resolved=resolved,
                               critical=critical, recent_tickets=recent_tickets,
                               total_users=total_users)
    else:
        my_tickets = Ticket.query.filter_by(user_id=user.id).order_by(Ticket.created_at.desc()).limit(5).all()
        my_open = Ticket.query.filter_by(user_id=user.id, status="Open").count()
        my_total = Ticket.query.filter_by(user_id=user.id).count()
        return render_template("dashboard_user.html",
                               user=user, role=role,
                               my_tickets=my_tickets,
                               my_open=my_open, my_total=my_total)


@main_bp.route("/log-analyzer", methods=["GET", "POST"])
def log_analyzer():
    try:
        user, role = _current_user()
    except Exception:
        return redirect(url_for("auth.login"))

    result = None
    if request.method == "POST":
        log_text = ""
        if "log_file" in request.files and request.files["log_file"].filename:
            file = request.files["log_file"]
            try:
                log_text = file.read().decode("utf-8", errors="ignore")
            except Exception:
                flash("Could not read file.", "danger")
        else:
            log_text = request.form.get("log_text", "").strip()

        if not log_text:
            flash("Please provide log content.", "warning")
        else:
            result = analyze_log(log_text)

    return render_template("log_analyzer.html", user=user, role=role, result=result)


# ── REST API ──────────────────────────────────────────────────────────────────

@main_bp.route("/api/analyze-log", methods=["POST"])
@jwt_required()
def api_analyze_log():
    data = request.get_json()
    log_text = data.get("log_text", "").strip()
    if not log_text:
        return jsonify({"error": "log_text is required."}), 400
    result = analyze_log(log_text)
    return jsonify(result), 200


@main_bp.route("/api/stats", methods=["GET"])
@jwt_required()
def api_stats():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin only."}), 403
    return jsonify({
        "total_tickets": Ticket.query.count(),
        "open": Ticket.query.filter_by(status="Open").count(),
        "in_progress": Ticket.query.filter_by(status="In Progress").count(),
        "resolved": Ticket.query.filter_by(status="Resolved").count(),
        "critical": Ticket.query.filter_by(priority="Critical").count(),
        "total_users": User.query.count(),
    }), 200


@main_bp.route("/api/users", methods=["GET"])
@jwt_required()
def api_users():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin only."}), 403
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200
