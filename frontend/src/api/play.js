import axios from 'axios'

// Các endpoint /play KHONG su dung JWT: tao instance axios chua interceptor token.
const api = axios.create({
  baseURL: '/api',
})

export const playApi = {
  lookup(code) {
    return api.get('/play/lookup', { params: { code } })
  },
  join(payload) {
    return api.post('/play/join', payload)
  },
  state(token) {
    return api.get(`/play/${encodeURIComponent(token)}/state`)
  },
  answer(token, questionId, choiceIds) {
    return api.post(`/play/${encodeURIComponent(token)}/answer`, {
      question_id: questionId,
      choice_ids: choiceIds,
    })
  },
  next(token) {
    return api.post(`/play/${encodeURIComponent(token)}/next`)
  },
  result(token) {
    return api.get(`/play/${encodeURIComponent(token)}/result`)
  },
  ranking(token) {
    return api.get(`/play/${encodeURIComponent(token)}/ranking`)
  },
  event(token, type) {
    return api.post(`/play/${encodeURIComponent(token)}/event`, { type })
  },
}