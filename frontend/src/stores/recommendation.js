import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useRecommendationStore = defineStore('recommendation', {
  state: () => ({
    motorcycles: [],
    priceBands: [],
    guides: [],
    result: null,
    chatMessages: [
      {
        role: 'assistant',
        text: '궁금한 내용을 짧게 물어보세요. 추천, 보험, 면허, 초기 비용, 연식별 가격, 운행 전 점검을 FAQ에서 찾아 답합니다.',
      },
    ],
    chatLoading: false,
    chatError: '',
    loading: false,
    error: '',
  }),
  actions: {
    async loadInitialData() {
      const [motorcycles, priceBands, guides] = await Promise.all([
        api.get('/motorcycles'),
        api.get('/price-bands'),
        api.get('/guides'),
      ])
      this.motorcycles = motorcycles.data
      this.priceBands = priceBands.data
      this.guides = guides.data
    },
    async recommend(payload) {
      this.loading = true
      this.error = ''
      try {
        const response = await api.post('/recommend', payload)
        this.result = response.data
      } catch (error) {
        this.error = error.response?.data?.detail || '추천 결과를 불러오지 못했습니다.'
      } finally {
        this.loading = false
      }
    },
    async askFaq(message) {
      const text = message.trim()
      if (!text) return

      this.chatLoading = true
      this.chatError = ''
      this.chatMessages.push({ role: 'user', text })

      try {
        const response = await api.post('/chat', { message: text })
        this.chatMessages.push({
          role: 'assistant',
          text: response.data.answer,
          title: response.data.matched_title || 'FAQ 검색',
          related: response.data.related_questions || [],
        })
      } catch (error) {
        this.chatError = error.response?.data?.detail || 'FAQ 답변을 불러오지 못했습니다.'
      } finally {
        this.chatLoading = false
      }
    },
  },
})
