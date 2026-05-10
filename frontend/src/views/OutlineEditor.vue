<template>
  <div class="page-container">
    <div class="page-header">
      <h2>📋 大纲编辑器</h2>
      <div class="header-actions">
        <el-button :loading="generating" type="primary" size="small" @click="handleGenerate">
          <el-icon><MagicStick /></el-icon>
          <span class="btn-text">生成大纲</span>
        </el-button>
        <el-button type="success" size="small" :disabled="!outline" @click="handleStartWriting">
          <el-icon><VideoPlay /></el-icon>
          <span class="btn-text">开始写作</span>
        </el-button>
      </div>
    </div>

    <el-empty v-if="!outline" description="暂无大纲">
      <el-button type="primary" :loading="generating" @click="handleGenerate">
        生成大纲
      </el-button>
    </el-empty>

    <template v-else>
      <!-- 总纲概览卡片 -->
      <div class="overview-grid">
        <div class="overview-card" v-if="outline.core_concept">
          <div class="card-label">💡 核心概念</div>
          <div class="card-value">{{ outline.core_concept }}</div>
        </div>
        <div class="overview-card" v-if="outline.ending_type">
          <div class="card-label">🎯 结局类型</div>
          <div class="card-value"><el-tag>{{ outline.ending_type }}</el-tag></div>
        </div>
        <div class="overview-card" v-if="outline.main_conflict">
          <div class="card-label">⚔️ 核心矛盾</div>
          <div class="card-value">{{ outline.main_conflict }}</div>
        </div>
      </div>

      <!-- 主角信息 -->
      <div class="section-card" v-if="outline.main_character">
        <div class="section-title">👤 主角设定</div>
        <div class="character-grid">
          <div class="char-item" v-if="outline.main_character.name">
            <span class="char-label">姓名</span>
            <span class="char-value">{{ outline.main_character.name }}</span>
          </div>
          <div class="char-item" v-if="outline.main_character.background">
            <span class="char-label">背景</span>
            <span class="char-value">{{ outline.main_character.background }}</span>
          </div>
          <div class="char-item" v-if="outline.main_character.ability">
            <span class="char-label">能力</span>
            <span class="char-value">{{ outline.main_character.ability }}</span>
          </div>
          <div class="char-item" v-if="outline.main_character.personality">
            <span class="char-label">性格</span>
            <span class="char-value">{{ outline.main_character.personality }}</span>
          </div>
          <div class="char-item" v-if="outline.main_character.goal">
            <span class="char-label">目标</span>
            <span class="char-value">{{ outline.main_character.goal }}</span>
          </div>
        </div>
      </div>

      <!-- 世界观 & 力量体系 -->
      <div class="two-col">
        <div class="section-card" v-if="outline.world_setting">
          <div class="section-title">🌍 世界观设定</div>
          <div class="section-text">{{ outline.world_setting }}</div>
        </div>
        <div class="section-card" v-if="outline.power_system">
          <div class="section-title">⚡ 力量体系</div>
          <div class="section-text">{{ outline.power_system }}</div>
        </div>
      </div>

      <!-- 卖点执行 -->
      <div class="section-card" v-if="outline.selling_points_execution">
        <div class="section-title">🔥 卖点执行方案</div>
        <div class="section-text" v-html="formatText(outline.selling_points_execution)"></div>
      </div>

      <!-- 卷章结构 -->
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">📚 卷章结构（{{ outline.volumes?.length || 0 }} 卷）</span>
        </div>

        <div class="volume-list">
          <div
            v-for="(vol, vi) in outline.volumes"
            :key="vi"
            class="volume-block"
          >
            <div
              class="volume-header"
              :class="{ expanded: expandedVolumes.includes(vi) }"
              @click="toggleVolume(vi)"
            >
              <span class="volume-num">第{{ vol.volume_number || vi + 1 }}卷</span>
              <span class="volume-title">{{ vol.title }}</span>
              <span class="volume-meta">
                <el-tag size="small" v-if="vol.word_target">{{ (vol.word_target / 10000).toFixed(1) }}万字</el-tag>
                <el-tag size="small" type="info" v-if="vol.key_arc">{{ vol.key_arc }}</el-tag>
              </span>
              <el-icon class="expand-icon"><ArrowDown v-if="!expandedVolumes.includes(vi)" /><ArrowUp v-else /></el-icon>
            </div>
            <div v-if="expandedVolumes.includes(vi)" class="volume-detail">
              <div class="volume-desc" v-if="vol.description">{{ vol.description }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { generateOutline, getOutline, startWriting } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const novelId = route.params.id

const outline = ref(null)
const generating = ref(false)
const expandedVolumes = ref([])

const toggleVolume = (vi) => {
  const idx = expandedVolumes.value.indexOf(vi)
  if (idx === -1) {
    expandedVolumes.value.push(vi)
  } else {
    expandedVolumes.value.splice(idx, 1)
  }
}

const formatText = (text) => {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

const handleGenerate = async () => {
  generating.value = true
  try {
    await generateOutline(novelId)
    ElMessage.success('大纲生成完成！')
    await loadOutline()
  } catch (e) {
    ElMessage.error('生成失败: ' + (e.message || '未知错误'))
  } finally {
    generating.value = false
  }
}

const handleStartWriting = async () => {
  try {
    await ElMessageBox.confirm('确认大纲后将开始 AI 自动写作，是否继续？', '确认', { type: 'info' })
    await startWriting(novelId)
    ElMessage.success('写作任务已启动！')
    router.push(`/novel/${novelId}/chapters`)
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('启动写作失败: ' + (e.message || ''))
  }
}

const loadOutline = async () => {
  try {
    const res = await getOutline(novelId)
    if (!res) return

    const outlines = res.outlines || []
    if (Array.isArray(outlines) && outlines.length > 0) {
      const master = outlines.find(o => o.level === 'master')
      if (master && master.content) {
        let parsed = master.content
        if (typeof parsed === 'string') {
          try { parsed = JSON.parse(parsed) } catch {}
        }
        if (parsed) {
          outline.value = parsed
          return
        }
      }
    }
    // fallback
    if (res.volumes) {
      outline.value = res
    }
  } catch {}
}

onMounted(loadOutline)
</script>

<style scoped>
.header-actions {
  display: flex;
  gap: 8px;
}

.btn-text {
  display: inline;
}

/* 概览网格 */
.overview-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

@media (min-width: 769px) {
  .overview-grid {
    grid-template-columns: 1fr 1fr 1fr;
  }
  .btn-text { display: inline; }
}

@media (max-width: 768px) {
  .btn-text { display: none; }
}

.overview-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
}

.card-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.card-value {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
}

/* 通用卡片 */
.section-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 16px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header .section-title {
  margin-bottom: 0;
}

.section-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  white-space: pre-wrap;
}

/* 主角 */
.character-grid {
  display: grid;
  gap: 12px;
}

.char-item {
  display: flex;
  gap: 12px;
}

.char-label {
  flex-shrink: 0;
  width: 40px;
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
}

.char-value {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 双列 */
.two-col {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

@media (min-width: 769px) {
  .two-col {
    grid-template-columns: 1fr 1fr;
  }
}

/* 卷列表 */
.volume-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.volume-block {
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.volume-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  cursor: pointer;
  transition: background 0.2s;
  -webkit-tap-highlight-color: transparent;
}

.volume-header:hover {
  background: var(--bg-hover);
}

.volume-header:active {
  background: var(--bg-hover);
}

.volume-num {
  font-size: 12px;
  font-weight: 700;
  color: var(--accent);
  flex-shrink: 0;
}

.volume-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.volume-meta {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.expand-icon {
  color: var(--text-muted);
  flex-shrink: 0;
  font-size: 14px;
}

.volume-detail {
  padding: 0 14px 14px;
  border-top: 1px solid var(--border);
}

.volume-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  padding-top: 10px;
}
</style>
