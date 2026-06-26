import base64
import hashlib
import hmac
import json
import os
import secrets
import smtplib
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from app.database import get_connection

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")), override=True)

router = APIRouter(prefix="/api/auth", tags=["auth"])

SECRET = os.getenv("AUTH_SECRET", "jeonse-guard-dev-secret")
TOKEN_TTL_HOURS = 24
SENS_SERVICE_ID = os.getenv("NAVER_SENS_SERVICE_ID")
SENS_ACCESS_KEY = os.getenv("NAVER_SENS_ACCESS_KEY")
SENS_SECRET_KEY = os.getenv("NAVER_SENS_SECRET_KEY")
SENS_FROM_NUMBER = os.getenv("NAVER_SENS_FROM_NUMBER")
GMAIL_SMTP_USER = os.getenv("GMAIL_SMTP_USER")
GMAIL_SMTP_PASSWORD = os.getenv("GMAIL_SMTP_PASSWORD")
GMAIL_FROM_EMAIL = os.getenv("GMAIL_FROM_EMAIL", GMAIL_SMTP_USER)


class PhoneCodeRequest(BaseModel):
    phone: str


class EmailCodeRequest(BaseModel):
    email: str


class VerifyPhoneRequest(BaseModel):
    phone: str
    code: str


class VerifyEmailRequest(BaseModel):
    email: str
    code: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    email: str
    phone: Optional[str] = None
    preferred_region: Optional[str] = None
    max_deposit: Optional[int] = None
    preferred_type: Optional[str] = None
    move_in_month: Optional[str] = None
    priority: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class FindIdRequest(BaseModel):
    phone: str


class ResetPasswordRequest(BaseModel):
    username: str
    phone: str
    code: str
    new_password: str


class PreferenceRequest(BaseModel):
    preferred_region: Optional[str] = None
    max_deposit: Optional[int] = None
    preferred_type: Optional[str] = None
    move_in_month: Optional[str] = None
    priority: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


DDL = """
CREATE TABLE IF NOT EXISTS app_users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name VARCHAR(80) NOT NULL,
    phone VARCHAR(30) UNIQUE,
    email VARCHAR(160) UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'MEMBER',
    phone_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_phone_verifications (
    id BIGSERIAL PRIMARY KEY,
    phone VARCHAR(30) NOT NULL,
    code VARCHAR(12) NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_email_verifications (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(160) NOT NULL,
    code VARCHAR(12) NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_user_preferences (
    user_id BIGINT PRIMARY KEY REFERENCES app_users(id) ON DELETE CASCADE,
    preferred_region TEXT,
    max_deposit BIGINT,
    preferred_type VARCHAR(20),
    move_in_month VARCHAR(7),
    priority VARCHAR(20),
    updated_at TIMESTAMP DEFAULT NOW()
);
"""


def ensure_tables():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            cur.execute("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'MEMBER'")
            cur.execute("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS email VARCHAR(160)")
            cur.execute("ALTER TABLE app_users ALTER COLUMN phone DROP NOT NULL")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS app_users_email_idx ON app_users(email) WHERE email IS NOT NULL")
            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin1234!")
            if admin_username and admin_password:
                admin_phone = normalize_phone(os.getenv("ADMIN_PHONE", "01000000000"))
                cur.execute("SELECT id FROM app_users WHERE username = %s", (admin_username,))
                if cur.fetchone():
                    cur.execute("UPDATE app_users SET role = 'ADMIN', updated_at = NOW() WHERE username = %s", (admin_username,))
                else:
                    cur.execute(
                        """
                        INSERT INTO app_users (username, password_hash, name, phone, role, phone_verified)
                        VALUES (%s, %s, %s, %s, 'ADMIN', TRUE)
                        ON CONFLICT (phone) DO UPDATE SET role = 'ADMIN', updated_at = NOW()
                        """,
                        (admin_username, hash_password(admin_password), os.getenv("ADMIN_NAME", "관리자"), admin_phone),
                    )
        conn.commit()


