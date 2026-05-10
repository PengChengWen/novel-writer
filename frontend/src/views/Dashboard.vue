<template>
  <div class="page-container">
    <div class="page-header">
      <h2>📚 我的小说项目</h2>
      <el-button type="primary" @click="router.push('/novel/create')">
        <el-icon><Plus /></el-icon>
        创建新小说
      </el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="novels.length === 0" description="还没有小说项目">
      <el-button type="primary" @click="router.push('/novel/create')">
        创建第一部小说
      </el-button>
    </el-empty>

    <!-- 小说卡片列表 -->
    <div v-else class="novel-grid">
      <div
        v-for="novel in novels"
        :key="novel.id"
        class="novel-card"
        @click="goToNovel(novel.id)"
      >
        <div class="novel-card-header">
          <h3 class="novel-title">{{ novel.title }}</h3>
          <el-tag :type="statusType(novel.status)" size="small">{{ statusText(novel.status) }}</el-tag>
        </div>
        <div class="novel-meta">
          <span class="meta-item">{{ novel.genre || '未分类' }}</span>
          <span class="meta-item">{{ formatWords(novel.target_words || novel.targetWords) }}</span>
        </div>
        <p class="novel-desc">{{ novel.description || '暂无简介' }}</p>
        <div class="novel-footer">
          <span class="novel-date">{{ formatDate(novel.created_at || novel.createdAt) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getNovels } from '../api'

const router = useRouter()
const novels = ref([])
const loading = ref(true)

const loadNovels = async () => {
  loading.value = true
  try {
    novels.value = await getNovels()
  } catch (e) {
    console.error('加载小说列表失败:', e)
  } finally {
    loading.value = false
  }
}

const goToNovel = (id) => {
  localStorage.setItem('currentNovelId', String(id))
  router.push(`/novel/${id}/style`)
}

const statusType = (status) => {
  const map = {
    draft: 'info', created: 'info', uploaded: 'warning',
    analyzing: 'warning', analyzed: 'success',
    writing: 'primary', completed: 'success', published: 'success'
  }
  return map[status] || 'info'
}

const statusText = (status) => {
  const map = {
    draft: '草稿', created: '已创建', uploaded: '已上传',
    analyzing: '分析中', analyzed: '已分析',
    writing: '写作中', completed: '已完成', published: '已发布'
  }
  return map[status] || status || '未知'
}

const formatWords = (val) => {
  if (!val) return '未设置'
  if (val >= 10000) return (val / 10000).toFixed(0) + '万字'
  return val + '字'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

onMounted(loadNovels)
</script>

<style scoped>
.novel-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.novel-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  -webkit-tap-highlight-color: transparent;
}

.novel-card:active {
  transform: scale(0.98);
  border-color: var(--accent);
}

.novel-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.novel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
}

.novel-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.meta-item {
  font-size: 12px;
  color: var(--text-muted);
}

.novel-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
}

.novel-footer {
  display: flex;
  justify-content: flex-end;
}

.novel-date {
  font-size: 11px;
  color: var(--text-muted);
}

.loading-state {
  padding: 16px;
}

/* 桌面端网格布局 */
@media (min-width: 769px) {
  .novel-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }

  .novel-card:hover {
    border-color: var(--accent);
    box-shadow: var(--shadow);
  }

  .novel-card:active {
    transform: none;
  }
}
</style>
