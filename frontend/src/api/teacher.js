import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

function downloadBlob(res, filename) {
  const url = window.URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

export const teacherApi = {
  // Danh sach bo de
  listQuizzes() {
    return api.get('/teacher/quizzes')
  },

  // Chi tiet bo de
  getQuiz(quizId) {
    return api.get(`/teacher/quizzes/${encodeURIComponent(quizId)}`)
  },

  // Tao bo de
  createQuiz(payload) {
    return api.post('/teacher/quizzes', payload)
  },

  // Cap nhat bo de
  updateQuiz(quizId, payload) {
    return api.put(`/teacher/quizzes/${encodeURIComponent(quizId)}`, payload)
  },

  // Công tác công khóa / mở đồng nhận bài
  publishQuiz(quizId, payload) {
    return api.patch(`/teacher/quizzes/${encodeURIComponent(quizId)}/publish`, payload)
  },

  // Xoa bo de
  deleteQuiz(quizId) {
    return api.delete(`/teacher/quizzes/${encodeURIComponent(quizId)}`)
  },

  // Cau hoi
  addQuestion(quizId, payload) {
    return api.post(`/teacher/quizzes/${encodeURIComponent(quizId)}/questions`, payload)
  },

  updateQuestion(questionId, payload) {
    return api.put(`/teacher/questions/${encodeURIComponent(questionId)}`, payload)
  },

  deleteQuestion(questionId) {
    return api.delete(`/teacher/questions/${encodeURIComponent(questionId)}`, payload)
  },

  reorderQuestions(quizId, ids) {
    return api.put(`/teacher/quizzes/${encodeURIComponent(quizId)}/questions/order`, { ids })
  },

  // Lich su lam bai
  listAttempts(quizId) {
    return api.get(`/teacher/quizzes/${encodeURIComponent(quizId)}/attempts`)
  },

  deleteAttempt(attemptId) {
    return api.delete(`/teacher/attempts/${encodeURIComponent(attemptId)}`)
  },

  deleteAllAttempts(quizId) {
    return api.delete(`/teacher/quizzes/${encodeURIComponent(quizId)}/attempts`)
  },

  // Thong ke
  getStats(quizId) {
    return api.get(`/teacher/quizzes/${encodeURIComponent(quizId)}/stats`)
  },

  // Xuat ket qua
  exportResults(quizId, format) {
    return api.get(`/teacher/quizzes/${encodeURIComponent(quizId)}/export`, {
      params: { format },
      responseType: 'blob',
    })
  },

  // Thong thuong (goi co header Authorization tu interceptor)
  downloadFile(url, filename) {
    return api.get(url, { responseType: 'blob' }).then((res) => {
      downloadBlob(res, filename)
    })
  },

  // Tai file sample
  downloadImportTemplate() {
    return api.get('/teacher/import-template', { responseType: 'blob' }).then((res) => {
      downloadBlob(res, 'mau_nhap_cau_hoi.xlsx')
    })
  },

  // Nhap CSV/Excel
  importQuestions(quizId, file) {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/teacher/quizzes/${encodeURIComponent(quizId)}/import`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // Tai anh
  uploadImage(file) {
    const form = new FormData()
    form.append('file', file)
    return api.post('/teacher/uploads', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // Thu vien
  listLibrary(params) {
    return api.get('/teacher/library', { params })
  },

  getLibraryQuiz(quizId) {
    return api.get(`/teacher/library/${encodeURIComponent(quizId)}`)
  },

  cloneQuiz(quizId) {
    return api.post(`/teacher/library/${encodeURIComponent(quizId)}/clone`)
  },

  // Sinh ma moi
  regenerateCode(quizId) {
    return api.post(`/teacher/quizzes/${encodeURIComponent(quizId)}/regenerate-code`)
  },

  // Xoa tat ca cua bo de (dung cho nut xoa ket qua de chinh sua)
  deleteQuizAttempts(quizId) {
    return api.delete(`/teacher/quizzes/${encodeURIComponent(quizId)}/attempts`)
  },
}