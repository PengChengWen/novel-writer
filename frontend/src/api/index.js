import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5分钟，AI生成较慢
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.response.use(
  response => response.data,
  error => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

// ========== 小说管理 ==========

export async function getNovels() {
  try {
    const res = await api.get('/analyzer/novels')
    localStorage.setItem('novels', JSON.stringify(res))
    return res
  } catch {
    return JSON.parse(localStorage.getItem('novels') || '[]')
  }
}

export async function createNovel(data) {
  const formData = new FormData()
  formData.append('title', data.title)
  formData.append('genre', data.genre || '玄幻')
  formData.append('description', data.description || '')
  formData.append('target_words', data.targetWords || 300000)

  const res = await api.post('/analyzer/create', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

  const novel = {
    id: res.novel_id,
    ...data,
    currentWords: 0,
    status: 'created',
    createdAt: new Date().toISOString()
  }

  const novels = JSON.parse(localStorage.getItem('novels') || '[]')
  novels.push(novel)
  localStorage.setItem('novels', JSON.stringify(novels))
  return novel
}

export async function getNovel(id) {
  try {
    return await api.get(`/analyzer/novel/${id}`)
  } catch {
    const novels = JSON.parse(localStorage.getItem('novels') || '[]')
    const novel = novels.find(n => String(n.id) === String(id))
    return novel || Promise.reject(new Error('小说不存在'))
  }
}

export function updateNovel(id, data) {
  const novels = JSON.parse(localStorage.getItem('novels') || '[]')
  const idx = novels.findIndex(n => String(n.id) === String(id))
  if (idx === -1) return Promise.reject(new Error('小说不存在'))
  novels[idx] = { ...novels[idx], ...data }
  localStorage.setItem('novels', JSON.stringify(novels))
  return Promise.resolve(novels[idx])
}

// ========== 风格分析 ==========

export function uploadReferenceText(novelId, text) {
  const formData = new FormData()
  formData.append('text', text)
  return api.post(`/analyzer/upload-text/${novelId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function analyzeStyle(novelId) {
  return api.post(`/analyzer/analyze/${novelId}`)
}

export function getAnalysisResult(novelId) {
  return api.get(`/analyzer/result/${novelId}`)
}

// 风格指南包含在分析结果中
export async function getStyleGuide(novelId) {
  const res = await api.get(`/analyzer/result/${novelId}`)
  return { items: [], style_guide: res.style_guide || res.profile?.style_summary || '' }
}

// ========== 大纲 ==========

export function generateOutline(novelId) {
  return api.post('/planner/generate-master', { novel_id: Number(novelId) })
}

export async function getOutline(novelId) {
  try {
    const res = await api.get(`/planner/list/${novelId}`)
    // 返回大纲数据，兼容前端期望的格式
    if (res && res.length > 0) {
      return res[0] // 返回第一个大纲
    }
    return null
  } catch {
    return null
  }
}

export function updateOutline(outlineId, data) {
  // 暂无编辑大纲的后端接口
  return Promise.resolve(data)
}

// ========== 写作 ==========

export async function startWriting(novelId) {
  // 先获取大纲，找到第一章
  const chapters = await api.get(`/writer/chapters/${novelId}`)
  const nextChapter = (chapters.chapters?.length || 0) + 1
  return api.post('/writer/write-chapter-async', {
    novel_id: Number(novelId),
    chapter_number: nextChapter,
    volume_number: 1
  })
}

export function getChapters(novelId) {
  return api.get(`/writer/chapters/${novelId}`).then(res => res.chapters || [])
}

export function getChapter(chapterId) {
  return api.get(`/writer/chapter/${chapterId}`).then(res => res.chapter || res)
}

export async function getWritingStatus(novelId) {
  try {
    const res = await api.get(`/writer/chapters/${novelId}`)
    const chapters = res.chapters || []
    const writing = chapters.some(c => c.status === 'writing')
    return { status: writing ? 'writing' : 'idle', chapters }
  } catch {
    return { status: 'idle', chapters: [] }
  }
}

// ========== 发布 ==========

export function publishNovel(novelId) {
  return api.post('/publisher/publish-batch', {
    novel_id: Number(novelId),
    platform: 'fanqie'
  })
}

export async function getPublishStatus(novelId) {
  try {
    const res = await api.get(`/publisher/publish-logs/${novelId}`)
    return {
      logged_in: true,
      history: (res || []).map(log => ({
        success: log.status === 'success',
        message: `章节 ${log.chapter_id || ''} - ${log.status}`,
        detail: log.error_message || '',
        time: log.published_at || ''
      }))
    }
  } catch {
    return { logged_in: false, history: [] }
  }
}

export default api
