<template>
  <div class="page-container">
    <div class="page-header">
      <h2>📝 章节管理</h2>
      <div class="header-actions">
        <el-button :loading="writingStatus === 'writing'" type="primary" size="small" @click="handleContinueWriting">
          <el-icon><VideoPlay /></el-icon>
          {{ writingStatus === 'writing' ? '写作中...' : '继续写作' }}
        </el-button>
        <el-button size="small" @click="refreshChapters">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 写作进度总览 -->
    <div class="progress-overview" v-if="chapters.length > 0">
      <div class="overview-grid">
        <div class="overview-stat">
          <span class="stat-value">{{ chapters.length }}</span>
          <span class="stat-label">总章节</span>
        </div>
        <div class="overview-stat">
          <span class="stat-value">{{ completedChapters }}</span>
          <span class="stat-label">已完成</span>
        </div>
        <div class="overview-stat">
          <span class="stat-value">{{ totalWords }}</span>
          <span class="stat-label">总字数</span>
        </div>
        <div class="overview-stat">
          <span class="stat-value">{{ avgScore }}</span>
          <span class="stat-label">平均质量</span>
        </div>
      </div>
      <el-progress
        :percentage="completionRate"
        :stroke-width="8"
        :color="progressColors"
        class="overview-progress"
      />
    </div>

    <!-- 章节列表 -->
    <div v-loading="loading" class="chapter-list">
      <el-empty v-if="chapters.length === 0 && !loading" description="暂无章节" />

      <div
        v-for="ch in chapters"
        :key="ch.id"
        class="chapter-card"
        @click="goToChapter(ch)"
      >
        <div class="chapter-main">
          <div class="chapter-row">
            <span class="chapter-num">第{{ ch.number || ch.chapter_number || '?' }}章</span>
            <span class="chapter-title">{{ ch.title }}</span>
          </div>
          <div class="chapter-meta">
            <span class="meta-text">{{ formatWords(ch.word_count || ch.wordCount || 0) }}字</span>
            <span class="meta-score">⭐ {{ ch.quality_score || ch.qualityScore || '-' }}</span>
            <el-tag :type="getChapterStatusType(ch.status)" size="small">
              {{ getChapterStatusLabel(ch.status) }}
            </el-tag>
          </div>
        </div>
        <el-icon class="chapter-arrow"><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getChapters, startWriting, getWritingStatus } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const novelId = route.params.id

const chapters = ref([])
const loading = ref(false)
const writingStatus = ref('idle')

const formatWords = (num) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return num.toString()
}

const completedChapters = computed(() =>
  chapters.value.filter(c => c.status === 'completed' || c.status === 'done').length
)

const totalWords = computed(() => {
  const total = chapters.value.reduce((sum, c) => sum + (c.word_count || c.wordCount || 0), 0)
  return formatWords(total)
})

const avgScore = computed(() => {
  const scored = chapters.value.filter(c => c.quality_score || c.qualityScore)
  if (scored.length === 0) return '-'
  const sum = scored.reduce((s, c) => s + (c.quality_score || c.qualityScore || 0), 0)
  return (sum / scored.length).toFixed(1)
})

const completionRate = computed(() => {
  if (chapters.value.length === 0) return 0
  return Math.round((completedChapters.value / chapters.value.length) * 100)
})

const progressColors = [
  { color: '#f85149', percentage: 20 },
  { color: '#d29922', percentage: 50 },
  { color: '#58a6ff', percentage: 80 },
  { color: '#3fb950', percentage: 100 }
]

const statusMap = {
  pending: { label: '待写作', type: 'info' },
  writing: { label: '写作中', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  done: { label: '已完成', type: 'success' },
  error: { label: '失败', type: 'danger' }
}

const getChapterStatusLabel = (s) => statusMap[s]?.label || s || '未知'
const getChapterStatusType = (s) => statusMap[s]?.type || 'info'

const goToChapter = (row) => {
  router.push(`/novel/${novelId}/chapter/${row.id}`)
}

const refreshChapters = async () => {
  loading.value = true
  try {
    chapters.value = await getChapters(novelId)
  } catch (e) {
    ElMessage.error('加载章节失败')
  } finally {
    loading.value = false
  }
}

const handleContinueWriting = async () => {
  try {
    await startWriting(novelId)
    writingStatus.value = 'writing'
    ElMessage.success('写作任务已启动，稍后刷新查看进度')
    const poll = setInterval(async () => {
      try {
        const status = await getWritingStatus(novelId)
        if (status.status !== 'writing') {
          clearInterval(poll)
          writingStatus.value = 'idle'
          refreshChapters()
        }
      } catch {
        clearInterval(poll)
        writingStatus.value = 'idle'
      }
    }, 5000)
  } catch (e) {
    ElMessage.error('启动写作失败: ' + (e.message || ''))
  }
}

onMounted(refreshChapters)
</script>

<style scoped>
.progress-overview {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 16px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--accent);
}

.stat-label {
  font-size: 11px;
  color: var(--text-muted);
}

.overview-progress {
  margin-top: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.chapter-list {
  min-height: 200px;
}

.chapter-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  -webkit-tap-highlight-color: transparent;
}

.chapter-card:active {
  transform: scale(0.98);
  border-color: var(--accent);
}

.chapter-main {
  flex: 1;
  min-width: 0;
}

.chapter-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.chapter-num {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  flex-shrink: 0;
}

.chapter-title {
  font-size: 14px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chapter-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--text-muted);
}

.meta-text, .meta-score {
  flex-shrink: 0;
}

.chapter-arrow {
  color: var(--text-muted);
  flex-shrink: 0;
  margin-left: 8px;
}

/* 桌面端 hover */
@media (min-width: 769px) {
  .chapter-card:hover {
    border-color: var(--accent);
    box-shadow: var(--shadow);
  }

  .chapter-card:active {
    transform: none;
  }

  .stat-value {
    font-size: 24px;
  }

  .stat-label {
    font-size: 12px;
  }
}
</style>
