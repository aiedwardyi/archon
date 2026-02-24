"""
Database models for AI Dev Team system.

Tables:
- Project: Named projects that group related executions
- Execution: Individual task executions linked to projects
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from pathlib import Path

# Base class for all models
Base = declarative_base()


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
    
    # Relationship: one project has many executions
    executions = relationship("Execution", back_populates="project", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to JSON-serializable dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "execution_count": len(self.executions) if self.executions else 0,
        }


class Execution(Base):
    """
    Represents a single versioned execution (pipeline run) within a project.
    
    Each execution is a complete snapshot — nothing is overwritten.
    Version numbers auto-increment per project (not globally).
    """
    __tablename__ = "executions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # --- Version tracking (Phase 7A) ---
    # version: auto-increments per project (v1, v2, v3...)
    version = Column(Integer, nullable=False, default=1)
    
    # prompt_history: full conversation array as JSON string
    # Format: [{"role": "user", "content": "Build a landing page"}, ...]
    prompt_history = Column(Text, nullable=True)
    
    # is_active_head: True for the "current" version of the project
    # Only one execution per project should have this = True
    is_active_head = Column(Boolean, nullable=False, default=True)
    
    # parent_execution_id: points to the previous version (for restore branching)
    # NULL means this is the first version of the project
    parent_execution_id = Column(Integer, ForeignKey("executions.id"), nullable=True)
    
    # Artifact file paths (relative to PUBLIC_DIR)
    prd_path = Column(String(500), nullable=True)
    plan_path = Column(String(500), nullable=True)
    request_path = Column(String(500), nullable=True)
    result_path = Column(String(500), nullable=True)
    
    # Error message if execution failed
    error_message = Column(Text, nullable=True)

    # Publish slug (Phase 8.1) -- set when this version is published
    published_slug = Column(String(100), nullable=True)
    
    # Relationship: many executions belong to one project
    project = relationship("Project", back_populates="executions")
    
    # Self-referential relationship: parent version
    parent = relationship("Execution", remote_side=[id], foreign_keys=[parent_execution_id])
    
    def to_dict(self):
        """Convert to JSON-serializable dictionary."""
        import json
        # Parse prompt_history from JSON string back to list
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
        }


def get_next_version(session, project_id: int) -> int:
    """
    Get the next version number for a project.
    
    Finds the highest existing version for this project and returns +1.
    If no executions exist yet, returns 1.
    
    Example: project has v1, v2, v3 → returns 4
    """
    from sqlalchemy import func
    result = session.query(func.max(Execution.version)).filter(
        Execution.project_id == project_id
    ).scalar()
    return (result or 0) + 1


# Database setup
REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "ai-dev-team.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine (connects to database)
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory (used to interact with database)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Initialize database tables. Safe to call multiple times."""
    Base.metadata.create_all(engine)
    print(f"Database initialized at: {DB_PATH}")


def get_session():
    """Get a new database session. Remember to close it after use!"""
    return SessionLocal()

