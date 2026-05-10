<template>
  <div class="page-container">
    <div class="page-header">
      <h2>🚀 发布管理</h2>
    </div>

    <el-row :gutter="24">
      <!-- 左侧：发布控制 -->
      <el-col :xs="24" :lg="10">
        <el-card class="section-card">
          <template #header>
            <span>番茄小说发布</span>
          </template>

          <!-- 登录状态 -->
          <div class="login-status">
            <div class="status-indicator" :class="{ active: isLoggedIn }"></div>
            <span>{{ isLoggedIn ? '已登录番茄小说' : '未登录番茄小说' }}</span>
            <el-button size="small" @click="checkLoginStatus">
              <el-icon><Refresh /></el-icon>
              检查状态
            </el-button>
          </div>

          <el-divider />

          <!-- 待发布章节 -->
          <h3 class="section-title">待发布章节</h3>
          <div v-if="pendingChapters.length === 0" class="empty-hint">
            所有章节已发布，或暂无章节
          </div>
          <div v-else class="pending-list">
            <div
              v-for="ch in pendingChapters"
              :key="ch.id"
              class="pending-item"
            >
              <span class="item-title">{{ ch.title }}</span>
              <span class="item-words">{{ ch.word_count || ch.wordCount || 0 }}字</span>
            </div>
          </div>

          <el-divider />

          <!-- 发布按钮 -->
          <el-button
            type="primary"
            size="large"
            :loading="publishing"
            :disabled="!isLoggedIn || pendingChapters.length === 0"
            class="publish-btn"
            @click="handlePublish"
          >
            {{ publishing ? '发布中...' : '一键发布到番茄小说' }}
          </el-button>
        </el-card>
      </el-col>

      <!-- 右侧：发布进度 -->
      <el-col :xs="24" :lg="14">
        <el-card class="section-card">
          <template #header>
            <span>发布状态与历史</span>
          </template>

          <!-- 发布进度 -->
          <div v-if="publishing" class="publish-progress">
            <el-progress
              :percentage="publishProgress"
              :stroke-width="16"
              :color="progressColors"
            />
            <p class="progress-text">{{ progressMessage }}</p>
          </div>

          <!-- 发布历史 -->
          <div v-if="publishHistory.length > 0">
            <h3 class="section-title">发布记录</h3>
            <el-timeline>
              <el-timeline-item
                v-for="(record, idx) in publishHistory"
                :key="idx"
                :type="record.success ? 'success' : 'danger'"
                :timestamp="record.time"
                placement="top"
              >
                <el-card class="timeline-card" shadow="never">
                  <p>{{ record.message }}</p>
                  <p v-if="record.detail" class="record-detail">{{ record.detail }}</p>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>

          <el-empty v-if="!publishing && publishHistory.length === 0" description="暂无发布记录" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { publishNovel, getPublishStatus, getChapters } from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const novelId = route.params.id

const isLoggedIn = ref(false)
const publishing = ref(false)
const publishProgress = ref(0)
const progressMessage = ref('')
const pendingChapters = ref([])
const publishHistory = ref([])

const progressColors = [
  { color: '#f85149', percentage: 20 },
  { color: '#d29922', percentage: 50 },
  { color: '#58a6ff', percentage: 80 },
  { color: '#3fb950', percentage: 100 }
]

// 检查登录状态
const checkLoginStatus = async () => {
  try {
    const status = await getPublishStatus(novelId)
    isLoggedIn.value = status.logged_in || status.isLoggedIn || false
    if (status.history) publishHistory.value = status.history
    ElMessage.success(isLoggedIn.value ? '已登录' : '未登录')
  } catch {
    isLoggedIn.value = false
    ElMessage.warning('无法获取登录状态')
  }
}

// 加载待发布章节
const loadChapters = async () => {
  try {
    const chapters = await getChapters(novelId)
    // 筛选已完成但未发布的章节
    pendingChapters.value = chapters.filter(c =>
      (c.status === 'completed' || c.status === 'done') &&
      c.publish_status !== 'published'
    )
  } catch {
    pendingChapters.value = []
  }
}

// 发布
const handlePublish = async () => {
  publishing.value = true
  publishProgress.value = 0
  progressMessage.value = '准备发布...'

  try {
    // 模拟进度
    const progressInterval = setInterval(() => {
      if (publishProgress.value < 90) {
        publishProgress.value += Math.random() * 15
        if (publishProgress.value > 30) progressMessage.value = '正在上传章节...'
        if (publishProgress.value > 60) progressMessage.value = '正在提交到番茄小说...'
      }
    }, 1000)

    const result = await publishNovel(novelId)

    clearInterval(progressInterval)
    publishProgress.value = 100
    progressMessage.value = '发布完成！'

    // 添加到历史
    publishHistory.value.unshift({
      success: true,
      message: `成功发布 ${pendingChapters.value.length} 个章节`,
      detail: result.message || '',
      time: new Date().toLocaleString('zh-CN')
    })

    ElMessage.success('发布成功！')
    loadChapters() // 刷新列表
  } catch (e) {
    publishHistory.value.unshift({
      success: false,
      message: '发布失败',
      detail: e.message || '未知错误',
      time: new Date().toLocaleString('zh-CN')
    })
    ElMessage.error('发布失败: ' + (e.message || ''))
  } finally {
    publishing.value = false
  }
}

onMounted(() => {
  checkLoginStatus()
  loadChapters()
})
</script>

<style scoped>
.section-card {
  background: var(--bg-card);
  border-color: var(--border);
}

.login-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--danger);
}

.status-indicator.active {
  background: var(--success);
  box-shadow: 0 0 6px var(--success);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.empty-hint {
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
  padding: 20px 0;
}

.pending-list {
  max-height: 300px;
  overflow-y: auto;
}

.pending-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 4px;
}

.pending-item:hover {
  background: var(--bg-hover);
}

.item-title {
  font-size: 14px;
  color: var(--text-primary);
}

.item-words {
  font-size: 12px;
  color: var(--text-muted);
}

.publish-btn {
  width: 100%;
  margin-top: 12px;
}

.publish-progress {
  margin-bottom: 24px;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.timeline-card {
  background: var(--bg-secondary) !important;
  border-color: var(--border) !important;
}

.timeline-card :deep(.el-card__body) {
  padding: 10px;
}

.record-detail {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}
</style>
