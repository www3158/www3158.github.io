from dataclasses import dataclass
import re

from app.models import ChatResponse


@dataclass(frozen=True)
class FaqItem:
    category: str
    title: str
    keywords: tuple[str, ...]
    answer: str


FAQ_ITEMS = [
    FaqItem(
        "추천",
        "추천 결과 기준",
        ("추천 결과", "모델 추천", "오토바이 추천", "라이더 추천", "PCX", "NMAX", "UHR", "VF100R", "1순위"),
        "추천은 가격만 보지 않고 예산, 운행 시간, 중고 가능 여부, 지역 특성, 장기 운행 계획을 같이 봅니다. 저예산 체험은 VF100R, 장기 운행과 유지관리는 PCX/NMAX, 중간 예산 대안은 UHR 쪽이 유리합니다.",
    ),
    FaqItem(
        "모델",
        "PCX",
        ("pcx", "피씨엑스", "혼다", "장기", "대중성", "유지관리"),
        "PCX는 중고 정보와 정비 접근성이 좋고 장기 운행에 강합니다. 다만 초기 비용이 높아서 300만 원 이하 예산이면 연식과 상태를 더 꼼꼼히 봐야 합니다.",
    ),
    FaqItem(
        "모델",
        "NMAX",
        ("nmax", "엔맥스", "야마하", "pcx 대안", "주행감", "장기"),
        "NMAX는 PCX의 직접 대안입니다. 주행감과 안정성을 중시하고 PCX 말고 다른 선택지를 원하면 우선 검토할 만합니다. 예산은 PCX와 비슷하게 잡는 편이 안전합니다.",
    ),
    FaqItem(
        "모델",
        "UHR",
        ("uhr", "유에이치알", "중간", "대안", "가성비"),
        "UHR은 PCX/NMAX보다 부담을 낮추고 싶은 중간 예산 대안입니다. 구매 전에는 근처 정비 접근성과 부품 수급을 먼저 확인하는 게 중요합니다.",
    ),
    FaqItem(
        "모델",
        "VF100R",
        ("vf100r", "vf", "브이에프", "저예산", "입문", "처음", "가성비"),
        "VF100R은 초기 비용을 낮춰 입문하기 좋습니다. 다만 장시간 배달, 장기 운행, 승차감까지 생각하면 PCX/NMAX급도 같이 비교해야 합니다.",
    ),
    FaqItem(
        "입문 준비",
        "면허",
        ("면허", "원동기", "2종", "125cc", "운전면허"),
        "125cc 이하라도 운행 가능 면허 조건을 먼저 확인해야 합니다. 본인 면허로 해당 이륜차를 운행할 수 있는지 확인한 뒤 보험과 등록을 진행하세요.",
    ),
    FaqItem(
        "입문 준비",
        "보험",
        ("보험", "유상운송", "시간제", "배달 보험", "책임보험"),
        "배달 목적이면 일반 보험만으로 부족할 수 있습니다. 유상운송 또는 시간제 보험 조건을 먼저 확인해야 사고 시 문제가 줄어듭니다.",
    ),
    FaqItem(
        "입문 준비",
        "번호판/등록",
        ("번호판", "등록", "이전", "사용신고", "서류"),
        "이륜자동차 사용신고, 번호판, 등록증, 양도서류를 확인해야 합니다. 중고 구매라면 명의 이전 가능 여부를 구매 전에 먼저 확인하세요.",
    ),
    FaqItem(
        "초기 비용",
        "초기 비용 계산",
        ("초기비용", "초기 비용", "계산기", "세팅비", "장비", "튜닝", "총비용"),
        "초기 비용은 차량가, 보험료, 등록/이전비, 초기 정비비, 헬멧, 거치대, 충전기, 배달가방, 우비/장갑까지 합쳐 봐야 합니다. 화면의 초기 비용 계산기에서 항목별 금액을 조정하세요.",
    ),
    FaqItem(
        "운행 가이드",
        "운행 전 1분 점검",
        ("점검", "1분", "타이어", "브레이크", "라이트", "엔진오일", "가방 고정"),
        "출발 전에는 타이어, 브레이크, 라이트, 방향지시등, 엔진오일, 배달가방 고정, 헬멧 착용을 빠르게 확인하세요.",
    ),
    FaqItem(
        "운행 가이드",
        "비 오는 날/야간",
        ("비", "우천", "비오는날", "야간", "밤", "미끄럼"),
        "비 오는 날과 야간은 초보에게 사고 위험이 높습니다. 첫 주에는 피하고, 꼭 해야 한다면 속도와 콜 수를 줄이고 짧은 거리 위주로 운행하세요.",
    ),
    FaqItem(
        "운행 가이드",
        "언덕/지하주차장/아파트",
        ("언덕", "지하주차장", "아파트", "단지", "경사로", "보행자"),
        "언덕, 지하주차장, 아파트 단지는 저속 조작과 보행자 확인이 핵심입니다. 초반에는 무리한 콜보다 익숙한 동선부터 잡는 게 안전합니다.",
    ),
    FaqItem(
        "운행 가이드",
        "첫 7일 운행 플랜",
        ("7일", "첫주", "첫 출근", "처음 운행", "피크타임", "장거리"),
        "1일차는 앱 흐름, 2~3일차는 가까운 거리, 4~5일차는 피크타임 짧게, 6~7일차는 체력과 수입 감을 잡는 방식이 좋습니다.",
    ),
    FaqItem(
        "가격 참고",
        "연식별 가격",
        ("가격", "시세", "연식", "중고", "몇년식", "예산"),
        "연식별 가격은 추천 기준이 아니라 예산 판단용 참고입니다. 실제 구매 전에는 주행거리, 사고 이력, 소모품 상태, 등록 서류를 같이 확인해야 합니다.",
    ),
    FaqItem(
        "운행 가이드",
        "관련 영상",
        ("영상", "유튜브", "동영상", "보는법", "참고영상"),
        "운행 가이드 탭의 관련 영상에서 국내 유튜브 참고 영상을 볼 수 있습니다. 영상은 보조 자료이고, 실제 운행 전에는 1분 점검과 보험 조건을 먼저 확인하세요.",
    ),
]

