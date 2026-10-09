import time
from sqlalchemy import Column, String, Integer, BigInteger, Text, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class ExecutionSessionModel(Base):
    __tablename__ = "execution_sessions"

    id = Column(String(64), primary_key=True)
    created_at = Column(BigInteger, default=time.time_ns)
    status = Column(String(32), default="active")  # active, completed, diverged
    head_event_id = Column(String(64), nullable=True)
    root_fs_hash = Column(String(64), nullable=True)
    metadata_json = Column(Text, default="{}")

    events = relationship("EventRecordModel", back_populates="session", cascade="all, delete-orphan")

class EventRecordModel(Base):
    __tablename__ = "event_records"

    event_id = Column(String(64), primary_key=True)
    session_id = Column(String(64), ForeignKey("execution_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_event_id = Column(String(64), nullable=True, index=True)
    lamport_clock = Column(Integer, nullable=False, index=True)
    vector_clock_json = Column(Text, default="{}")
    event_type = Column(String(64), nullable=False, index=True)
    actor = Column(String(64), default="agent")
    payload_json = Column(Text, default="{}")
    fs_state_blake3 = Column(String(64), nullable=True)
    timestamp_ns = Column(BigInteger, default=time.time_ns)

    session = relationship("ExecutionSessionModel", back_populates="events")

    __table_args__ = (
        Index("idx_session_lamport", "session_id", "lamport_clock"),
    )

class SnapshotRecordModel(Base):
    __tablename__ = "fs_snapshots"

    root_hash = Column(String(64), primary_key=True)
    manifest_json = Column(Text, nullable=False)
    file_count = Column(Integer, default=0)
    created_at = Column(BigInteger, default=time.time_ns)
