from typing import Optional

from fastapi import APIRouter, Header, Query
from app.database import get_connection
from app.routers.auth import current_user_id, ensure_tables

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def ensure_property_columns(cur):
    cur.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS image_url TEXT")


@router.get("")
def get_recommendations(
    region: Optional[str] = Query(default=None, description="지역명 일부 검색 예: 구로구, 부평구, 봉천동"),
    property_type: Optional[str] = Query(default=None, description="APT, VILLA, OFFICETEL, SINGLE_MULTI"),
    max_deposit: Optional[int] = Query(default=None, description="최대 전세보증금"),
    authorization: Optional[str] = Header(default=None),
):
    ensure_tables()
    user_id = current_user_id(authorization)
    if not any([region, property_type, max_deposit]):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT preferred_region, max_deposit, preferred_type
                    FROM app_user_preferences
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                pref = cur.fetchone()
        if pref:
            region = pref["preferred_region"]
            property_type = pref["preferred_type"]
            max_deposit = pref["max_deposit"]

    params = []

    if max_deposit is None:
        budget_score_sql = "70"
    else:
        budget_score_sql = """
            CASE
                WHEN p.deposit <= %s THEN 100
                ELSE 0
            END
        """
        params.append(max_deposit)

    sql = f"""
        SELECT
            p.id,
            p.external_property_id,
            p.title,
            p.address,
            p.region,
            p.lawd_cd,
            p.property_type,
            p.deposit,
            p.monthly_rent,
            p.area_m2,
            p.floor,
            p.maintenance_fee,
            p.station_distance_min,
            p.move_in_date,
            p.risk_level,
            p.risk_tags,
            p.image_url,
            s.sample_count AS market_sample_count,
            s.avg_deposit_won AS market_avg_deposit_won,
            s.median_deposit_won AS market_median_deposit_won,
            CASE
                WHEN s.median_deposit_won IS NULL OR s.median_deposit_won = 0 THEN NULL
                ELSE ROUND((p.deposit::NUMERIC / s.median_deposit_won) * 100, 1)
            END AS deposit_vs_median_pct,
            r.risk_score,
            r.has_mortgage,
            r.has_seizure,
            r.has_provisional_seizure,
            r.has_trust,
            r.has_leasehold_registration,
            r.insurance_checked,
            r.senior_tenant_checked,
            r.building_register_checked,
            r.broker_status_checked,

            GREATEST(0, 100 - COALESCE(r.risk_score, 0)) AS safety_score,

            CASE
                WHEN p.station_distance_min IS NULL THEN 50
                WHEN p.station_distance_min <= 5 THEN 100
                WHEN p.station_distance_min <= 10 THEN 80
                WHEN p.station_distance_min <= 15 THEN 60
                ELSE 40
            END AS transport_score,

            {budget_score_sql} AS budget_score,

            (
                GREATEST(0, 100 - COALESCE(r.risk_score, 0)) * 0.5
                +
                ({budget_score_sql}) * 0.3
                +
                CASE
                    WHEN p.station_distance_min IS NULL THEN 50
                    WHEN p.station_distance_min <= 5 THEN 100
                    WHEN p.station_distance_min <= 10 THEN 80
                    WHEN p.station_distance_min <= 15 THEN 60
                    ELSE 40
                END * 0.2
            )::INTEGER AS final_score

        FROM properties p
        LEFT JOIN property_risk_checks r
            ON p.id = r.property_id
        LEFT JOIN rent_market_stats s
            ON s.address_region = p.region
           AND s.property_type = p.property_type
        WHERE 1 = 1
    """

    if max_deposit is not None:
        params.append(max_deposit)

    if region:
        sql += " AND p.region LIKE %s"
        params.append(f"%{region}%")

    if property_type:
        sql += " AND p.property_type = %s"
        params.append(property_type)

    if max_deposit:
        sql += " AND p.deposit <= %s"
        params.append(max_deposit)

    sql += """
        ORDER BY
            final_score DESC,
            COALESCE(r.risk_score, 0) ASC,
            p.deposit ASC
        LIMIT 10;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            ensure_property_columns(cur)
            cur.execute(sql, params)
            rows = cur.fetchall()

    return {
        "count": len(rows),
        "items": rows
    }
