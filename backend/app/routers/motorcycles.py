from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import MotorcycleModel

router = APIRouter(prefix="/motorcycles", tags=["motorcycles"])


@router.get("", response_model=list[MotorcycleModel])
def list_motorcycles(session: Session = Depends(get_session)) -> list[MotorcycleModel]:
    return list(session.exec(select(MotorcycleModel)).all())

