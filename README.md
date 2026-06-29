# 박주환 Portfolio

AI 추천 서비스와 데이터 기반 웹 서비스를 구현하는 AI Full-Stack 개발자 박주환의 포트폴리오 저장소입니다.

[![Portfolio](https://img.shields.io/badge/Portfolio-www3158.github.io-111111?style=flat-square&logo=githubpages)](https://www3158.github.io/)
[![GitHub](https://img.shields.io/badge/GitHub-www3158-181717?style=flat-square&logo=github)](https://github.com/www3158)

## 배포 프로젝트

| 경로 | 프로젝트 | 구분 | 바로가기 |
| --- | --- | --- | --- |
| `web01` | 성남 문화관광 사이트 | 공공기관형 웹사이트 | [서비스 열기](https://www3158.github.io/web01/) |
| `web02` | Rider Starter AI | 오토바이 추천·입문 가이드 | [서비스 열기](https://www3158.github.io/web02/) |
| `web03` | LUXE SHOP | 쇼핑몰 프론트엔드 | [서비스 열기](https://www3158.github.io/web03/) |
| `web04` | JS 전세 안전 서비스 | 전세 위험 분석·매물 추천 | [서비스 열기](https://www3158.github.io/web04/) |

## web01. 성남 문화관광 사이트

성남시의 관광지, 역사·문화, 축제·행사 정보를 정리한 공공기관형 웹사이트입니다.

### 주요 기능

- 성남 8경, 공원·자연, 쇼핑·거리, 맛집 등 관광 정보 제공
- 성남문화예술제, 탄천페스티벌, 파크콘서트 등 행사 안내
- 남한산성, 봉국사, 판교박물관, 성남아트센터 소개
- 시티투어버스, 공영주차장, 관광지도 등 여행 편의 정보 제공
- 로그인, 회원가입, 새소식, 포토갤러리, 여행후기, Q&A 화면 구성

### 기술 스택

`HTML5` `CSS3` `JavaScript` `GitHub Pages`

## web02. Rider Starter AI

초보 라이더의 예산과 운행 조건을 분석해 적합한 오토바이 모델과 구매·운행 가이드를 제공하는 서비스입니다.

### 주요 기능

- 예산, 경험, 배달 계획, 운행 시간, 지역 특성 기반 모델 추천
- 추천 1·2순위와 모델별 추천 근거 및 예상 세팅 비용 제공
- 신차·중고 연식별 가격 구간과 구매 체크리스트 제공
- 초기 비용 계산기, 첫 7일 운행 플랜, 운행 전 점검 안내
- 보험, 면허, 비용 관련 FAQ 검색형 챗봇

### 기술 스택

- Frontend: `Vue 3` `Vite` `Tailwind CSS` `Pinia` `Axios`
- Backend: `FastAPI` `Pydantic` `SQLModel`
- Database: `PostgreSQL` `Supabase`
- Deploy: `GitHub Pages` `Render`

## web03. LUXE SHOP

상품 탐색부터 장바구니까지 쇼핑 흐름을 구현한 패션 쇼핑몰 프론트엔드입니다.

### 주요 기능

- 카테고리별 상품 목록과 검색·필터·정렬
- 상품 상세 정보, 옵션, 재고, 할인 가격 표시
- 장바구니 추가·삭제와 주문 금액 계산
- 관심 상품 관리와 결제 화면 흐름 구성
- JSON 상품 데이터를 활용한 동적 화면 렌더링

### 기술 스택

`Vue 3` `Vite` `Pinia` `Vue Router` `Bootstrap Icons` `JSON` `GitHub Pages`

## web04. JS 전세 안전 서비스

전세 매물을 추천하고 확인 가능한 데이터를 바탕으로 위험 요소와 추가 점검 항목을 제시하는 생활형 안전 플랫폼입니다.

### 주요 기능

- 희망 보증금, 지역, 주택 유형을 반영한 매물 조회·추천
- 근저당, 압류, 신탁등기 등 항목별 위험 점수와 분석 근거 제공
- 주변 중개업소 정보와 리뷰 제공
- 계약 전 서류·권리관계·보증 가능성 체크리스트 제공
- 회원가입, 로그인, 본인 확인, 선호 조건과 마이페이지 관리
- 매물, 문의, 체크리스트를 관리하는 관리자 화면

### 기술 스택

- Frontend: `Vue 3` `Vite` `JavaScript` `HTML5` `CSS3`
- Backend: `FastAPI` `Uvicorn`
- Database: `PostgreSQL` `Supabase`
- Deploy: `GitHub Pages` `Render`

> 이 서비스는 매물의 안전을 보장하지 않습니다. 현재 확인 가능한 데이터를 기준으로 위험 요소와 계약 전 추가 확인 사항을 안내합니다.

## 배포 구조

```text
사용자
  └─ GitHub Pages
      ├─ /web01  성남 문화관광
      ├─ /web02  Rider Starter AI ── Render API ── Supabase PostgreSQL
      ├─ /web03  LUXE SHOP
      └─ /web04  JS 전세 안전 서비스 ── Render API ── Supabase PostgreSQL
```

- 정적 프론트엔드는 GitHub Pages의 경로별 디렉터리로 배포했습니다.
- API 서버는 Render, 서비스 데이터는 Supabase PostgreSQL에 배포했습니다.
- 포트폴리오 메인에서 각 프로젝트를 새 탭으로 열 수 있습니다.

## 저장소 구조

```text
www3158.github.io/
├─ index.html             # 포트폴리오 메인
├─ web01/                 # 성남 문화관광 사이트
├─ web02/                 # Rider Starter AI 프론트엔드
├─ web03/                 # LUXE SHOP 프론트엔드
├─ web04/                 # JS 전세 안전 서비스 프론트엔드
└─ project-screenshots/   # 프로젝트 미리보기 이미지
```

## Contact

- GitHub: [github.com/www3158](https://github.com/www3158)
- Email: [lasr5324@gmail.com](mailto:lasr5324@gmail.com)
