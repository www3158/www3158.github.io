from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


ExperienceLevel = Literal["none", "some", "experienced"]
DeliveryPlan = Literal["try", "part_time", "long_term"]
Priority = Literal["cost", "popularity", "maintenance", "long_term", "beginner_safety"]
AreaType = Literal["flat", "hills", "long_distance"]
BodyPreference = Literal["light", "none"]
ModelPreference = Literal["popular", "pcx_alternative", "sporty", "cost", "none"]


class MotorcycleModel(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    base_price: int
    setup_price: int
    market_share: int
    beginner_score: int
    cost_score: int
    long_term_score: int
    popularity_score: int
    maintenance_score: int
    description: str
    pros: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    cons: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    recommended_for: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    caution: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))


class GuideContent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    category: str
    title: str
    content: str
    beginner_level: str = "beginner"
    sort_order: int


class RiderProfile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    budget: int
    experience_level: str
    delivery_plan: str
    daily_hours: int
    used_ok: bool
    priority: str
    area_type: str
    body_preference: str = "none"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RecommendationResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    rider_profile_id: int
    top_model: str
    second_model: str
    score_detail: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    reason: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    caution: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RecommendationRequest(BaseModel):
    budget: int = PydanticField(ge=0)
    experience_level: ExperienceLevel
    delivery_plan: DeliveryPlan
    daily_hours: int = PydanticField(ge=1, le=16)
    used_ok: bool = False
    priority: Priority
    area_type: AreaType
    body_preference: BodyPreference = "none"
    model_preference: ModelPreference = "none"


class PriceGuidance(BaseModel):
    summary: str
    affordable_years: str
    bands: list[str]


class ModelScore(BaseModel):
    model_id: str
    name: str
    setup_price: int
    total_score: float
    score_detail: dict[str, float]
    reasons: list[str]
    cautions: list[str]
    price_guidance: PriceGuidance | None = None


class RecommendationResponse(BaseModel):
    top_model: ModelScore
    second_model: ModelScore
    checklist: list[str]
    beginner_guide: list[str]
    result_id: int | None = None


class ChatRequest(BaseModel):
    message: str = PydanticField(min_length=1, max_length=500)


class ChatResponse(BaseModel):
    answer: str
    matched_title: str | None = None
    category: str | None = None
    confidence: float = 0
    related_questions: list[str] = []