def normalize_phone(phone: str) -> str:
    return "".join(ch for ch in phone if ch.isdigit())


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"pbkdf2_sha256${salt}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt, encoded = stored.split("$", 2)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
        return hmac.compare_digest(base64.b64encode(digest).decode(), encoded)
    except ValueError:
        return False


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(user_id: int) -> str:
    payload = {
        "sub": user_id,
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)).timestamp()),
    }
    body = b64url(json.dumps(payload, separators=(",", ":")).encode())
    signature = b64url(hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"


def send_sms_code(phone: str, code: str):
    if not all([SENS_SERVICE_ID, SENS_ACCESS_KEY, SENS_SECRET_KEY, SENS_FROM_NUMBER]):
        raise HTTPException(status_code=500, detail="SMS 발송 설정이 필요합니다.")

    timestamp = str(int(time.time() * 1000))
    path = f"/sms/v2/services/{SENS_SERVICE_ID}/messages"
    signature_message = f"POST {path}\n{timestamp}\n{SENS_ACCESS_KEY}"
    signature = base64.b64encode(
        hmac.new(SENS_SECRET_KEY.encode(), signature_message.encode(), hashlib.sha256).digest()
    ).decode()
    body = {
        "type": "SMS",
        "contentType": "COMM",
        "countryCode": "82",
        "from": normalize_phone(SENS_FROM_NUMBER),
        "content": f"[전세가드 AI] 인증번호는 {code}입니다.",
        "messages": [{"to": phone}],
    }
    request = urllib.request.Request(
        f"https://sens.apigw.ntruss.com{path}",
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "x-ncp-apigw-timestamp": timestamp,
            "x-ncp-iam-access-key": SENS_ACCESS_KEY,
            "x-ncp-apigw-signature-v2": signature,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            if response.status >= 300:
                raise HTTPException(status_code=502, detail="SMS 발송에 실패했습니다.")
    except urllib.error.HTTPError as exc:
        raise HTTPException(status_code=502, detail="SMS 발송에 실패했습니다.") from exc
    except urllib.error.URLError as exc:
        raise HTTPException(status_code=502, detail="SMS 발송 서버에 연결하지 못했습니다.") from exc


def normalize_email(email: str) -> str:
    return email.strip().lower()


def send_email_code(email: str, code: str):
    load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")), override=True)
    smtp_user = os.getenv("GMAIL_SMTP_USER")
    smtp_password = os.getenv("GMAIL_SMTP_PASSWORD")
    from_email = os.getenv("GMAIL_FROM_EMAIL", smtp_user)
    if not smtp_user or not smtp_password:
        raise HTTPException(status_code=500, detail="Gmail SMTP 설정이 필요합니다.")
    message = EmailMessage()
    message["Subject"] = "[전세가드 AI] 이메일 인증번호"
    message["From"] = from_email
    message["To"] = email
    message.set_content(f"전세가드 AI 회원가입 인증번호는 {code}입니다.\n\n5분 안에 입력해주세요.")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=8) as smtp:
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(message)
    except smtplib.SMTPException as exc:
        raise HTTPException(status_code=502, detail="이메일 발송에 실패했습니다.") from exc


def decode_token(token: str) -> int:
    try:
        body, signature = token.split(".", 1)
        expected = b64url(hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        payload = json.loads(b64url_decode(body))
        if int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError
        return int(payload["sub"])
    except Exception as exc:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.") from exc


def current_user_id(authorization: Optional[str]) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    return decode_token(authorization.removeprefix("Bearer ").strip())


def current_user(authorization: Optional[str]):
    user_id = current_user_id(authorization)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, name, phone, email, phone_verified, role FROM app_users WHERE id = %s", (user_id,))
            user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user


def require_admin(authorization: Optional[str]):
    ensure_tables()
    user = current_user(authorization)
    if user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    return user


def save_preferences(cur, user_id: int, data: PreferenceRequest):
    cur.execute(
        """
        INSERT INTO app_user_preferences (
            user_id, preferred_region, max_deposit, preferred_type, move_in_month, priority, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE SET
            preferred_region = EXCLUDED.preferred_region,
            max_deposit = EXCLUDED.max_deposit,
            preferred_type = EXCLUDED.preferred_type,
            move_in_month = EXCLUDED.move_in_month,
            priority = EXCLUDED.priority,
            updated_at = NOW()
        """,
        (
            user_id,
            data.preferred_region,
            data.max_deposit,
            data.preferred_type,
            data.move_in_month,
            data.priority,
        ),
    )


def user_payload(row, pref=None):
    return {
        "id": row["id"],
        "username": row["username"],
        "name": row["name"],
        "phone": row["phone"],
        "email": row.get("email"),
        "role": row.get("role", "MEMBER"),
        "phone_verified": row["phone_verified"],
        "preferences": pref or {},
    }


@router.post("/send-phone-code")
def send_phone_code(payload: PhoneCodeRequest):
    ensure_tables()
    phone = normalize_phone(payload.phone)
    if len(phone) < 10:
        raise HTTPException(status_code=400, detail="휴대폰 번호를 입력해주세요.")
    code = f"{secrets.randbelow(1_000_000):06d}"
    send_sms_code(phone, code)
    expires_at = datetime.now() + timedelta(minutes=5)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_phone_verifications (phone, code, expires_at)
                VALUES (%s, %s, %s)
                """,
                (phone, code, expires_at),
            )
        conn.commit()
    return {"message": "인증번호를 문자로 발송했습니다."}


@router.post("/verify-phone-code")
def verify_phone_code(payload: VerifyPhoneRequest):
    ensure_tables()
    phone = normalize_phone(payload.phone)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM user_phone_verifications
                WHERE phone = %s AND code = %s AND expires_at > NOW()
                ORDER BY id DESC LIMIT 1
                """,
                (phone, payload.code.strip()),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=400, detail="인증번호가 올바르지 않습니다.")
            cur.execute("UPDATE user_phone_verifications SET verified = TRUE WHERE id = %s", (row["id"],))
        conn.commit()
    return {"verified": True}


@router.post("/send-email-code")
def send_email_verification_code(payload: EmailCodeRequest):
    ensure_tables()
    email = normalize_email(payload.email)
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="이메일 주소를 확인해주세요.")
    code = f"{secrets.randbelow(1_000_000):06d}"
    send_email_code(email, code)
    expires_at = datetime.now() + timedelta(minutes=5)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_email_verifications (email, code, expires_at)
                VALUES (%s, %s, %s)
                """,
                (email, code, expires_at),
            )
        conn.commit()
    return {"message": "인증번호를 이메일로 발송했습니다."}


@router.post("/verify-email-code")
def verify_email_code(payload: VerifyEmailRequest):
    ensure_tables()
    email = normalize_email(payload.email)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM user_email_verifications
                WHERE email = %s AND code = %s AND expires_at > NOW()
                ORDER BY id DESC LIMIT 1
                """,
                (email, payload.code.strip()),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=400, detail="인증번호가 올바르지 않습니다.")
            cur.execute("UPDATE user_email_verifications SET verified = TRUE WHERE id = %s", (row["id"],))
        conn.commit()
    return {"verified": True}


