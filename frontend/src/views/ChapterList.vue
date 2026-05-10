<template>
  <div class="page-container">
    <div class="page-header">
      <h2>📝 章节管理</h2>
      <div class="header-actions">
        <el-button :loading="writingStatus === 'writing'" type="primary" @click="handleContinueWriting">
          <el-icon><VideoPlay /></el-icon>
          {{ writingStatus === 'writing' ? '写作中...' : '继续写作' }}
        </el-button>
        <el-button @click="refreshChapters">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 写作进度总览 -->
    <el-card class="progress-overview" v-if="chapters.length > 0">
      <el-row :gutter="20" align="middle">
        <el-col :span="6">
          <div class="overview-stat">
            <span class="stat-value">{{ chapters.length }}</span>
            <span class="stat-label">总章节</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="overview-stat">
            <span class="stat-value">{{ completedChapters }}</span>
            <span class="stat-label">已完成</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="overview-stat">
            <span class="stat-value">{{ totalWords }}</span>
            <span class="stat-label">总字数</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="overview-stat">
            <span class="stat-value">{{ avgScore }}</span>
            <span class="stat-label">平均质量</span>
          </div>
        </el-col>
      </el-row>
      <el-progress
        :percentage="completionRate"
        :stroke-width="12"
        :color="progressColors"
        class="overview-progress"
      />
    </el-card>

    <!-- 章节列表 -->
    <el-card class="section-card">
      <el-table
        :data="chapters"
        style="width: 100%"
        row-key="id"
        v-loading="loading"
        empty-text="暂无章节"
        @row-click="goToChapter"
      >
        <el-table-column prop="number" label="章节" width="80" align="center">
          <template #default="{ row }">
            <span class="chapter-num">{{ row.number || row.chapter_number || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="title" label="标题" min-width="200">
          <template #default="{ row }">
            <span class="chapter-title">{{ row.title }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="word_count" label="字数" width="100" align="center">
          <template #default="{ row }">
            {{ formatWords(row.word_count || row.wordCount || 0) }}
          </template>
        </el-table-column>

        <el-table-column prop="quality_score" label="质量评分" width="120" align="center">
          <template #default="{ row }">
            <el-rate
              :model-value="(row.quality_score || row.qualityScore || 0) / 20"
              disabled
              show-score
              text-color="#d29922"
              :score-template="(row.quality_score || row.qualityScore || 0).toString()"
            />
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getChapterStatusType(row.status)" size="small">
              {{ getChapterStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" text @click.stop="goToChapter(row)">
              阅读
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
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

// 格式化字数
const formatWords = (num) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return num.toString()
}

// 统计
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

// 章节状态
const statusMap = {
  pending: { label: '待写作', type: 'info' },
  writing: { label: '写作中', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  done: { label: '已完成', type: 'success' },
  error: { label: '失败', type: 'danger' }
}

const getChapterStatusLabel = (s) => statusMap[s]?.label || s || '未知'
const getChapterStatusType = (s) => statusMap[s]?.type || 'info'

// 跳转到章节阅读
const goToChapter = (row) => {
  router.push(`/novel/${novelId}/chapter/${row.id}`)
}

// 刷新章节列表
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

// 继续写作
const handleContinueWriting = async () => {
  try {
    await startWriting(novelId)
    writingStatus.value = 'writing'
    ElMessage.success('写作任务已启动，稍后刷新查看进度')
    // 轮询状态
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
  margin-bottom: 20px;
  background: var(--bg-card);
  border-color: var(--border);
}

.overview-stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: var(--accent);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.overview-progress {
  margin-top: 16px;
}

.section-card {
  background: var(--bg-card);
  border-color: var(--border);
}

.chapter-num {
  font-weight: 600;
  color: var(--accent);
}

.chapter-title {
  cursor: pointer;
  color: var(--text-primary);
}

.chapter-title:hover {
  color: var(--accent);
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 表格深色适配 */
.section-card :deep(.el-table) {
  --el-table-bg-color: var(--bg-card);
  --el-table-tr-bg-color: var(--bg-card);
  --el-table-header-bg-color: var(--bg-secondary);
  --el-table-row-hover-bg-color: var(--bg-hover);
  --el-table-text-color: var(--text-primary);
  --el-table-header-text-color: var(--text-secondary);
  --el-table-border-color: var(--border);
}

.section-card :deep(.el-table__empty-text) {
  color: var(--text-muted);
}
</style>
