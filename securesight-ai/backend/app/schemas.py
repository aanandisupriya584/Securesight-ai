from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=8, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AssetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    asset_type: str = Field(min_length=1, max_length=40)
    identifier: str = Field(min_length=1, max_length=255)

class AssetResponse(AssetCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime

class OrganizationResponse(BaseModel):
    id: str
    name: str
    role: str

class AIAnalysisRequest(BaseModel):
    question: str = Field(min_length=4, max_length=4000)

class AIAnalysisResponse(BaseModel):
    answer: str
    provider: str
    model: str
    tools_used: list[str] = Field(default_factory=list)
    notice: str = "AI output is advisory and may include redacted workspace metadata retrieved through read-only tools. Verify evidence before acting."
