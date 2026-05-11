from datetime import datetime, timezone
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="user")  # 'admin' or 'user'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    tickets = db.relationship("Ticket", foreign_keys="Ticket.user_id", backref="author", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
        }


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="General")
    priority = db.Column(db.String(20), default="Medium")  # Low, Medium, High, Critical
    status = db.Column(db.String(20), default="Open")  # Open, In Progress, Resolved
    ai_suggestions = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "ai_suggestions": self.ai_suggestions,
            "user_id": self.user_id,
            "author": self.author.username if self.author else None,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
