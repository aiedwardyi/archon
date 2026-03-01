"""
Database models for AI Dev Team system.

Tables:
- User: Account model (Phase 13 foundation)
- Project: Named projects that group related executions
- Execution: Individual task executions linked to projects
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, Boolean, ForeignKey, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from pathlib import Path

Base = declarative_base()


class User(Base):
    """User account with JWT auth (Phase 16.5)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    projects = relationship("Project", back_populates="owner")


class Project(Base):
    """
    Represents a named project (e.g., "Calculator App", "Portfolio Site").
    A project groups related executions together for organization.
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    locked_ui_archetype = Column(String(50), nullable=True)

    # Owner FK (Phase 13) -- nullable, no breaking change
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="projects")

    # Relationship: one project has many executions
    executions = relationship("Execution", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self):
        max_version = max((e.version for e in self.executions), default=0) if self.executions else 0
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "execution_count": len(self.executions) if self.executions else 0,
            "version_count": max_version,
        }


class Execution(Base):
    """
    Represents a single versioned execution (pipeline run) within a project.
    Each execution is a complete snapshot -- nothing is overwritten.
    Version numbers auto-increment per project (not globally).
    """
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Version tracking (Phase 7A)
    version = Column(Integer, nullable=False, default=1)

    # prompt_history: full conversation array as JSON string
    prompt_history = Column(Text, nullable=True)

    # is_active_head: True for the "current" version of the project
    is_active_head = Column(Boolean, nullable=False, default=True)

    # parent_execution_id: points to the previous version
    parent_execution_id = Column(Integer, ForeignKey("executions.id"), nullable=True)

    # Artifact file paths
    prd_path = Column(String(500), nullable=True)
    plan_path = Column(String(500), nullable=True)
    request_path = Column(String(500), nullable=True)
    result_path = Column(String(500), nullable=True)

    # Error message if execution failed
    error_message = Column(Text, nullable=True)

    # Publish slug (Phase 8.1)
    published_slug = Column(String(100), nullable=True)

    # Chat messages (Phase 13) -- JSON array of {role, content, timestamp}
    chat_messages = Column(Text, nullable=True)

    # Build metrics
    tokens_used = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    credits_used = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    model_used = Column(String(100), nullable=True)
    governance_log = Column(Text, nullable=True)  # JSON Factsheet
    readiness_score = Column(Float, nullable=True)
    quality_tier = Column(String(10), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="executions")
    parent = relationship("Execution", remote_side=[id], foreign_keys=[parent_execution_id])

    def to_dict(self):
        import json
        history = []
        if self.prompt_history:
            try:
                history = json.loads(self.prompt_history)
            except (json.JSONDecodeError, TypeError):
                history = []

        return {
            "id": self.id,
            "project_id": self.project_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "version": self.version,
            "prompt_history": history,
            "is_active_head": self.is_active_head,
            "parent_execution_id": self.parent_execution_id,
            "prd_path": self.prd_path,
            "plan_path": self.plan_path,
            "request_path": self.request_path,
            "result_path": self.result_path,
            "error_message": self.error_message,
            "tokens_used": self.tokens_used,
            "estimated_cost": self.estimated_cost,
            "credits_used": self.credits_used,
            "duration_seconds": self.duration_seconds,
            "model_used": self.model_used,
            "governance_log": json.loads(self.governance_log) if self.governance_log else None,
            "readiness_score": self.readiness_score,
            "quality_tier": self.quality_tier,
        }


def get_next_version(session, project_id: int) -> int:
    from sqlalchemy import func
    result = session.query(func.max(Execution.version)).filter(
        Execution.project_id == project_id
    ).scalar()
    return (result or 0) + 1


# Database setup
REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "ai-dev-team.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Initialize database tables. Safe to call multiple times."""
    Base.metadata.create_all(engine)
    # Lightweight migration: add locked_ui_archetype column if missing
    try:
        with engine.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(projects)")).fetchall()]
            if "locked_ui_archetype" not in cols:
                conn.execute(text("ALTER TABLE projects ADD COLUMN locked_ui_archetype VARCHAR(50)"))
                conn.commit()
    except Exception as e:
        print(f"Warning: could not ensure locked_ui_archetype column: {e}")
    # Lightweight migration: add build metrics columns if missing
    try:
        with engine.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(executions)")).fetchall()]
            for col_name, col_type in [
                ("tokens_used", "INTEGER"),
                ("estimated_cost", "REAL"),
                ("credits_used", "INTEGER"),
                ("duration_seconds", "REAL"),
                ("model_used", "VARCHAR(100)"),
                ("governance_log", "TEXT"),
                ("readiness_score", "REAL"),
                ("quality_tier", "VARCHAR(10)"),
            ]:
                if col_name not in cols:
                    conn.execute(text(f"ALTER TABLE executions ADD COLUMN {col_name} {col_type}"))
            conn.commit()
    except Exception as e:
        print(f"Warning: could not ensure build metrics columns: {e}")
    # Migration: add auth columns to users table if missing
    try:
        with engine.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()]
            for col_name, col_type in [
                ("password_hash", "VARCHAR(255)"),
                ("reset_token", "VARCHAR(255)"),
                ("reset_token_expires", "DATETIME"),
            ]:
                if col_name not in cols:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
            conn.commit()
    except Exception as e:
        print(f"Warning: could not ensure auth columns: {e}")
    print(f"Database initialized at: {DB_PATH}")


def get_session():
    """Get a new database session. Remember to close it after use!"""
    return SessionLocal()

