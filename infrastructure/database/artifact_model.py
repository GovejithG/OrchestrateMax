from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from infrastructure.database.session import Base


class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True, index=True)
    execution_id = Column(
        String,
        ForeignKey("executions.id"),
        nullable=False,
        index=True,
    )

    name = Column(String, nullable=False)
    artifact_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    execution = relationship("ExecutionModel")