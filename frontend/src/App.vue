<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { AlertTriangle, Calculator, CalendarDays, CheckCircle2, ClipboardCheck, ExternalLink, Loader2, MessageCircle, PackageCheck, PlayCircle, Send, ShieldCheck, Wrench, X } from '@lucide/vue'
import { useRecommendationStore } from './stores/recommendation'
import chatbotIcon from './assets/chatbot-icon.png'
import joeunCallLogo from './assets/joeun-call-logo.png'

const store = useRecommendationStore()

const form = reactive({
  budget: 300,
  experience_level: 'none',
  delivery_plan: 'try',
  daily_hours: 3,
  used_ok: false,
  priority: 'cost',
  model_preference: 'none',
  area_type: 'flat',
  body_preference: 'none',
})
const activeView = ref('recommend')
const selectedStarter = ref('면허')
const showCostDetails = ref(false)
const selectedRisk = ref('비 오는 날')
const selectedPriceModel = ref('pcx')
const selectedGuideVideo = ref(0)
const chatInput = ref('')
const isChatOpen = ref(false)
const viewTabs = [
  ['recommend', '추천 결과'],
  ['prepare', '입문 준비'],
  ['guide', '운행 가이드'],
  ['price', '가격 참고'],
]
const faqQuickQuestions = ['보험은 뭘 봐야 하나요?', '초기 비용은 얼마 잡아야 하나요?', 'PCX랑 NMAX 차이가 뭐예요?']

const costs = reactive([
  { name: '차량가', value: 300, product: '추천 차량 예산', range: '300~500만' },
  { name: '보험료', value: 80, product: '유상운송 보험', range: '60~120만' },
  { name: '등록/이전비', value: 5, product: '번호판/등록 서류', range: '3~10만' },
  { name: '초기 정비비', value: 15, product: '엔진오일/브레이크 점검', range: '10~30만' },
  { name: '헬멧/보호장비', value: 18, product: 'HJC 보급형 + 기본 보호대', range: '15~35만' },
  { name: '휴대폰 거치대', value: 8, product: 'Quad Lock/RAM 기본형', range: '5~15만' },
  { name: '방진댐퍼', value: 3, product: 'Quad Lock 방진댐퍼', range: '2~4만' },
  { name: 'USB/방수 충전기', value: 5, product: 'Oxford/방수 USB 충전기', range: '3~8만' },
  { name: '배달통/브라켓', value: 25, product: 'GIVI/SHAD/배달통 브라켓', range: '15~45만' },
  { name: '배달가방/고정끈', value: 10, product: '보온보냉 가방 + 고정끈', range: '6~15만' },
  { name: '우비/방수장갑', value: 10, product: 'Komine/RS Taichi급', range: '7~18만' },
  { name: '핸들토시/열선그립', value: 12, product: 'Oxford 열선그립 + 핸들토시', range: '8~20만' },
  { name: '블랙박스', value: 20, product: 'INNOVV/2채널 보급형', range: '15~35만' },
  { name: '락/반사/보조등', value: 8, product: '디스크락/반사스티커/보조등', range: '5~15만' },
])

const starterChecklist = [
  { group: '필수', title: '면허', guide: '125cc 이하 운행 가능 조건을 먼저 확인', brands: '원동기 · 2종 소형 · 자동차면허 조건' },
  { group: '필수', title: '보험', guide: '배달 목적 운행이면 유상운송/시간제 조건 확인', brands: '일반 보험만으로 배달 운행 금지' },
  { group: '필수', title: '번호판/등록', guide: '이륜자동차 사용신고와 등록서류 확인', brands: '번호판 · 등록증 · 양도서류' },
  { group: '필수', title: '헬멧', guide: '초보는 반모보다 턱 보호형 우선', brands: 'HJC · LS2 · SHOEI · Arai' },
  { group: '필수', title: '배달앱 설치', guide: '계정, 정산, 보험 조건을 미리 확인', brands: '배민커넥트 · 쿠팡이츠 · 지역 대행 앱' },
  { group: '권장', title: '휴대폰 거치대', guide: '진동 고정력, 충전, 방수 확인', brands: 'Quad Lock · RAM Mounts · SP Connect · 방수 충전형' },
  { group: '권장', title: '배달가방', guide: '흔들림 고정과 보온/보냉성 우선', brands: '플랫폼 가방 · 보온보냉 가방 · 하드 탑박스' },
  { group: '권장', title: '보조배터리', guide: 'KC 인증, 과열/리콜 여부 확인', brands: 'Anker · Samsung · Xiaomi · 10,000mAh 이상' },
  { group: '상황별', title: '우비/장갑', guide: '밝은색/반사 소재와 방수성 확인', brands: 'Komine · RS Taichi · 방수 장갑류' },
]

