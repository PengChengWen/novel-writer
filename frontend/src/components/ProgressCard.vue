<template>
  <div class="progress-card" @click="$emit('click')">
    <div class="card-header">
      <h3 class="card-title">{{ novel.title }}</h3>
      <el-tag :type="statusType" size="small">{{ statusLabel }}</el-tag>
    </div>

    <div class="card-meta">
      <span class="genre">
        <el-icon><Collection /></el-icon>
        {{ novel.genre || '未分类' }}
      </span>
    </div>

    <div class="card-stats">
      <div class="stat">
        <span class="stat-value">{{ formatWords(novel.currentWords || 0) }}</span>
        <span class="stat-label">当前字数</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat">
        <span class="stat-value">{{ formatWords(novel.targetWords || 0) }}</span>
        <span class="stat-label">目标字数</span>
      </div>
    </div>

    <el-progress
      :percentage="progress"
      :color="progressColor"
      :stroke-width="8"
      class="card-progress"
    />

    <div class="card-desc" v-if="novel.description">
      {{ novel.description }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  novel: {
    type: Object,
    required: true
  }
})

defineEmits(['click'])

// 格式化字数
const formatWords = (num) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num.toString()
}

// 进度百分比
const progress = computed(() => {
  const target = props.novel.targetWords || 1
  const current = props.novel.currentWords || 0
  return Math.min(Math.round((current / target) * 100), 100)
})

// 进度条颜色
const progressColor = computed(() => {
  if (progress.value >= 80) return '#3fb950'
  if (progress.value >= 50) return '#58a6ff'
  if (progress.value >= 20) return '#d29922'
  return '#f85149'
})

// 状态映射
const statusMap = {
  created: { label: '已创建', type: 'info' },
  analyzing: { label: '分析中', type: 'warning' },
  analyzed: { label: '已分析', type: '' },
  outlining: { label: '大纲生成中', type: 'warning' },
  outlined: { label: '大纲完成', type: 'success' },
  writing: { label: '写作中', type: 'warning' },
  written: { label: '写作完成', type: 'success' },
  publishing: { label: '发布中', type: 'warning' },
  published: { label: '已发布', type: 'success' }
}

const statusLabel = computed(() => statusMap[props.novel.status]?.label || props.novel.status)
const statusType = computed(() => statusMap[props.novel.status]?.type || 'info')
</script>

<style scoped>
.progress-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.progress-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(88, 166, 255, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.card-meta {
  margin-bottom: 16px;
}

.genre {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.card-stats {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.stat {
  flex: 1;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: var(--accent);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.stat-divider {
  width: 1px;
  height: 30px;
  background: var(--border);
}

.card-progress {
  margin-bottom: 12px;
}

.card-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-top: auto;
}
</style>
