from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from app.database import get_connection
from app.routers.auth import current_user_id, ensure_tables

router = APIRouter(prefix="/api/properties", tags=["properties"])


def ensure_property_columns(cur):
    cur.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS image_url TEXT")


@router.get("")
def get_properties(authorization: Optional[str] = Header(default=None)):
    current_user_id(authorization)
    ensure_tables()
    sql = """
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
            r.broker_status_checked
        FROM properties p
        LEFT JOIN property_risk_checks r
            ON p.id = r.property_id
        LEFT JOIN rent_market_stats s
            ON s.address_region = p.region
           AND s.property_type = p.property_type
        ORDER BY p.id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            ensure_property_columns(cur)
            cur.execute(sql)
            rows = cur.fetchall()

    return {
        "count": len(rows),
        "items": rows
    }


@router.get("/{property_id}")
def get_property(property_id: int, authorization: Optional[str] = Header(default=None)):
    current_user_id(authorization)
    ensure_tables()
    sql = """
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
            r.broker_status_checked
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
            ensure_property_columns(cur)
            cur.execute(sql, (property_id,))
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="매물을 찾을 수 없습니다.")

    return row
