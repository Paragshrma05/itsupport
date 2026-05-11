import os
from flask import Flask
from config import Config
from extensions import db, bcrypt, jwt, cors


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # JWT cookie config
    app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
    app.config["JWT_COOKIE_SECURE"] = False  # Set True in production with HTTPS
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False

    # Register blueprints
    from routes.auth import auth_bp
    from routes.tickets import tickets_bp
    from routes.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(main_bp)

    # Create tables and seed admin
    with app.app_context():
        os.makedirs("instance", exist_ok=True)
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    from extensions import bcrypt as bc
    from models.models import User, Ticket

    if User.query.count() == 0:
        admin = User(
            username="admin",
            email="admin@itsupport.dev",
            password_hash=bc.generate_password_hash("admin123").decode("utf-8"),
            role="admin",
        )
        user = User(
            username="jsmith",
            email="jsmith@itsupport.dev",
            password_hash=bc.generate_password_hash("user123").decode("utf-8"),
            role="user",
        )
        db.session.add_all([admin, user])
        db.session.flush()

        sample_tickets = [
            Ticket(title="VPN not connecting from home", description="I cannot connect to the company VPN since yesterday. Getting error: 'Authentication failed'. I've tried resetting my password.", category="Network", priority="High", status="Open", ai_suggestions="• Verify VPN credentials are correct.\n• Check if MFA token is required.\n• Try a different network connection.", user_id=user.id),
            Ticket(title="Outlook keeps crashing on startup", description="Microsoft Outlook crashes immediately after opening. Running Windows 11, Outlook 2021.", category="Software", priority="Medium", status="In Progress", ai_suggestions="• Start Outlook in Safe Mode (outlook /safe).\n• Repair Office installation via Control Panel.\n• Check for Windows updates.", user_id=user.id),
            Ticket(title="Database connection timeout in production", description="Our production app is throwing DB connection timeout errors since 2am. Multiple services affected.", category="Database", priority="Critical", status="Open", ai_suggestions="• Check DB server health and connection pool.\n• Review max_connections setting.\n• Check for long-running queries locking tables.", user_id=admin.id),
            Ticket(title="Forgot password - account locked", description="I entered the wrong password 5 times and now my account is locked. Need urgent access.", category="Authentication", priority="High", status="Resolved", ai_suggestions="• Admin can unlock account via Active Directory.\n• Reset password via IT portal.\n• Enable MFA to prevent future lockouts.", user_id=user.id),
        ]
        db.session.add_all(sample_tickets)
        db.session.commit()
