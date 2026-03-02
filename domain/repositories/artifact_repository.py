from abc import ABC, abstractmethod
from typing import List
from domain.entities.artifact import Artifact


class ArtifactRepository(ABC):

    @abstractmethod
    async def save(self, artifact: Artifact) -> None:
        pass

    @abstractmethod
    async def get_by_execution_id(
        self,
        execution_id: str,
    ) -> List[Artifact]:
        pass