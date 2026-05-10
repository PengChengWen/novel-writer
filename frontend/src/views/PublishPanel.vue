<template>
  <div class="page-container">
    <div class="page-header">
      <h2>🚀 发布管理</h2>
    </div>

    <div class="publish-layout">
      <!-- 发布控制 -->
      <div class="publish-left">
        <div class="section-card">
          <div class="section-title">番茄小说发布</div>

          <div class="login-status">
            <div class="status-indicator" :class="{ active: isLoggedIn }"></div>
            <span>{{ isLoggedIn ? '已登录' : '未登录' }}</span>
            <el-button size="small" @click="checkLoginStatus">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>

          <div class="divider"></div>

          <div class="sub-title">待发布章节</div>
          <div v-if="pendingChapters.length === 0" class="empty-hint">
            所有章节已发布，或暂无章节
          </div>
          <div v-else class="pending-list">
            <div v-for="ch in pendingChapters" :key="ch.id" class="pending-item">
              <span class="item-title">{{ ch.title }}</span>
              <span class="item-words">{{ ch.word_count || ch.wordCount || 0 }}字</span>
            </div>
          </div>

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
        </div>
      </div>

      <!-- 发布进度 -->
      <div class="publish-right">
        <div class="section-card">
          <div class="section-title">发布状态与历史</div>

          <div v-if="publishing" class="publish-progress">
            <el-progress :percentage="publishProgress" :stroke-width="10" :color="progressColors" />
            <p class="progress-text">{{ progressMessage }}</p>
          </div>

          <div v-if="publishHistory.length > 0" class="history-list">
            <div
              v-for="(record, idx) in publishHistory"
              :key="idx"
              class="history-item"
              :class="{ success: record.success, fail: !record.success }"
            >
              <div class="history-dot" :class="{ success: record.success }"></div>
              <div class="history-content">
                <div class="history-msg">{{ record.message }}</div>
                <div v-if="record.detail" class="history-detail">{{ record.detail }}</div>
                <div class="history-time">{{ record.time }}</div>
              </div>
            </div>
          </div>

          <el-empty v-if="!publishing && publishHistory.length === 0" description="暂无发布记录" />
        </div>
      </div>
    </div>
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

const loadChapters = async () => {
  try {
    const chapters = await getChapters(novelId)
    pendingChapters.value = chapters.filter(c =>
      (c.status === 'completed' || c.status === 'done') && c.publish_status !== 'published'
    )
  } catch {
    pendingChapters.value = []
  }
}

const handlePublish = async () => {
  publishing.value = true
  publishProgress.value = 0
  progressMessage.value = '准备发布...'

  try {
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

    publishHistory.value.unshift({
      success: true,
      message: `成功发布 ${pendingChapters.value.length} 个章节`,
      detail: result.message || '',
      time: new Date().toLocaleString('zh-CN')
    })

    ElMessage.success('发布成功！')
    loadChapters()
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
.publish-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.sub-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.login-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
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

.divider {
  height: 1px;
  background: var(--border);
  margin: 16px 0;
}

.empty-hint {
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
  padding: 16px 0;
}

.pending-list {
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.pending-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  border-radius: 4px;
  font-size: 13px;
}

.pending-item:active {
  background: var(--bg-hover);
}

.item-title {
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-words {
  font-size: 12px;
  color: var(--text-muted);
  flex-shrink: 0;
  margin-left: 8px;
}

.publish-btn {
  width: 100%;
}

.publish-progress {
  margin-bottom: 16px;
}

.progress-text {
  text-align: center;
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 13px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 6px;
  background: var(--bg-secondary);
}

.history-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--danger);
  flex-shrink: 0;
  margin-top: 6px;
}

.history-dot.success {
  background: var(--success);
}

.history-msg {
  font-size: 13px;
  color: var(--text-primary);
}

.history-detail {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.history-time {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* 桌面端 */
@media (min-width: 769px) {
  .publish-layout {
    flex-direction: row;
  }

  .publish-left {
    width: 40%;
    flex-shrink: 0;
  }

  .publish-right {
    flex: 1;
  }

  .pending-item:hover {
    background: var(--bg-hover);
  }
}
</style>
