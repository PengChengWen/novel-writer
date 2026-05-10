import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 Axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2分钟超时，AI 生成可能较慢
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  response => response.data,
  error => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

// ========== 小说管理 ==========

// 获取所有小说项目（从后端获取）
export async function getNovels() {
  try {
    const res = await api.get('/analyzer/novels')
    // 同步到 localStorage 作为缓存
    localStorage.setItem('novels', JSON.stringify(res))
    return res
  } catch {
    // 后端不可用时回退到 localStorage
    const novels = JSON.parse(localStorage.getItem('novels') || '[]')
    return novels
  }
}

// 创建新小说（写入后端数据库）
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
    id: res.novel_id,  // 使用后端返回的 MySQL ID
    ...data,
    currentWords: 0,
    status: 'created',
    createdAt: new Date().toISOString()
  }

  // 同步保存到 localStorage
  const novels = JSON.parse(localStorage.getItem('novels') || '[]')
  novels.push(novel)
  localStorage.setItem('novels', JSON.stringify(novels))

  return novel
}

// 获取单个小说
export async function getNovel(id) {
  try {
    const res = await api.get(`/analyzer/novel/${id}`)
    return res
  } catch {
    const novels = JSON.parse(localStorage.getItem('novels') || '[]')
    const novel = novels.find(n => String(n.id) === String(id))
    return novel ? novel : Promise.reject(new Error('小说不存在'))
  }
}

// 更新小说信息
export function updateNovel(id, data) {
  const novels = JSON.parse(localStorage.getItem('novels') || '[]')
  const idx = novels.findIndex(n => String(n.id) === String(id))
  if (idx === -1) return Promise.reject(new Error('小说不存在'))
  novels[idx] = { ...novels[idx], ...data }
  localStorage.setItem('novels', JSON.stringify(novels))
  return Promise.resolve(novels[idx])
}

// ========== 风格分析 ==========

// 上传参考文本（向已有小说上传文本）
export function uploadReferenceText(novelId, text) {
  const formData = new FormData()
  formData.append('text', text)
  return api.post(`/analyzer/upload-text/${novelId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 触发风格分析
export function analyzeStyle(novelId) {
  return api.post(`/analyzer/analyze/${novelId}`)
}

// 获取分析结果
export function getAnalysisResult(novelId) {
  return api.get(`/analyzer/result/${novelId}`)
}

// 获取风格指南
export function getStyleGuide(novelId) {
  return api.get(`/analyzer/style-guide/${novelId}`)
}

// ========== 大纲 ==========

// 生成大纲
export function generateOutline(novelId) {
  return api.post(`/planner/generate/${novelId}`)
}

// 获取大纲
export function getOutline(novelId) {
  return api.get(`/planner/outline/${novelId}`)
}

// 编辑大纲
export function updateOutline(outlineId, data) {
  return api.put(`/planner/outline/${outlineId}`, data)
}

// ========== 写作 ==========

// 开始写作
export function startWriting(novelId) {
  return api.post(`/writer/start/${novelId}`)
}

// 获取章节列表
export function getChapters(novelId) {
  return api.get(`/writer/chapters/${novelId}`)
}

// 获取单章内容
export function getChapter(chapterId) {
  return api.get(`/writer/chapter/${chapterId}`)
}

// 获取写作状态
export function getWritingStatus(novelId) {
  return api.get(`/writer/status/${novelId}`)
}

// ========== 发布 ==========

// 发布到番茄小说
export function publishNovel(novelId) {
  return api.post(`/publisher/publish/${novelId}`)
}

// 获取发布状态
export function getPublishStatus(novelId) {
  return api.get(`/publisher/status/${novelId}`)
}

export default api