DEFAULT_RELATED = ["보험은 뭘 봐야 하나요?", "초기 비용은 얼마 잡아야 하나요?", "PCX랑 NMAX 차이가 뭐예요?"]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def _score(item: FaqItem, message: str) -> int:
    normalized = _normalize(message)
    tokens = set(re.findall(r"[0-9a-zA-Z가-힣]+", message.lower()))
    score = 0
    for keyword in item.keywords:
        key = _normalize(keyword)
        if key and key in normalized:
            score += 5 if len(key) >= 3 else 3
        if keyword.lower() in tokens:
            score += 2
    if _normalize(item.title) in normalized:
        score += 5
    return score


def answer_faq(message: str) -> ChatResponse:
    ranked = sorted(
        ((_score(item, message), item) for item in FAQ_ITEMS),
        key=lambda pair: pair[0],
        reverse=True,
    )
    best_score, best = ranked[0]
    related = [item.title for score, item in ranked[1:5] if score > 0][:3] or DEFAULT_RELATED

    if best_score <= 0:
        return ChatResponse(
            answer="현재 FAQ에서 정확히 찾지 못했습니다. 추천 모델, 초기 비용, 보험, 면허, 연식별 가격, 운행 전 점검처럼 짧게 다시 질문해 주세요.",
            confidence=0,
            related_questions=DEFAULT_RELATED,
        )

    return ChatResponse(
        answer=best.answer,
        matched_title=best.title,
        category=best.category,
        confidence=min(round(best_score / 15, 2), 1),
        related_questions=related,
    )
