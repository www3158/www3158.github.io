from sqlmodel import Session, select

from app.models import GuideContent, MotorcycleModel
from app.price_models import MotorcyclePriceBand


MOTORCYCLES = [
    {
        "id": "pcx",
        "name": "PCX",
        "base_price": 470,
        "setup_price": 500,
        "market_share": 60,
        "beginner_score": 85,
        "cost_score": 60,
        "long_term_score": 90,
        "popularity_score": 100,
        "maintenance_score": 90,
        "description": "배달 시장에서 가장 대중적인 장기 운행용 스쿠터입니다.",
        "pros": ["정보와 사례가 많음", "중고 거래가 활발함", "장기 운행에 안정적"],
        "cons": ["초기 비용이 높음"],
        "recommended_for": ["500만 원 전후 예산", "장기 운행", "대중성 중시"],
        "caution": ["중고 구매 시 사고 여부와 정비 이력을 확인하세요."],
    },
    {
        "id": "nmax",
        "name": "NMAX",
        "base_price": 470,
        "setup_price": 500,
        "market_share": 20,
        "beginner_score": 85,
        "cost_score": 60,
        "long_term_score": 88,
        "popularity_score": 80,
        "maintenance_score": 85,
        "description": "PCX와 함께 비교되는 대중적인 장기 운행 후보입니다.",
        "pros": ["PCX 대안", "장기 운행 후보", "대중적인 선택지"],
        "cons": ["초기 비용이 높음"],
        "recommended_for": ["PCX 외 대안", "장기 운행", "대중 모델 비교"],
        "caution": ["주변 정비 접근성과 부품 수급을 확인하세요."],
    },
    {
        "id": "uhr",
        "name": "UHR",
        "base_price": 450,
        "setup_price": 480,
        "market_share": 20,
        "beginner_score": 80,
        "cost_score": 70,
        "long_term_score": 75,
        "popularity_score": 60,
        "maintenance_score": 70,
        "description": "PCX/NMAX가 부담될 때 고려할 수 있는 중간 가격대 대안입니다.",
        "pros": ["상위 모델보다 가격 부담이 낮음", "125cc급 스쿠터 대안"],
        "cons": ["정비 접근성과 부품 수급 확인 필요"],
        "recommended_for": ["450만 원 이하 가격대", "중간 가격대 대안", "125cc급 선호"],
        "caution": ["가격만 보지 말고 정비 가능 여부를 확인하세요."],
    },
    {
        "id": "vf100r",
        "name": "VF100R",
        "base_price": 250,
        "setup_price": 300,
        "market_share": 0,
        "beginner_score": 75,
        "cost_score": 95,
        "long_term_score": 60,
        "popularity_score": 50,
        "maintenance_score": 65,
        "description": "초기 비용을 줄이고 배달을 먼저 경험해보기 좋은 입문용 모델입니다.",
        "pros": ["초기 비용이 낮음", "입문용으로 현실적", "배달 세팅 포함 약 300만 원대"],
        "cons": ["장기 운행, 승차감, 적재성은 상위 모델과 비교 필요"],
        "recommended_for": ["300만 원대 예산", "완전 초보", "일단 경험해보기"],
        "caution": ["장시간 배달 계획이면 PCX/NMAX급도 비교하세요."],
    },
]

GUIDES = [
    ("면허", "면허 확인", "125cc 이하라도 운전 가능 면허 조건을 먼저 확인하세요."),
    ("보험", "보험 확인", "배달 목적 운행은 일반 보험과 조건이 다를 수 있어 가입 가능 여부를 확인해야 합니다."),
    ("점검", "배달 전 1분 점검", "타이어, 브레이크, 라이트, 방향지시등, 엔진오일, 거치대, 배달가방, 헬멧을 확인하세요."),
    ("중고", "중고 구매 체크", "시동, 공회전, 엔진 소음, 브레이크, 타이어, 사고 흔적, 서류 상태를 확인하세요."),
    ("안전", "비/야간/언덕 주의", "노면 상태와 시야가 나쁠 때는 속도를 낮추고 무리한 콜 수행을 피하세요."),
]

