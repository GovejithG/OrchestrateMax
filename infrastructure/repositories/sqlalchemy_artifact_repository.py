from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from domain.entities.artifact import Artifact, ArtifactType
from domain.repositories.artifact_repository import ArtifactRepository

from infrastructure.database.artifact_model import ArtifactModel


class SQLAlchemyArtifactRepository(ArtifactRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, artifact: Artifact) -> None:

        model = ArtifactModel(
            id=artifact.id,
            execution_id=artifact.execution_id,
            name=artifact.name,
            artifact_type=artifact.artifact_type.value,
            content=artifact.content,
            created_at=artifact.created_at,
        )

        self.db.add(model)
        await self.db.commit()

    async def get_by_execution_id(
        self,
        execution_id: str,
    ) -> List[Artifact]:

        result = await self.db.execute(
            select(ArtifactModel).where(
                ArtifactModel.execution_id == execution_id
            )
        )

        models = result.scalars().all()

        return [
            Artifact(
                id=m.id,
                execution_id=m.execution_id,
                name=m.name,
                artifact_type=ArtifactType(m.artifact_type),
                content=m.content,
                created_at=m.created_at,
            )
            for m in models
        ]