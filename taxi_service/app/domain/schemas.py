from dataclasses import dataclass
from uuid import UUID


@dataclass
class TaxiState:
    public_id: UUID
    x: int
    y: int
