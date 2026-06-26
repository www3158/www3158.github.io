from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.database import get_connection
from app.routers.auth import require_admin
from app.routers.content import ensure_content_tables

router = APIRouter(prefix="/api/admin", tags=["admin"])


class PropertyPayload(BaseModel):
    title: str
    address: str
    region: str
    lawd_cd: Optional[str] = None
    property_type: str = "APT"
    deposit: int
    monthly_rent: Optional[int] = 0
    area_m2: Optional[float] = None
    floor: Optional[int] = None
    maintenance_fee: Optional[int] = 0
    station_distance_min: Optional[int] = None
    move_in_date: Optional[str] = None
    risk_level: Optional[str] = "확인"
    risk_tags: Optional[str] = None
    image_url: Optional[str] = None


class InquiryUpdate(BaseModel):
    status: str = "확인중"
    answer: Optional[str] = None


class ChecklistPayload(BaseModel):
    title: str
    description: str
    category: str = "기본"
    sort_order: int = 0
    active: bool = True


PROPERTY_COLUMNS = """
    id, external_property_id, title, address, region, lawd_cd, property_type,
    deposit, monthly_rent, area_m2, floor, maintenance_fee, station_distance_min,
    move_in_date, risk_level, risk_tags, image_url
"""


def ensure_property_columns(cur):
    cur.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS image_url TEXT")


def property_params(payload: PropertyPayload):
    return (
        payload.title.strip(),
        payload.address.strip(),
        payload.region.strip(),
        payload.lawd_cd,
        payload.property_type,
        payload.deposit,
        payload.monthly_rent,
        payload.area_m2,
        payload.floor,
        payload.maintenance_fee,
        payload.station_distance_min,
        payload.move_in_date,
        payload.risk_level,
        payload.risk_tags,
        payload.image_url,
    )


@router.get("/summary")
def summary(authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    ensure_content_tables()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS count FROM properties")
            property_count = cur.fetchone()["count"]
            cur.execute("SELECT COUNT(*) AS count FROM app_inquiries WHERE status <> '완료'")
            inquiry_count = cur.fetchone()["count"]
            cur.execute("SELECT COUNT(*) AS count FROM app_checklist_items WHERE active = TRUE")
            checklist_count = cur.fetchone()["count"]
    return {
        "property_count": property_count,
        "pending_inquiry_count": inquiry_count,
        "checklist_count": checklist_count,
    }


@router.get("/properties")
def list_properties(authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    with get_connection() as conn:
        with conn.cursor() as cur:
            ensure_property_columns(cur)
            cur.execute(f"SELECT {PROPERTY_COLUMNS} FROM properties ORDER BY id DESC LIMIT 200")
            rows = cur.fetchall()
    return {"count": len(rows), "items": rows}


@router.post("/properties")
def create_property(payload: PropertyPayload, authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    if not payload.title.strip() or not payload.address.strip() or not payload.region.strip():
        raise HTTPException(status_code=400, detail="매물명, 주소, 지역은 필수입니다.")
    with get_connection() as conn:
        with conn.cursor() as cur:
            ensure_property_columns(cur)
            cur.execute(
                """
                INSERT INTO properties (
                    external_property_id, title, address, region, lawd_cd, property_type,
                    deposit, monthly_rent, area_m2, floor, maintenance_fee, station_distance_min,
                    move_in_date, risk_level, risk_tags, image_url
                )
                VALUES (
                    'ADMIN-' || REPLACE(EXTRACT(EPOCH FROM CLOCK_TIMESTAMP())::TEXT, '.', ''),
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
                """,
                property_params(payload),
            )
            row = cur.fetchone()
        conn.commit()
    return {"id": row["id"], "message": "매물이 등록되었습니다."}


@router.put("/properties/{property_id}")
def update_property(property_id: int, payload: PropertyPayload, authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    with get_connection() as conn:
        with conn.cursor() as cur:
            ensure_property_columns(cur)
            cur.execute(
                """
                UPDATE properties SET
                    title = %s,
                    address = %s,
                    region = %s,
                    lawd_cd = %s,
                    property_type = %s,
                    deposit = %s,
                    monthly_rent = %s,
                    area_m2 = %s,
                    floor = %s,
                    maintenance_fee = %s,
                    station_distance_min = %s,
                    move_in_date = %s,
                    risk_level = %s,
                    risk_tags = %s,
                    image_url = %s
                WHERE id = %s
                RETURNING id
                """,
                (*property_params(payload), property_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="매물을 찾을 수 없습니다.")
        conn.commit()
    return {"message": "매물이 수정되었습니다."}


@router.delete("/properties/{property_id}")
def delete_property(property_id: int, authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM properties WHERE id = %s RETURNING id", (property_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="매물을 찾을 수 없습니다.")
        conn.commit()
    return {"message": "매물이 삭제되었습니다."}


@router.get("/inquiries")
def list_inquiries(authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    ensure_content_tables()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, phone, inquiry_type, message, status, answer, created_at, updated_at
                FROM app_inquiries
                ORDER BY id DESC
                LIMIT 200
                """
            )
            rows = cur.fetchall()
    return {"count": len(rows), "items": rows}


@router.put("/inquiries/{inquiry_id}")
def update_inquiry(inquiry_id: int, payload: InquiryUpdate, authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    ensure_content_tables()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE app_inquiries
                SET status = %s, answer = %s, updated_at = NOW()
                WHERE id = %s
                RETURNING id
                """,
                (payload.status, payload.answer, inquiry_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="문의를 찾을 수 없습니다.")
        conn.commit()
    return {"message": "문의가 수정되었습니다."}


@router.get("/checklist")
def list_checklist(authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    ensure_content_tables()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description, category, sort_order, active
                FROM app_checklist_items
                ORDER BY sort_order, id
                """
            )
            rows = cur.fetchall()
    return {"count": len(rows), "items": rows}


@router.post("/checklist")
def create_checklist_item(payload: ChecklistPayload, authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    ensure_content_tables()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_checklist_items (title, description, category, sort_order, active)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (payload.title.strip(), payload.description.strip(), payload.category, payload.sort_order, payload.active),
            )
            row = cur.fetchone()
        conn.commit()
    return {"id": row["id"], "message": "체크리스트가 등록되었습니다."}


@router.put("/checklist/{item_id}")
def update_checklist_item(item_id: int, payload: ChecklistPayload, authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    ensure_content_tables()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE app_checklist_items
                SET title = %s, description = %s, category = %s, sort_order = %s, active = %s, updated_at = NOW()
                WHERE id = %s
                RETURNING id
                """,
                (payload.title.strip(), payload.description.strip(), payload.category, payload.sort_order, payload.active, item_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="체크리스트를 찾을 수 없습니다.")
        conn.commit()
    return {"message": "체크리스트가 수정되었습니다."}


@router.delete("/checklist/{item_id}")
def delete_checklist_item(item_id: int, authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    ensure_content_tables()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM app_checklist_items WHERE id = %s RETURNING id", (item_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="체크리스트를 찾을 수 없습니다.")
        conn.commit()
    return {"message": "체크리스트가 삭제되었습니다."}
