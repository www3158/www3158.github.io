from app.models import ModelScore, MotorcycleModel, PriceGuidance, RecommendationRequest
from app.price_models import MotorcyclePriceBand


CHECKLIST = [
    "시동이 한 번에 걸리는지 확인",
    "공회전과 엔진 소음 확인",
    "브레이크 앞/뒤 밀림 확인",
    "타이어 마모와 공기압 확인",
    "사고/전도 흔적 확인",
    "등록서류와 보험 가입 가능 여부 확인",
]

BEGINNER_GUIDE = [
    "면허와 보험 조건을 먼저 확인하세요.",
    "처음 한 달은 장시간 운행보다 짧게 적응하는 것이 좋습니다.",
    "구매 직후 엔진오일, 타이어, 브레이크 상태를 점검하세요.",
]


def recommend(
    profile: RecommendationRequest,
    models: list[MotorcycleModel],
    price_bands: list[MotorcyclePriceBand] | None = None,
) -> list[ModelScore]:
    bands_by_model = _group_price_bands(price_bands or [])
    return sorted(
        (_score_model(profile, model, bands_by_model.get(model.id, [])) for model in models),
        key=lambda item: item.total_score,
        reverse=True,
    )


def _score_model(profile: RecommendationRequest, model: MotorcycleModel, price_bands: list[MotorcyclePriceBand]) -> ModelScore:
    budget = _budget_score(profile.budget, model.setup_price)
    beginner = model.beginner_score * 0.25
    long_term = _long_term_score(profile, model)
    popularity = model.popularity_score * 0.15
    maintenance = model.maintenance_score * 0.10
    priority = _priority_bonus(profile, model)
    area = _area_bonus(profile, model)
    fit = _fit_bonus(profile, model)
    experience = _experience_bonus(profile, model)
    availability = _availability_penalty(profile, model)

    detail = {
        "budget": round(budget, 1),
        "beginner": round(beginner, 1),
        "long_term": round(long_term, 1),
        "popularity": round(popularity, 1),
        "maintenance": round(maintenance, 1),
        "priority_bonus": round(priority, 1),
        "area_bonus": round(area, 1),
        "fit_bonus": round(fit, 1),
        "experience_bonus": round(experience, 1),
        "availability_penalty": round(availability, 1),
    }

    return ModelScore(
        model_id=model.id,
        name=model.name,
        setup_price=model.setup_price,
        total_score=round(sum(detail.values()), 1),
        score_detail=detail,
        reasons=_reasons(profile, model),
        cautions=model.caution,
        price_guidance=_price_guidance(profile, price_bands),
    )


def _group_price_bands(price_bands: list[MotorcyclePriceBand]) -> dict[str, list[MotorcyclePriceBand]]:
    groups: dict[str, list[MotorcyclePriceBand]] = {}
    for band in price_bands:
        groups.setdefault(band.model_id, []).append(band)
    for bands in groups.values():
        bands.sort(key=lambda item: (item.year, item.price_max), reverse=True)
    return groups


def _price_guidance(profile: RecommendationRequest, price_bands: list[MotorcyclePriceBand]) -> PriceGuidance:
    candidates = price_bands if profile.used_ok else [band for band in price_bands if band.condition_type == "신차/재고"]
    possible = [band for band in candidates if band.price_min <= profile.budget]
    stable = [band for band in possible if band.price_max <= profile.budget]

    if not possible:
        cheapest = min(candidates, key=lambda item: item.price_min, default=None)
        if not cheapest:
            return PriceGuidance(summary="연식별 가격 데이터가 아직 없습니다.", affordable_years="-", bands=[])
        return PriceGuidance(
            summary=f"현재 예산으로는 가장 낮은 구간도 약 {cheapest.price_min}만 원부터라 예산 증액이 필요합니다.",
            affordable_years="-",
            bands=[],
        )

    years = sorted({band.year for band in possible})
    year_text = f"{years[0]}년식" if len(years) == 1 else f"{years[0]}~{years[-1]}년식"
    stable_note = "안정권" if stable else "하한가 매물 기준"
    bands = [
        f"{band.year}년식 {band.condition_type}: {band.price_min}~{band.price_max}만 원"
        for band in possible[:3]
    ]

    return PriceGuidance(
        summary=f"예산 {profile.budget}만 원 기준 {year_text} 후보가 가능합니다. ({stable_note})",
        affordable_years=year_text,
        bands=bands,
    )


def _budget_score(budget: int, setup_price: int) -> float:
    if setup_price <= budget:
        return 35
    over = setup_price - budget
    if over <= 50:
        return 24
    if over <= 100:
        return 12
    return 0


