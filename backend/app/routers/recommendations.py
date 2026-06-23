from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import MotorcycleModel, RecommendationRequest, RecommendationResponse, RecommendationResult, RiderProfile
from app.price_models import MotorcyclePriceBand
from app.services.recommender import BEGINNER_GUIDE, CHECKLIST, recommend

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.post("", response_model=RecommendationResponse)
def create_recommendation(payload: RecommendationRequest, session: Session = Depends(get_session)) -> RecommendationResponse:
    models = list(session.exec(select(MotorcycleModel)).all())
    if len(models) < 2:
        raise HTTPException(status_code=500, detail="Motorcycle data is not ready.")

    price_bands = list(session.exec(select(MotorcyclePriceBand)).all())
    scores = recommend(payload, models, price_bands)
    profile = RiderProfile(**payload.model_dump(exclude={"model_preference"}))
    session.add(profile)
    session.commit()
    session.refresh(profile)

    result = RecommendationResult(
        rider_profile_id=profile.id or 0,
        top_model=scores[0].model_id,
        second_model=scores[1].model_id,
        score_detail={score.model_id: score.score_detail for score in scores},
        reason=scores[0].reasons,
        caution=scores[0].cautions,
    )
    session.add(result)
    session.commit()
    session.refresh(result)

    return RecommendationResponse(
        top_model=scores[0],
        second_model=scores[1],
        checklist=CHECKLIST,
        beginner_guide=BEGINNER_GUIDE,
        result_id=result.id,
    )
