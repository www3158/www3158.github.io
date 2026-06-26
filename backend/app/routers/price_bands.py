from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.price_models import MotorcyclePriceBand

router = APIRouter(prefix="/price-bands", tags=["price-bands"])


@router.get("", response_model=list[MotorcyclePriceBand])
def list_price_bands(session: Session = Depends(get_session)) -> list[MotorcyclePriceBand]:
    statement = select(MotorcyclePriceBand).order_by(MotorcyclePriceBand.model_id, MotorcyclePriceBand.year.desc())
    return list(session.exec(statement).all())