@router.post("/register")
def register(payload: RegisterRequest):
    ensure_tables()
    email = normalize_email(payload.email)
    phone = normalize_phone(payload.phone or "")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM user_email_verifications
                WHERE email = %s AND verified = TRUE AND expires_at > NOW()
                ORDER BY id DESC LIMIT 1
                """,
                (email,),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=400, detail="이메일 인증을 완료해주세요.")
            cur.execute(
                "SELECT id FROM app_users WHERE username = %s OR email = %s OR (%s <> '' AND phone = %s)",
                (payload.username.strip(), email, phone, phone),
            )
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="이미 가입된 아이디 또는 이메일입니다.")
            cur.execute(
                """
                INSERT INTO app_users (username, password_hash, name, phone, email, role, phone_verified)
                VALUES (%s, %s, %s, NULLIF(%s, ''), %s, 'MEMBER', FALSE)
                RETURNING id, username, name, phone, email, role, phone_verified
                """,
                (payload.username.strip(), hash_password(payload.password), payload.name.strip(), phone, email),
            )
            user = cur.fetchone()
            save_preferences(cur, user["id"], PreferenceRequest(
                preferred_region=payload.preferred_region,
                max_deposit=payload.max_deposit,
                preferred_type=payload.preferred_type,
                move_in_month=payload.move_in_month,
                priority=payload.priority,
            ))
        conn.commit()
    return {"token": create_token(user["id"]), "user": user_payload(user)}


@router.post("/login")
def login(payload: LoginRequest):
    ensure_tables()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM app_users WHERE username = %s", (payload.username.strip(),))
            user = cur.fetchone()
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호를 확인해주세요.")
    return {"token": create_token(user["id"]), "user": user_payload(user)}


@router.post("/find-id")
def find_id(payload: FindIdRequest):
    ensure_tables()
    phone = normalize_phone(payload.phone)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT username FROM app_users WHERE phone = %s", (phone,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="가입 정보를 찾을 수 없습니다.")
    return {"username": row["username"]}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):
    ensure_tables()
    phone = normalize_phone(payload.phone)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM user_phone_verifications
                WHERE phone = %s AND code = %s AND verified = TRUE AND expires_at > NOW()
                ORDER BY id DESC LIMIT 1
                """,
                (phone, payload.code.strip()),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=400, detail="휴대폰 인증을 완료해주세요.")
            cur.execute(
                """
                UPDATE app_users SET password_hash = %s, updated_at = NOW()
                WHERE username = %s AND phone = %s
                RETURNING id
                """,
                (hash_password(payload.new_password), payload.username.strip(), phone),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="가입 정보를 찾을 수 없습니다.")
        conn.commit()
    return {"message": "비밀번호가 변경되었습니다."}