def _fit_bonus(profile: RecommendationRequest, model: MotorcycleModel) -> float:
    score = 0.0

    if profile.budget <= 300:
        score += 18 if model.id == "vf100r" else -8
    elif profile.budget <= 450:
        score += 12 if model.id in {"vf100r", "uhr"} else -5
    elif profile.budget <= 500:
        score += 12 if model.id in {"uhr", "pcx", "nmax"} else -8
    else:
        score += 14 if model.id in {"pcx", "nmax"} else -12

    if model.setup_price > profile.budget:
        over = model.setup_price - profile.budget
        if profile.used_ok:
            score -= 4 if over <= 50 else 10
        else:
            score -= 18 if over <= 50 else 28

    if profile.delivery_plan == "long_term":
        score += 18 if model.id in {"pcx", "nmax"} else -14 if model.id == "vf100r" else 4
    elif profile.delivery_plan == "part_time":
        score += 8 if model.id in {"uhr", "pcx", "nmax"} else 0
    elif profile.delivery_plan == "try":
        score += 12 if model.id == "vf100r" else 2 if model.id == "uhr" else -4

    if profile.daily_hours >= 7:
        score += 14 if model.id in {"pcx", "nmax"} else -10 if model.id == "vf100r" else 2

    if profile.model_preference == "popular":
        score += 10 if model.id == "pcx" else 4 if model.id == "nmax" else 0
    elif profile.model_preference == "pcx_alternative":
        score += 20 if model.id == "nmax" else -8 if model.id == "pcx" else 0
    elif profile.model_preference == "sporty":
        score += 18 if model.id == "nmax" else 4 if model.id == "pcx" else 0
    elif profile.model_preference == "cost":
        score += 10 if model.id == "vf100r" else 7 if model.id == "uhr" else 0

    return score


def _availability_penalty(profile: RecommendationRequest, model: MotorcycleModel) -> float:
    if profile.used_ok or model.setup_price <= profile.budget:
        return 0
    over = model.setup_price - profile.budget
    if over <= 50:
        return -35
    if over <= 100:
        return -50
    return -80


def _experience_bonus(profile: RecommendationRequest, model: MotorcycleModel) -> float:
    if profile.experience_level == "none":
        if model.id in {"pcx", "nmax"}:
            return 8
        if model.id == "uhr":
            return 6
        return 2
    if profile.experience_level == "some":
        if model.id in {"pcx", "nmax", "uhr"}:
            return 6
        return 0
    if profile.experience_level == "experienced":
        if model.id in {"pcx", "nmax"}:
            return 8
        if model.id == "uhr":
            return 4
        return -4
    return 0


def _long_term_score(profile: RecommendationRequest, model: MotorcycleModel) -> float:
    score = model.long_term_score * 0.15
    if profile.delivery_plan == "long_term":
        return score
    if profile.delivery_plan == "part_time":
        return score * 0.75
    return score * 0.45


def _priority_bonus(profile: RecommendationRequest, model: MotorcycleModel) -> float:
    if profile.priority == "cost":
        return 14 if model.id == "vf100r" else 10 if model.id == "uhr" else 2
    if profile.priority == "popularity":
        return 16 if model.id == "pcx" else 10 if model.id == "nmax" else 4 if model.id == "uhr" else 0
    if profile.priority == "maintenance":
        return 14 if model.id == "pcx" else 12 if model.id == "nmax" else 7 if model.id == "uhr" else 3
    if profile.priority == "long_term":
        return 16 if model.id == "pcx" else 14 if model.id == "nmax" else 7 if model.id == "uhr" else -4
    return 12 if model.id in {"pcx", "nmax", "uhr"} else 4


def _area_bonus(profile: RecommendationRequest, model: MotorcycleModel) -> float:
    if profile.area_type == "long_distance" or profile.daily_hours >= 7:
        return 6 if model.id in {"pcx", "nmax"} else 2
    if profile.area_type == "hills":
        return 4 if model.id in {"pcx", "nmax", "uhr"} else 1
    if profile.body_preference == "light":
        return 4 if model.id == "vf100r" else 1
    return 0


def _reasons(profile: RecommendationRequest, model: MotorcycleModel) -> list[str]:
    reasons = []
    if model.setup_price <= profile.budget:
        reasons.append(f"예산 {profile.budget}만 원 안에서 세팅 포함 예상가를 맞출 수 있습니다.")
    else:
        reasons.append(f"예산보다 약 {model.setup_price - profile.budget}만 원 높지만 비교 후보로 볼 수 있습니다.")

    if profile.delivery_plan == "long_term" and model.id in {"pcx", "nmax"}:
        reasons.append("장기 운행을 생각할 때 대중성과 정비 접근성이 좋습니다.")
    elif profile.delivery_plan == "try" and model.id == "vf100r":
        reasons.append("배달을 먼저 경험해보기 위한 저예산 입문용으로 적합합니다.")

    if profile.priority == "cost" and model.cost_score >= 90:
        reasons.append("초기 비용 부담을 낮추는 데 유리합니다.")
    if profile.priority == "popularity" and model.id in {"pcx", "nmax"}:
        reasons.append("주변 사례와 정보가 많은 대중적인 모델입니다.")
    if profile.model_preference == "pcx_alternative" and model.id == "nmax":
        reasons.append("PCX와 같은 급에서 다른 선택지를 원하는 경우 NMAX가 좋은 대안입니다.")
    if profile.model_preference == "sporty" and model.id == "nmax":
        reasons.append("스쿠터급 안에서 조금 더 스포티한 주행 성향을 원하는 조건에 맞습니다.")
    if not reasons:
        reasons.extend(model.recommended_for[:2])

    return reasons
