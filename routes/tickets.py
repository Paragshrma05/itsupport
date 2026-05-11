from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from datetime import datetime, timezone
from extensions import db
from models.models import Ticket, User
from services.ai_service import categorize_ticket

tickets_bp = Blueprint("tickets", __name__)


def _current_user():
    verify_jwt_in_request(locations=["cookies", "headers"])
    uid = get_jwt_identity()
    claims = get_jwt()
    return User.query.get(int(uid)), claims.get("role", "user")


# ── WEB VIEWS ─────────────────────────────────────────────────────────────────

@tickets_bp.route("/tickets")
def ticket_list():
    try:
        user, role = _current_user()
    except Exception:
        return redirect(url_for("auth.login"))

    status_filter = request.args.get("status", "")
    priority_filter = request.args.get("priority", "")
    category_filter = request.args.get("category", "")
    search = request.args.get("q", "")

    query = Ticket.query if role == "admin" else Ticket.query.filter_by(user_id=user.id)

    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if category_filter:
        query = query.filter_by(category=category_filter)
    if search:
        query = query.filter(Ticket.title.ilike(f"%{search}%") | Ticket.description.ilike(f"%{search}%"))

    tickets = query.order_by(Ticket.created_at.desc()).all()
    return render_template("tickets.html", tickets=tickets, user=user, role=role,
                           status_filter=status_filter, priority_filter=priority_filter,
                           category_filter=category_filter, search=search)


@tickets_bp.route("/tickets/new", methods=["GET", "POST"])
def new_ticket():
    try:
        user, role = _current_user()
    except Exception:
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        return render_template("new_ticket.html", user=user, role=role)

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if not title or not description:
        flash("Title and description are required.", "danger")
        return render_template("new_ticket.html", user=user, role=role)

    ai_result = categorize_ticket(title, description)
    suggestions_text = "\n".join(f"• {s}" for s in ai_result.get("suggestions", []))

    ticket = Ticket(
        title=title,
        description=description,
        category=ai_result.get("category", "Other"),
        priority=ai_result.get("priority", "Medium"),
        status="Open",
        ai_suggestions=suggestions_text,
        user_id=user.id,
    )
    db.session.add(ticket)
    db.session.commit()
    flash(f"Ticket #{ticket.id} created successfully!", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@tickets_bp.route("/tickets/<int:ticket_id>")
def ticket_detail(ticket_id):
    try:
        user, role = _current_user()
    except Exception:
        return redirect(url_for("auth.login"))

    ticket = Ticket.query.get_or_404(ticket_id)
    if role != "admin" and ticket.user_id != user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("tickets.ticket_list"))

    return render_template("ticket_detail.html", ticket=ticket, user=user, role=role)


@tickets_bp.route("/tickets/<int:ticket_id>/update", methods=["POST"])
def update_ticket(ticket_id):
    try:
        user, role = _current_user()
    except Exception:
        return redirect(url_for("auth.login"))

    ticket = Ticket.query.get_or_404(ticket_id)
    if role != "admin" and ticket.user_id != user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("tickets.ticket_list"))

    if role == "admin":
        ticket.status = request.form.get("status", ticket.status)
        ticket.priority = request.form.get("priority", ticket.priority)
        ticket.category = request.form.get("category", ticket.category)
    ticket.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Ticket updated.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))


@tickets_bp.route("/tickets/<int:ticket_id>/delete", methods=["POST"])
def delete_ticket(ticket_id):
    try:
        user, role = _current_user()
    except Exception:
        return redirect(url_for("auth.login"))

    ticket = Ticket.query.get_or_404(ticket_id)
    if role != "admin" and ticket.user_id != user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("tickets.ticket_list"))

    db.session.delete(ticket)
    db.session.commit()
    flash("Ticket deleted.", "info")
    return redirect(url_for("tickets.ticket_list"))


# ── REST API ──────────────────────────────────────────────────────────────────

@tickets_bp.route("/api/tickets", methods=["GET"])
@jwt_required()
def api_list_tickets():
    uid = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role", "user")

    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")
    search = request.args.get("q")

    query = Ticket.query if role == "admin" else Ticket.query.filter_by(user_id=int(uid))
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if search:
        query = query.filter(Ticket.title.ilike(f"%{search}%"))

    tickets = query.order_by(Ticket.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tickets]), 200


@tickets_bp.route("/api/tickets", methods=["POST"])
@jwt_required()
def api_create_ticket():
    uid = get_jwt_identity()
    data = request.get_json()
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()

    if not title or not description:
        return jsonify({"error": "Title and description required."}), 400

    ai_result = categorize_ticket(title, description)
    suggestions_text = "\n".join(f"• {s}" for s in ai_result.get("suggestions", []))
    ticket = Ticket(
        title=title, description=description,
        category=ai_result.get("category", "Other"),
        priority=ai_result.get("priority", "Medium"),
        status="Open", ai_suggestions=suggestions_text,
        user_id=int(uid),
    )
    db.session.add(ticket)
    db.session.commit()
    return jsonify({"ticket": ticket.to_dict(), "ai_analysis": ai_result}), 201


@tickets_bp.route("/api/tickets/<int:ticket_id>", methods=["GET"])
@jwt_required()
def api_get_ticket(ticket_id):
    uid = get_jwt_identity()
    claims = get_jwt()
    ticket = Ticket.query.get_or_404(ticket_id)
    if claims.get("role") != "admin" and ticket.user_id != int(uid):
        return jsonify({"error": "Forbidden"}), 403
    return jsonify(ticket.to_dict()), 200


@tickets_bp.route("/api/tickets/<int:ticket_id>", methods=["PATCH"])
@jwt_required()
def api_update_ticket(ticket_id):
    uid = get_jwt_identity()
    claims = get_jwt()
    ticket = Ticket.query.get_or_404(ticket_id)
    if claims.get("role") != "admin" and ticket.user_id != int(uid):
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    for field in ["status", "priority", "category", "title", "description"]:
        if field in data:
            setattr(ticket, field, data[field])
    ticket.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(ticket.to_dict()), 200


@tickets_bp.route("/api/tickets/<int:ticket_id>", methods=["DELETE"])
@jwt_required()
def api_delete_ticket(ticket_id):
    uid = get_jwt_identity()
    claims = get_jwt()
    ticket = Ticket.query.get_or_404(ticket_id)
    if claims.get("role") != "admin" and ticket.user_id != int(uid):
        return jsonify({"error": "Forbidden"}), 403
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({"message": "Deleted."}), 200
