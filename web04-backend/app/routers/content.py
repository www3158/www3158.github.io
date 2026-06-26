from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_connection

router = APIRouter(prefix="/api", tags=["content"])


class InquiryRequest(BaseModel):
    name: str
    phone: str
    inquiry_type: str
    message: str


CHECKLIST_DEFAULTS = [
    ("등기부등본 최신본 확인", "계약 당일 기준 소유권, 근저당, 압류 변동 여부를 확인합니다.", "필수", 1),
    ("임대인 신분 확인", "등기부 소유자와 계약 당사자의 이름과 신분증을 대조합니다.", "필수", 2),
    ("보증보험 가능 여부", "HUG, HF, SGI 가입 가능성과 거절 사유를 계약 전에 확인합니다.", "보증", 3),
    ("건축물대장 확인", "위반건축물, 용도, 호수 표시가 실제 임차 공간과 맞는지 봅니다.", "서류", 4),
    ("선순위 보증금 확인", "다가구·빌라는 선순위 임차보증금 총액을 반드시 확인합니다.", "권리", 5),
    ("전입신고·확정일자 계획", "잔금 직후 전입신고와 확정일자를 받을 수 있는 일정을 잡습니다.", "계약", 6),
]


DDL = """
CREATE TABLE IF NOT EXISTS app_inquiries (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    phone VARCHAR(40) NOT NULL,
    inquiry_type VARCHAR(80) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT '대기',
    answer TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_checklist_items (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(40) NOT NULL DEFAULT '기본',
    sort_order INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
"""


def ensure_content_tables():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            cur.execute("SELECT COUNT(*) AS count FROM app_checklist_items")
            if cur.fetchone()["count"] == 0:
                cur.executemany(
                    """
                    INSERT INTO app_checklist_items (title, description, category, sort_order)
                    VALUES (%s, %s, %s, %s)
                    """,
                    CHECKLIST_DEFAULTS,
                )
        conn.commit()


@router.get("/checklist")
def get_checklist():
    ensure_content_tables()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description, category, sort_order, active
                FROM app_checklist_items
                WHERE active = TRUE
                ORDER BY sort_order, id
                """
            )
            rows = cur.fetchall()
    return {"count": len(rows), "items": rows}


@router.post("/inquiries")
def create_inquiry(payload: InquiryRequest):
    ensure_content_tables()
    if not payload.name.strip() or not payload.phone.strip() or not payload.message.strip():
        raise HTTPException(status_code=400, detail="이름, 연락처, 문의 내용을 입력해주세요.")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_inquiries (name, phone, inquiry_type, message)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    payload.name.strip(),
                    payload.phone.strip(),
                    payload.inquiry_type.strip() or "일반 문의",
                    payload.message.strip(),
                ),
            )
            row = cur.fetchone()
        conn.commit()
    return {"id": row["id"], "message": "문의가 접수되었습니다."}