@router.get("/me")
def me(authorization: Optional[str] = Header(default=None)):
    ensure_tables()
    user_id = current_user_id(authorization)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, name, phone, email, phone_verified, role FROM app_users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            cur.execute("SELECT preferred_region, max_deposit, preferred_type, move_in_month, priority FROM app_user_preferences WHERE user_id = %s", (user_id,))
            pref = cur.fetchone()
    return user_payload(user, pref)


@router.put("/me")
def update_me(payload: ProfileUpdateRequest, authorization: Optional[str] = Header(default=None)):
    ensure_tables()
    user_id = current_user_id(authorization)
    username = payload.username.strip()
    email = normalize_email(payload.email or "") or None
    phone = normalize_phone(payload.phone or "") or None
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="아이디는 3자 이상 입력해주세요.")
    if email and ("@" not in email or "." not in email):
        raise HTTPException(status_code=400, detail="이메일 주소를 확인해주세요.")
    if phone and len(phone) < 10:
        raise HTTPException(status_code=400, detail="휴대폰 번호를 확인해주세요.")
    password_hash = None
    if payload.new_password:
        if len(payload.new_password) < 6:
            raise HTTPException(status_code=400, detail="새 비밀번호는 6자 이상 입력해주세요.")
        if not payload.current_password:
            raise HTTPException(status_code=400, detail="현재 비밀번호를 입력해주세요.")
        password_hash = hash_password(payload.new_password)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM app_users WHERE id = %s", (user_id,))
            current = cur.fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            if password_hash and not verify_password(payload.current_password, current["password_hash"]):
                raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")
            cur.execute("SELECT id FROM app_users WHERE id <> %s AND username = %s LIMIT 1", (user_id, username))
            exists = cur.fetchone()
            if not exists and email:
                cur.execute("SELECT id FROM app_users WHERE id <> %s AND email = %s LIMIT 1", (user_id, email))
                exists = cur.fetchone()
            if not exists and phone:
                cur.execute("SELECT id FROM app_users WHERE id <> %s AND phone = %s LIMIT 1", (user_id, phone))
                exists = cur.fetchone()
            if exists:
                raise HTTPException(status_code=400, detail="이미 사용 중인 아이디, 이메일 또는 휴대폰 번호입니다.")
            if password_hash:
                cur.execute(
                    """
                    UPDATE app_users
                    SET username = %s, email = %s, phone = %s, password_hash = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (username, email, phone, password_hash, user_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE app_users
                    SET username = %s, email = %s, phone = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (username, email, phone, user_id),
                )
            cur.execute("SELECT id, username, name, phone, email, phone_verified, role FROM app_users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            cur.execute("SELECT preferred_region, max_deposit, preferred_type, move_in_month, priority FROM app_user_preferences WHERE user_id = %s", (user_id,))
            pref = cur.fetchone()
        conn.commit()
    return {"message": "회원 정보가 수정되었습니다.", "user": user_payload(user, pref)}


@router.put("/preferences")
def update_preferences(payload: PreferenceRequest, authorization: Optional[str] = Header(default=None)):
    ensure_tables()
    user_id = current_user_id(authorization)
    with get_connection() as conn:
        with conn.cursor() as cur:
            save_preferences(cur, user_id, payload)
        conn.commit()
    return {"message": "희망 조건을 저장했습니다."}
