from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

@dataclass
class Company:
    id: UUID
    name: str
    plan: str
    created_at: datetime

@dataclass
class User:
    id: UUID
    company_id: UUID
    email: str
    hashed_password: str
    role: str
    is_active: bool
    created_at: datetime
