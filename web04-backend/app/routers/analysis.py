from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from app.database import get_connection
from app.routers.auth import current_user_id, ensure_tables

router = APIRouter(prefix="/api/properties", tags=["analysis"])

REVIEW_RISK_KEYWORDS = (
    "허위매물", "계약 강요", "강요", "수수료", "연락두절", "설명 다름",
    "보증금", "불친절", "말 바꿈", "압박", "환불", "분쟁"
)


def review_judgement(review_count, avg_rating, negative_count, low_rating_count):
    if not review_count:
        return "리뷰 없음"
    if avg_rating < 3.5 or negative_count >= 3 or low_rating_count >= 2:
        return "리뷰 기반 주의"
    if avg_rating < 4.2 or negative_count:
        return "추가 확인 필요"
    return "참고 양호"


def attach_review_summary(real_estates, reviews):
    grouped = {item["id"]: [] for item in real_estates}
    for review in reviews:
        grouped.setdefault(review["office_id"], []).append(review)

    for item in real_estates:
        office_reviews = grouped.get(item["id"], [])
        ratings = [r["rating"] for r in office_reviews if r["rating"]]
        texts = [r["content"] or "" for r in office_reviews]
        sample_count = sum(1 for r in office_reviews if r["source"] == "sample")
        negative_count = sum(1 for text in texts for keyword in REVIEW_RISK_KEYWORDS if keyword in text)
        low_rating_count = sum(1 for rating in ratings if rating <= 2)
        review_count = len(office_reviews)
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0

        if review_count:
            item["review_count"] = review_count
            item["avg_rating"] = avg_rating
            item["negative_keyword_count"] = negative_count
        item["review_judgement"] = review_judgement(review_count, avg_rating, negative_count, low_rating_count)
        item["review_risk_keywords"] = negative_count
        item["review_low_rating_count"] = low_rating_count
        item["review_sample_count"] = sample_count
        item["review_source_label"] = "예시 리뷰" if review_count and sample_count == review_count else "실제 리뷰"
        item["review_evidence"] = [text[:80] for text in texts if text][:2]
        item["review_items"] = [
            {"rating": review["rating"], "content": (review["content"] or "")[:80]}
            for review in office_reviews
            if review["content"]
        ][:2]


