from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import GuideContent

router = APIRouter(prefix="/guides", tags=["guides"])


@router.get("", response_model=list[GuideContent])
def list_guides(session: Session = Depends(get_session)) -> list[GuideContent]:
    statement = select(GuideContent).order_by(GuideContent.sort_order)
    return list(session.exec(statement).all())