const firstWeekPlan = [
  ['1일차', '앱 흐름 익히기', '수락, 픽업, 전달, 사진/메모 처리만 익힙니다.'],
  ['2~3일차', '가까운 거리 위주', '익숙한 동네와 짧은 거리로 실수를 줄입니다.'],
  ['4~5일차', '피크타임 짧게 경험', '점심/저녁 피크를 짧게 타며 압박감을 확인합니다.'],
  ['6~7일차', '체력/수입 감 잡기', '무리하지 않는 시간대와 하루 가능량을 정합니다.'],
]

const riskGuides = [
  ['비 오는 날', '첫 운행은 피하고, 해야 한다면 속도와 콜 수를 줄입니다.'],
  ['야간', '시야 확보와 반사 장비가 없으면 장거리 콜을 피합니다.'],
  ['언덕', '정차/출발, 미끄럼, 브레이크 부담을 먼저 익힙니다.'],
  ['지하주차장', '경사로, 기둥, 보행자, 통신 끊김을 조심합니다.'],
  ['아파트 단지', '보행자, 아이, 차량 출입구를 최우선으로 봅니다.'],
  ['장거리 콜', '초반에는 길 찾기와 피로 누적 때문에 제한합니다.'],
  ['피크타임 과욕', '콜을 많이 잡기보다 사고 없이 끝내는 것이 먼저입니다.'],
]

const preRideChecks = ['타이어', '브레이크', '라이트', '방향지시등', '엔진오일', '배달가방 고정', '헬멧 착용']
const guideVideos = [
  {
    title: '배달용 전기오토바이 실사용',
    source: '이누리 공식 유튜브',
    note: '배달용 오토바이 사용감과 세팅 참고',
    embedUrl: 'https://www.youtube-nocookie.com/embed/zmAe2iXjufA',
    sourceUrl: 'https://www.youtube.com/watch?v=zmAe2iXjufA',
  },
  {
    title: '오토바이 점검/관리 참고',
    source: '국내 유튜브',
    note: '초보 운행 전 기본 점검 흐름 참고',
    embedUrl: 'https://www.youtube-nocookie.com/embed/KuO0QODNoHM',
    sourceUrl: 'https://www.youtube.com/watch?v=KuO0QODNoHM',
  },
  {
    title: '스쿠터 기본 조작 참고',
    source: '국내 유튜브',
    note: '저속 조향과 기본 조작 감각 참고',
    embedUrl: 'https://www.youtube-nocookie.com/embed/ODHrzchIZGU',
    sourceUrl: 'https://www.youtube.com/watch?v=ODHrzchIZGU',
  },
]

const top = computed(() => store.result?.top_model)
const second = computed(() => store.result?.second_model)
const totalStarterCost = computed(() => costs.reduce((sum, item) => sum + Number(item.value || 0), 0))
const starterGroups = computed(() =>
  ['필수', '권장', '상황별'].map((name) => ({
    name,
    items: starterChecklist.filter((item) => item.group === name),
  })),
)
const selectedStarterItem = computed(() => starterChecklist.find((item) => item.title === selectedStarter.value) || starterChecklist[0])
const coreCosts = computed(() => costs.slice(0, 3))
const detailCosts = computed(() => costs.slice(3))
const selectedRiskGuide = computed(() => riskGuides.find((item) => item[0] === selectedRisk.value) || riskGuides[0])
const currentGuideVideo = computed(() => guideVideos[selectedGuideVideo.value] || guideVideos[0])
const priceBandsByModel = computed(() =>
  store.priceBands.reduce((groups, item) => {
    if (!groups[item.model_id]) {
      groups[item.model_id] = {
        modelName: item.model_name,
        bands: [],
      }
    }
    groups[item.model_id].bands.push(item)
    return groups
  }, {}),
)
const selectedPriceGroup = computed(() => priceBandsByModel.value[selectedPriceModel.value])

onMounted(() => {
  store.loadInitialData()
})

function submitRecommendation() {
  store.recommend({ ...form, budget: Number(form.budget), daily_hours: Number(form.daily_hours) })
}