@router.get("/{property_id}/analysis")
def analyze_property(property_id: int, authorization: Optional[str] = Header(default=None)):
    ensure_tables()
    current_user_id(authorization)
    sql = """
        SELECT
            p.id,
            p.title,
            p.address,
            p.region,
            p.property_type,
            p.deposit,
            p.risk_level,
            p.risk_tags,
            s.sample_count AS market_sample_count,
            s.avg_deposit_won AS market_avg_deposit_won,
            s.median_deposit_won AS market_median_deposit_won,
            s.min_deposit_won AS market_min_deposit_won,
            s.max_deposit_won AS market_max_deposit_won,
            s.min_contract_date AS market_min_contract_date,
            s.max_contract_date AS market_max_contract_date,
            r.risk_score,
            r.has_mortgage,
            r.has_seizure,
            r.has_provisional_seizure,
            r.has_trust,
            r.has_leasehold_registration,
            r.owner_matched,
            r.insurance_checked,
            r.senior_tenant_checked,
            r.building_register_checked,
            r.broker_status_checked,
            r.registry_checked_before_balance
        FROM properties p
        LEFT JOIN property_risk_checks r
            ON p.id = r.property_id
        LEFT JOIN rent_market_stats s
            ON s.address_region = p.region
           AND s.property_type = p.property_type
        WHERE p.id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (property_id,))
            row = cur.fetchone()
            cur.execute(
                """
                SELECT
                    o.id,
                    o.name,
                    o.address,
                    o.registration_no,
                    o.business_status,
                    o.mutual_aid_checked,
                    o.registration_no_verified,
                    o.phone,
                    o.source_url,
                    o.image_url,
                    o.review_count,
                    o.avg_rating,
                    o.recent_review_days,
                    o.negative_keyword_count,
                    o.trust_score,
                    o.trust_level,
                    (o.registration_no LIKE 'RE-%%') AS is_sample,
                    n.distance_m
                FROM property_nearby_real_estates n
                JOIN real_estate_offices o ON o.id = n.office_id
                WHERE n.property_id = %s
                ORDER BY o.trust_score DESC, n.distance_m ASC
                LIMIT 3
                """,
                (property_id,),
            )
            real_estates = cur.fetchall()
            office_ids = [item["id"] for item in real_estates]
            reviews = []
            if office_ids:
                cur.execute(
                    """
                    SELECT office_id, rating, content, source, reviewed_at
                    FROM real_estate_office_reviews
                    WHERE office_id = ANY(%s)
                    ORDER BY reviewed_at DESC NULLS LAST, id DESC
                    """,
                    (office_ids,),
                )
                reviews = cur.fetchall()
            attach_review_summary(real_estates, reviews)

    if row is None:
        raise HTTPException(status_code=404, detail="매물을 찾을 수 없습니다.")

    risk_reasons = []
    questions_to_broker = []
    special_clause_examples = []

    if row["has_mortgage"]:
        risk_reasons.append("근저당이 있어 선순위 권리와 채권최고액 확인이 필요합니다.")
        questions_to_broker.append("근저당 채권최고액은 얼마인가요?")
        special_clause_examples.append("잔금 전까지 근저당 말소가 완료되지 않을 경우 계약을 해제할 수 있다.")

    if row["has_seizure"]:
        risk_reasons.append("압류가 확인되어 보증금 반환 위험이 높습니다.")
        questions_to_broker.append("압류가 발생한 사유와 해제 예정일을 확인할 수 있나요?")
        special_clause_examples.append("압류 해제가 확인되지 않을 경우 계약은 무효로 한다.")

    if row["has_provisional_seizure"]:
        risk_reasons.append("가압류가 확인되어 권리관계 확인이 필요합니다.")
        questions_to_broker.append("가압류 해제 가능 여부와 관련 서류를 확인할 수 있나요?")

    if row["has_trust"]:
        risk_reasons.append("신탁등기가 있어 임대 권한 확인이 반드시 필요합니다.")
        questions_to_broker.append("신탁회사 동의서 또는 임대 권한 증빙을 확인할 수 있나요?")
        special_clause_examples.append("신탁회사의 임대차 동의가 확인되지 않을 경우 계약을 진행하지 않는다.")

    if row["has_leasehold_registration"]:
        risk_reasons.append("임차권등기명령 이력이 있어 이전 임차인의 보증금 반환 문제가 있었을 가능성이 있습니다.")
        questions_to_broker.append("임차권등기명령 발생 사유와 말소 여부를 확인할 수 있나요?")

    if row["owner_matched"] is False:
        risk_reasons.append("소유자와 계약자가 일치하지 않아 대리계약 위험이 있습니다.")
        questions_to_broker.append("소유자의 위임장과 인감증명서를 확인할 수 있나요?")

    if row["insurance_checked"] is False:
        risk_reasons.append("전세보증금반환보증 가입 가능 여부가 확인되지 않았습니다.")
        questions_to_broker.append("HUG 전세보증금반환보증 가입이 가능한 매물인가요?")

    if row["senior_tenant_checked"] is False:
        risk_reasons.append("선순위 임차인 정보가 확인되지 않았습니다.")
        questions_to_broker.append("선순위 임차인의 보증금 총액을 확인할 수 있나요?")

    if row["building_register_checked"] is False:
        risk_reasons.append("건축물대장 확인이 필요합니다.")
        questions_to_broker.append("건축물대장상 용도와 실제 사용 용도가 일치하나요?")

    if row["broker_status_checked"] is False:
        risk_reasons.append("중개업소 영업 상태 확인이 필요합니다.")
        questions_to_broker.append("공인중개사 등록번호와 보증보험 가입 여부를 확인할 수 있나요?")

    if row["registry_checked_before_balance"] is False:
        risk_reasons.append("잔금 전 등기부등본 재확인이 필요합니다.")
        questions_to_broker.append("잔금 당일 최신 등기부등본을 다시 확인할 수 있나요?")
        special_clause_examples.append("잔금일 등기부등본상 새로운 권리침해가 확인될 경우 계약을 해제할 수 있다.")

    if not risk_reasons:
        risk_reasons.append("현재 데이터 기준으로 큰 위험 요소는 확인되지 않았습니다.")
        questions_to_broker.append("계약 전 최신 등기부등본과 건축물대장을 다시 확인할 수 있나요?")

    if row["risk_score"] >= 80:
        summary = "이 매물은 전세사기 위험 요소가 많이 확인되어 신중한 검토가 필요합니다."
    elif row["risk_score"] >= 30:
        summary = "이 매물은 일부 위험 요소가 있어 계약 전 추가 확인이 필요합니다."
    else:
        summary = "이 매물은 현재 데이터 기준으로 큰 위험 요소가 제한적으로 확인됩니다. 계약 전 최신 서류 확인은 필요합니다."

    market_stats = None
    market_comment = "같은 지역과 주택유형의 전세 거래 비교 데이터가 부족합니다."
    median_deposit = row["market_median_deposit_won"]
    if median_deposit:
        pct = round((row["deposit"] / median_deposit) * 100, 1)
        market_stats = {
            "sample_count": row["market_sample_count"],
            "avg_deposit_won": row["market_avg_deposit_won"],
            "median_deposit_won": median_deposit,
            "min_deposit_won": row["market_min_deposit_won"],
            "max_deposit_won": row["market_max_deposit_won"],
            "min_contract_date": row["market_min_contract_date"],
            "max_contract_date": row["market_max_contract_date"],
            "deposit_vs_median_pct": pct,
        }
        market_comment = (
            f"이 매물의 보증금은 같은 지역·유형 중앙값의 {pct}% 수준입니다. "
            "시세 비교는 참고 지표이며 권리관계와 보증보험 가능 여부 확인을 대체하지 않습니다."
        )

    sample_real_estate_count = sum(1 for item in real_estates if item.get("is_sample"))
    if real_estates and sample_real_estate_count == len(real_estates):
        real_estate_comment = (
            "현재 부동산 정보는 실제 등록 데이터 연동 전 예시입니다. 실제 데이터 연동 후 지도 링크와 등록 정보를 제공합니다."
        )
    else:
        real_estate_comment = (
            "검색으로 확인한 실제 상호·주소와 등록·공제·리뷰 참고 정보입니다. 리뷰가 없는 항목은 현장 확인이 필요합니다."
        )

    return {
        "property_id": row["id"],
        "title": row["title"],
        "address": row["address"],
        "region": row["region"],
        "property_type": row["property_type"],
        "deposit": row["deposit"],
        "risk_level": row["risk_level"],
        "risk_score": row["risk_score"],
        "risk_tags": row["risk_tags"],
        "market_stats": market_stats,
        "market_comment": market_comment,
        "nearby_real_estates": real_estates,
        "real_estate_comment": real_estate_comment,
        "summary": summary,
        "risk_reasons": risk_reasons,
        "questions_to_broker": questions_to_broker,
        "special_clause_examples": special_clause_examples
    }
