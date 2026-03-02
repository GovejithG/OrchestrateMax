from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid
from typing import Optional


class ArtifactType(str, Enum):
    TEXT = "TEXT"
    JSON = "JSON"


@dataclass
class Artifact:
    id: str
    execution_id: str
    name: str
    artifact_type: ArtifactType
    content: str
    created_at: datetime

    @staticmethod
    def create(
        execution_id: str,
        name: str,
        artifact_type: ArtifactType,
        content: str,
    ) -> "Artifact":
        return Artifact(
            id=str(uuid.uuid4()),
            execution_id=execution_id,
            name=name,
            artifact_type=artifact_type,
            content=content,
            created_at=datetime.utcnow(),
        )