PRICE_BANDS = [
    # PCX: 신차가 470만 원대, 확인 중고 매물과 인접 연식 감가 기준.
    ("pcx", "PCX", 2026, "신차/재고", 470, 540, "신차 차량가 470만 원대, 판매처 배달 파츠 포함 상품은 500만 원대까지 확인"),
    ("pcx", "PCX", 2025, "최근 중고", 390, 460, "2025년형 신차가 472만 원 기준, 최근 중고 보간"),
    ("pcx", "PCX", 2024, "중고", 300, 380, "고주행 배달 매물은 더 낮을 수 있음"),
    ("pcx", "PCX", 2023, "중고", 270, 340, "상태와 주행거리 편차 반영"),
    ("pcx", "PCX", 2022, "중고", 250, 300, "2022년식 270만 원대 매물 확인"),
    ("pcx", "PCX", 2021, "중고", 210, 270, "인접 연식 감가 보간"),
    ("pcx", "PCX", 2020, "중고", 180, 240, "인접 연식 감가 보간"),

    # NMAX: 국내 125/155 매물이 섞여 있어 MVP에서는 NMAX 계열로 관리.
    ("nmax", "NMAX", 2026, "신차/재고", 460, 490, "2026년형 NMAX 125/155 관련 가격 자료 기준"),
    ("nmax", "NMAX", 2025, "최근 중고", 400, 470, "2025년식 NMAX125 ABS 468만 원 판매가 확인"),
    ("nmax", "NMAX", 2024, "중고", 340, 430, "2024년식 신차/중고 혼재 구간"),
    ("nmax", "NMAX", 2023, "중고", 300, 380, "인접 연식 감가 보간"),
    ("nmax", "NMAX", 2022, "중고", 250, 330, "2022년식 NMAX 계열 250만 원대 매물 확인"),
    ("nmax", "NMAX", 2021, "중고", 220, 290, "2021년식 220만 원대 매물 확인"),
    ("nmax", "NMAX", 2020, "중고", 180, 240, "2020년식 170만 원대 매물 확인"),

    # UHR: 출시 연식이 비교적 짧아 2022년 이후만 관리.
    ("uhr", "UHR", 2026, "신차/재고", 440, 450, "2026년식 판매가 445만 원 확인"),
    ("uhr", "UHR", 2025, "최근 중고", 300, 340, "2025년식 개인중고 310만 원 매물 확인"),
    ("uhr", "UHR", 2025, "신차/재고", 420, 445, "2025년식 권장소비자가 420만 원대 확인"),
    ("uhr", "UHR", 2024, "중고", 300, 360, "2024년식 중고 매물과 감가 보간"),
    ("uhr", "UHR", 2024, "신차/재고", 410, 430, "2024년식 권장소비자가 420만 원 확인"),
    ("uhr", "UHR", 2023, "중고", 260, 330, "인접 연식 감가 보간"),
    ("uhr", "UHR", 2022, "중고", 230, 300, "초기 연식 감가 보간"),

    # VF100R: 중고시장에서는 VF100R/P/F 명칭이 섞임.
    ("vf100r", "VF100R", 2026, "신차/재고", 260, 270, "DNA Motors 공식 VF100R 265만 원 확인"),
    ("vf100r", "VF100R", 2025, "최근 중고", 210, 250, "신차가 대비 감가 보간"),
    ("vf100r", "VF100R", 2024, "중고", 170, 230, "인접 연식 감가 보간"),
    ("vf100r", "VF100R", 2023, "중고", 140, 190, "VF100 계열 매물 기준 보간"),
    ("vf100r", "VF100R", 2022, "중고", 110, 150, "2022년식 VF100P 125만 원 매물 확인"),
    ("vf100r", "VF100R", 2021, "중고", 100, 140, "인접 연식 감가 보간"),
    ("vf100r", "VF100R", 2020, "중고", 90, 130, "2020년식 VF100F 110만 원 매물 확인"),
]


def seed_initial_data(session: Session) -> None:
    if not session.exec(select(MotorcycleModel)).first():
        session.add_all(MotorcycleModel(**item) for item in MOTORCYCLES)

    if not session.exec(select(GuideContent)).first():
        session.add_all(
            GuideContent(category=category, title=title, content=content, sort_order=index)
            for index, (category, title, content) in enumerate(GUIDES, start=1)
        )

    if not session.exec(select(MotorcyclePriceBand)).first():
        session.add_all(
            MotorcyclePriceBand(
                model_id=model_id,
                model_name=model_name,
                year=year,
                condition_type=condition_type,
                price_min=price_min,
                price_max=price_max,
                note=note,
            )
            for model_id, model_name, year, condition_type, price_min, price_max, note in PRICE_BANDS
        )

    session.commit()