async function askChat(message = chatInput.value) {
  const text = message.trim()
  if (!text || store.chatLoading) return
  chatInput.value = ''
  await store.askFaq(text)
}
</script>

<template>
  <main class="min-h-screen">
    <section class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <div class="flex items-center gap-3">
          <img :src="joeunCallLogo" alt="조은콜 로고" class="h-14 w-14 rounded-full object-contain" />
          <div>
            <h1 class="text-xl font-semibold">라이더 스타터 AI</h1>
            <p class="text-sm text-slate-500">오토바이 추천 · 구매 체크 · 입문 가이드</p>
          </div>
        </div>
        <div class="hidden items-center gap-2 text-sm text-slate-600 sm:flex">
          <ShieldCheck :size="18" class="text-emerald-600" />
          규칙 기반 MVP
        </div>
      </div>
    </section>

    <section class="mx-auto grid max-w-6xl gap-5 px-5 py-6 lg:grid-cols-[390px_1fr]">
      <form class="rounded-md border border-slate-200 bg-white p-5 shadow-sm" @submit.prevent="submitRecommendation">
        <div class="mb-5 flex items-center gap-2">
          <ClipboardCheck :size="20" class="text-emerald-600" />
          <h2 class="text-lg font-semibold">라이더 진단</h2>
        </div>

        <label class="mb-4 block">
          <span class="mb-1 block text-sm font-medium text-slate-700">예산</span>
          <select v-model.number="form.budget" class="w-full rounded-md border border-slate-300 px-3 py-2">
            <option :value="300">300만 원 이하</option>
            <option :value="450">300~450만 원</option>
            <option :value="500">450~500만 원</option>
            <option :value="600">500만 원 이상</option>
          </select>
        </label>

        <label class="mb-4 block">
          <span class="mb-1 block text-sm font-medium text-slate-700">오토바이 경험</span>
          <select v-model="form.experience_level" class="w-full rounded-md border border-slate-300 px-3 py-2">
            <option value="none">없음</option>
            <option value="some">조금 있음</option>
            <option value="experienced">오래 타봄</option>
          </select>
        </label>

        <label class="mb-4 block">
          <span class="mb-1 block text-sm font-medium text-slate-700">배달 계획</span>
          <select v-model="form.delivery_plan" class="w-full rounded-md border border-slate-300 px-3 py-2">
            <option value="try">잠깐 해보기</option>
            <option value="part_time">부업</option>
            <option value="long_term">장기 운행</option>
          </select>
        </label>

        <label class="mb-4 block">
          <span class="mb-1 block text-sm font-medium text-slate-700">하루 운행 시간</span>
          <input v-model.number="form.daily_hours" min="1" max="16" type="number" class="w-full rounded-md border border-slate-300 px-3 py-2" />
        </label>

        <label class="mb-4 block">
          <span class="mb-1 block text-sm font-medium text-slate-700">우선 기준</span>
          <select v-model="form.priority" class="w-full rounded-md border border-slate-300 px-3 py-2">
            <option value="cost">가격</option>
            <option value="popularity">대중성</option>
            <option value="maintenance">유지관리</option>
            <option value="long_term">장기 운행</option>
            <option value="beginner_safety">초보 안정성</option>
          </select>
        </label>

        <label class="mb-4 block">
          <span class="mb-1 block text-sm font-medium text-slate-700">모델 성향</span>
          <select v-model="form.model_preference" class="w-full rounded-md border border-slate-300 px-3 py-2">
            <option value="none">상관없음</option>
            <option value="popular">가장 대중적인 모델</option>
            <option value="pcx_alternative">PCX 외 대안</option>
            <option value="sporty">주행감/스포티함</option>
            <option value="cost">저예산 우선</option>
          </select>
        </label>

        <label class="mb-4 block">
          <span class="mb-1 block text-sm font-medium text-slate-700">지역 특성</span>
          <select v-model="form.area_type" class="w-full rounded-md border border-slate-300 px-3 py-2">
            <option value="flat">평지 위주</option>
            <option value="hills">언덕 많음</option>
            <option value="long_distance">장거리 많음</option>
          </select>
        </label>

        <div class="mb-5 flex items-center justify-between rounded-md border border-slate-200 px-3 py-2">
          <span class="text-sm font-medium text-slate-700">중고 구매 가능</span>
          <input v-model="form.used_ok" type="checkbox" class="h-5 w-5 accent-emerald-600" />
        </div>

        <button class="flex w-full items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 py-3 font-semibold text-white hover:bg-emerald-700" type="submit">
          <Loader2 v-if="store.loading" :size="18" class="animate-spin" />
          <CheckCircle2 v-else :size="18" />
          추천 받기
        </button>

        <p v-if="store.error" class="mt-3 text-sm text-red-600">{{ store.error }}</p>
      </form>

      <div class="space-y-5">
        <nav class="rounded-md border border-slate-200 bg-white p-2 shadow-sm">
          <div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <button
              v-for="tab in viewTabs"
              :key="tab[0]"
              class="rounded-md px-3 py-2 text-sm font-semibold"
              :class="activeView === tab[0] ? 'bg-emerald-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
              type="button"
              @click="activeView = tab[0]"
            >
              {{ tab[1] }}
            </button>
          </div>
        </nav>

        <section v-if="activeView === 'recommend'" class="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <h2 class="mb-4 text-lg font-semibold">추천 결과</h2>
          <div v-if="top" class="grid gap-4 md:grid-cols-2">
            <article class="rounded-md border border-emerald-200 bg-emerald-50 p-4">
              <p class="text-sm font-medium text-emerald-700">1순위</p>
              <h3 class="mt-1 text-2xl font-bold">{{ top.name }}</h3>
              <p class="mt-1 text-sm text-slate-600">세팅 포함 약 {{ top.setup_price }}만 원 · {{ top.total_score }}점</p>
              <div v-if="top.price_guidance" class="mt-3 rounded-md border border-emerald-200 bg-white/70 p-3 text-sm">
                <p class="font-medium text-emerald-800">예산 참고 연식: {{ top.price_guidance.affordable_years }}</p>
                <p class="mt-1 text-slate-700">{{ top.price_guidance.summary }}</p>
                <ul class="mt-2 space-y-1 text-slate-600">
                  <li v-for="band in top.price_guidance.bands" :key="band">- {{ band }}</li>
                </ul>
              </div>
              <ul class="mt-4 space-y-2 text-sm text-slate-700">
                <li v-for="reason in top.reasons" :key="reason">- {{ reason }}</li>
              </ul>
            </article>

            <article class="rounded-md border border-slate-200 p-4">
              <p class="text-sm font-medium text-slate-500">2순위</p>
              <h3 class="mt-1 text-2xl font-bold">{{ second.name }}</h3>
              <p class="mt-1 text-sm text-slate-600">세팅 포함 약 {{ second.setup_price }}만 원 · {{ second.total_score }}점</p>
              <div v-if="second.price_guidance" class="mt-3 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
                <p class="font-medium text-slate-800">예산 참고 연식: {{ second.price_guidance.affordable_years }}</p>
                <p class="mt-1 text-slate-700">{{ second.price_guidance.summary }}</p>
                <ul class="mt-2 space-y-1 text-slate-600">
                  <li v-for="band in second.price_guidance.bands" :key="band">- {{ band }}</li>
                </ul>
              </div>
              <ul class="mt-4 space-y-2 text-sm text-slate-700">
                <li v-for="reason in second.reasons" :key="reason">- {{ reason }}</li>
              </ul>
            </article>
          </div>
          <p v-else class="text-sm text-slate-500">진단을 완료하면 1순위와 2순위 모델이 표시됩니다.</p>
        </section>

        <section v-if="activeView === 'prepare'" class="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <div class="mb-4 flex items-center gap-2">
            <PackageCheck :size="20" class="text-emerald-600" />
            <h2 class="text-lg font-semibold">초보 입문 준비</h2>
          </div>
          <div class="grid gap-4 xl:grid-cols-[1fr_260px]">
            <div class="space-y-4">
              <div v-for="group in starterGroups" :key="group.name">
                <p class="mb-2 text-xs font-bold uppercase text-slate-500">{{ group.name }}</p>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="item in group.items"
                    :key="item.title"
                    class="rounded-md border px-3 py-2 text-sm font-semibold"
                    :class="selectedStarter === item.title ? 'border-emerald-600 bg-emerald-50 text-emerald-800' : 'border-slate-200 text-slate-700 hover:bg-slate-50'"
                    type="button"
                    @click="selectedStarter = item.title"
                  >
                    {{ item.title }}
                  </button>
                </div>
              </div>
            </div>
            <aside class="rounded-md border border-emerald-200 bg-emerald-50 p-4">
              <p class="text-xs font-bold text-emerald-700">{{ selectedStarterItem.group }}</p>
              <h3 class="mt-1 text-lg font-semibold">{{ selectedStarterItem.title }}</h3>
              <p class="mt-2 text-sm leading-6 text-slate-700">{{ selectedStarterItem.guide }}</p>
              <p class="mt-3 text-xs font-semibold text-emerald-800">{{ selectedStarterItem.brands }}</p>
            </aside>
          </div>
        </section>

        <section v-if="activeView === 'prepare'" class="grid gap-5">
          <div class="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div class="mb-4 flex items-center justify-between gap-3">
              <div class="flex items-center gap-2">
                <Calculator :size="20" class="text-emerald-600" />
                <h2 class="text-lg font-semibold">초기 비용 계산기</h2>
              </div>
              <p class="text-xl font-bold text-emerald-700">{{ totalStarterCost }}만 원</p>
            </div>
            <div class="grid gap-3 sm:grid-cols-3">
              <label v-for="item in coreCosts" :key="item.name" class="block">
                <span class="mb-1 block text-sm font-medium text-slate-700">{{ item.name }}</span>
                <span class="mb-1 block text-xs text-slate-500">{{ item.product }} · {{ item.range }}</span>
                <div class="flex items-center rounded-md border border-slate-300 bg-white px-3 py-2">
                  <input v-model.number="item.value" min="0" type="number" class="w-full border-0 p-0 outline-none" />
                  <span class="ml-2 shrink-0 text-sm text-slate-500">만 원</span>
                </div>
              </label>
            </div>
            <button class="mt-3 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" type="button" @click="showCostDetails = !showCostDetails">
              {{ showCostDetails ? '상세 비용 접기' : '상세 비용 펼치기' }}
            </button>
            <div v-if="showCostDetails" class="mt-3 grid gap-3 sm:grid-cols-2">
              <label v-for="item in detailCosts" :key="item.name" class="block">
                <span class="mb-1 block text-sm font-medium text-slate-700">{{ item.name }}</span>
                <span class="mb-1 block text-xs text-slate-500">{{ item.product }} · {{ item.range }}</span>
                <div class="flex items-center rounded-md border border-slate-300 bg-white px-3 py-2">
                  <input v-model.number="item.value" min="0" type="number" class="w-full border-0 p-0 outline-none" />
                  <span class="ml-2 shrink-0 text-sm text-slate-500">만 원</span>
                </div>
              </label>
            </div>
            <p class="mt-3 text-xs text-slate-500">상품명은 대표 예시이며, 실제 구매가는 시점과 장착 공임에 따라 달라질 수 있습니다.</p>
          </div>

        </section>

        <section v-if="activeView === 'guide'" class="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
          <div class="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div class="mb-4 flex items-center gap-2">
              <CalendarDays :size="20" class="text-emerald-600" />
              <h2 class="text-lg font-semibold">첫 7일 운행 플랜</h2>
            </div>
            <div class="grid gap-3">
              <article v-for="step in firstWeekPlan" :key="step[0]" class="grid gap-3 rounded-md border border-slate-200 p-4 sm:grid-cols-[84px_1fr]">
                <p class="text-sm font-bold text-emerald-700">{{ step[0] }}</p>
                <div>
                  <p class="font-semibold text-slate-900">{{ step[1] }}</p>
                  <p class="mt-1 text-sm leading-6 text-slate-600">{{ step[2] }}</p>
                </div>
              </article>
            </div>
          </div>

          <div class="space-y-5">
            <div class="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <div class="mb-4 flex items-center gap-2">
                <Wrench :size="20" class="text-emerald-600" />
                <h2 class="text-lg font-semibold">운행 전 1분 점검</h2>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <div v-for="item in preRideChecks" :key="item" class="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm">
                  <CheckCircle2 :size="16" class="text-emerald-600" />
                  {{ item }}
                </div>
              </div>
            </div>

            <div class="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <div class="mb-4 flex items-center gap-2">
                <AlertTriangle :size="20" class="text-amber-600" />
                <h2 class="text-lg font-semibold">초보 위험 상황</h2>
              </div>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="risk in riskGuides"
                  :key="risk[0]"
                  class="rounded-md border px-3 py-2 text-sm font-semibold"
                  :class="selectedRisk === risk[0] ? 'border-amber-500 bg-amber-50 text-amber-800' : 'border-slate-200 text-slate-700 hover:bg-slate-50'"
                  type="button"
                  @click="selectedRisk = risk[0]"
                >
                  {{ risk[0] }}
                </button>
              </div>
              <div class="mt-4 rounded-md border border-amber-200 bg-amber-50 p-4">
                <p class="font-semibold text-slate-900">{{ selectedRiskGuide[0] }}</p>
                <p class="mt-1 text-sm leading-6 text-slate-700">{{ selectedRiskGuide[1] }}</p>
              </div>
            </div>
          </div>

          <div class="rounded-md border border-slate-200 bg-white p-5 shadow-sm xl:col-span-2">
            <div class="mb-4 flex items-center justify-between gap-3">
              <div class="flex items-center gap-2">
                <PlayCircle :size="20" class="text-emerald-600" />
                <h2 class="text-lg font-semibold">관련 영상</h2>
              </div>
              <a :href="currentGuideVideo.sourceUrl" target="_blank" rel="noreferrer" class="flex items-center gap-1 text-sm font-semibold text-emerald-700 hover:text-emerald-800">
                원본 열기
                <ExternalLink :size="14" />
              </a>
            </div>
            <div class="grid gap-4 lg:grid-cols-[260px_1fr]">
              <div class="grid gap-2">
                <button
                  v-for="(video, index) in guideVideos"
                  :key="video.title"
                  class="rounded-md border px-3 py-2 text-left"
                  :class="selectedGuideVideo === index ? 'border-emerald-600 bg-emerald-50' : 'border-slate-200 hover:bg-slate-50'"
                  type="button"
                  @click="selectedGuideVideo = index"
                >
                  <span class="block text-sm font-semibold text-slate-900">{{ video.title }}</span>
                  <span class="mt-1 block text-xs font-semibold text-emerald-700">{{ video.source }}</span>
                  <span class="mt-1 block text-xs text-slate-500">{{ video.note }}</span>
                </button>
              </div>
              <div class="aspect-video overflow-hidden rounded-md border border-slate-200 bg-slate-100">
                <iframe
                  class="h-full w-full"
                  :src="currentGuideVideo.embedUrl"
                  :title="currentGuideVideo.title"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  referrerpolicy="strict-origin-when-cross-origin"
                  allowfullscreen
                ></iframe>
              </div>
            </div>
          </div>
        </section>

        <section v-if="activeView === 'price'" class="grid gap-5 xl:grid-cols-2">
          <div class="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <h2 class="mb-1 text-lg font-semibold">모델 가격 참고</h2>
            <p class="mb-4 text-sm text-slate-500">추천은 모델 성향 기준이며 가격은 예산 판단용 참고 정보입니다.</p>
            <div class="overflow-x-auto">
              <table class="w-full text-left text-sm">
                <thead class="border-b text-slate-500">
                  <tr>
                    <th class="py-2">모델</th>
                    <th class="py-2">세팅가</th>
                    <th class="py-2">포지션</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in store.motorcycles" :key="item.id" class="border-b border-slate-100">
                    <td class="py-2 font-medium">{{ item.name }}</td>
                    <td class="py-2">{{ item.setup_price }}만 원</td>
                    <td class="py-2 text-slate-600">{{ item.description }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <h2 class="mb-4 text-lg font-semibold">중고 구매 체크</h2>
            <ul class="space-y-2 text-sm text-slate-700">
              <li v-for="item in store.result?.checklist || []" :key="item" class="flex gap-2">
                <CheckCircle2 :size="16" class="mt-0.5 shrink-0 text-emerald-600" />
                {{ item }}
              </li>
            </ul>
          </div>
        </section>

        <section v-if="activeView === 'price'" class="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <h2 class="mb-1 text-lg font-semibold">연식별 시세 참고</h2>
          <p class="mb-4 text-sm text-slate-500">가격은 추천 기준이 아니라 예산 판단을 돕는 참고 정보입니다. 차량가 기준이며 세팅비, 이전비, 보험료는 제외했습니다.</p>
          <div class="mb-4 flex flex-wrap gap-2">
            <button
              v-for="item in store.motorcycles"
              :key="item.id"
              class="rounded-md border px-3 py-2 text-sm font-semibold"
              :class="selectedPriceModel === item.id ? 'border-emerald-600 bg-emerald-50 text-emerald-800' : 'border-slate-200 text-slate-700 hover:bg-slate-50'"
              type="button"
              @click="selectedPriceModel = item.id"
            >
              {{ item.name }}
            </button>
          </div>
          <div v-if="selectedPriceGroup" class="overflow-x-auto">
            <table class="w-full text-left text-sm">
              <thead class="border-b text-slate-500">
                <tr>
                  <th class="py-2">연식</th>
                  <th class="py-2">구분</th>
                  <th class="py-2">가격 구간</th>
                  <th class="py-2">메모</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="band in selectedPriceGroup.bands" :key="`${band.model_id}-${band.year}-${band.condition_type}`" class="border-b border-slate-100">
                  <td class="py-2 font-medium">{{ band.year }}</td>
                  <td class="py-2">{{ band.condition_type }}</td>
                  <td class="py-2">{{ band.price_min }}~{{ band.price_max }}만 원</td>
                  <td class="min-w-56 py-2 text-slate-600">{{ band.note }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

      </div>
    </section>

    <div class="fixed bottom-5 right-4 z-50 sm:right-6">
      <section
        v-if="isChatOpen"
        class="mb-3 w-[calc(100vw-2rem)] max-w-sm overflow-hidden rounded-md border border-slate-200 bg-white shadow-xl sm:w-96"
      >
        <div class="flex items-center justify-between border-b border-slate-200 px-4 py-3">
          <div class="flex items-center gap-2">
            <MessageCircle :size="20" class="text-emerald-600" />
            <div>
              <h2 class="text-sm font-bold text-slate-900">무료 FAQ 상담</h2>
              <p class="text-xs text-slate-500">키워드 검색 · 비용 0원</p>
            </div>
          </div>
          <button
            class="rounded-md p-2 text-slate-500 hover:bg-slate-100"
            type="button"
            aria-label="상담창 닫기"
            @click="isChatOpen = false"
          >
            <X :size="18" />
          </button>
        </div>

        <div class="max-h-80 space-y-2 overflow-y-auto bg-slate-50 p-3">
          <div
            v-for="(message, index) in store.chatMessages"
            :key="`${message.role}-${index}`"
            class="flex"
            :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <div
              class="max-w-[86%] rounded-md px-3 py-2 text-sm leading-6"
              :class="message.role === 'user' ? 'bg-emerald-600 text-white' : 'border border-slate-200 bg-white text-slate-700'"
            >
              <p v-if="message.title" class="mb-1 text-xs font-bold text-emerald-700">{{ message.title }}</p>
              <p>{{ message.text }}</p>
              <div v-if="message.related && message.related.length" class="mt-2 flex flex-wrap gap-1">
                <button
                  v-for="item in message.related"
                  :key="item"
                  class="rounded-md border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  type="button"
                  @click="askChat(item)"
                >
                  {{ item }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="border-t border-slate-200 p-3">
          <form class="flex gap-2" @submit.prevent="askChat()">
            <input
              v-model="chatInput"
              class="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
              placeholder="예: 보험은 뭘 봐야 하나요?"
            />
            <button
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"
              type="submit"
              :disabled="store.chatLoading"
              aria-label="질문 보내기"
            >
              <Loader2 v-if="store.chatLoading" :size="16" class="animate-spin" />
              <Send v-else :size="16" />
            </button>
          </form>

          <p v-if="store.chatError" class="mt-2 text-sm text-red-600">{{ store.chatError }}</p>
          <div class="mt-3 flex flex-wrap gap-2">
            <button
              v-for="question in faqQuickQuestions"
              :key="question"
              class="rounded-md border border-slate-200 px-2 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
              type="button"
              @click="askChat(question)"
            >
              {{ question }}
            </button>
          </div>
        </div>
      </section>

      <button
        class="ml-auto flex h-16 w-16 items-center justify-center overflow-hidden rounded-full border border-slate-200 bg-white p-1 shadow-lg shadow-emerald-900/20 hover:border-emerald-300"
        type="button"
        :aria-label="isChatOpen ? '챗봇 닫기' : '챗봇 열기'"
        @click="isChatOpen = !isChatOpen"
      >
        <X v-if="isChatOpen" :size="24" class="text-slate-700" />
        <img v-else :src="chatbotIcon" alt="" class="h-full w-full rounded-full object-contain" />
      </button>
    </div>
  </main>
</template>
