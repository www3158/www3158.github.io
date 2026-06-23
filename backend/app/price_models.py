from sqlmodel import Field, SQLModel


class MotorcyclePriceBand(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    model_id: str = Field(index=True)
    model_name: str
    year: int = Field(index=True)
    condition_type: str
    price_min: int
    price_max: int
    note: str = ""
    source_type: str = "market_seed"
