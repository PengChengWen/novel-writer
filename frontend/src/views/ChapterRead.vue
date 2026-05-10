<template>
  <div class="page-container">
    <div class="page-header">
      <h2>📖 {{ chapter?.title || '章节阅读' }}</h2>
      <el-button @click="router.push(`/novel/${novelId}/chapters`)">返回章节列表</el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="10" animated />
    </div>

    <template v-else-if="chapter">
      <!-- 章节元信息 -->
      <el-card class="meta-card">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="meta-item">
              <span class="meta-label">字数</span>
              <span class="meta-value">{{ chapter.word_count || chapter.wordCount || 0 }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="meta-item">
              <span class="meta-label">质量评分</span>
              <span class="meta-value score">{{ chapter.quality_score || chapter.qualityScore || '-' }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="meta-item">
              <span class="meta-label">出场人物</span>
              <span class="meta-value">{{ (chapter.characters || []).join('、') || '-' }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="meta-item">
              <span class="meta-label">状态</span>
              <el-tag :type="statusType" size="small">{{ statusLabel }}</el-tag>
            </div>
          </el-col>
        </el-row>

        <!-- 章节摘要 -->
        <div v-if="chapter.summary" class="chapter-summary">
          <h4>章节摘要</h4>
          <p>{{ chapter.summary }}</p>
        </div>
      </el-card>

      <!-- 章节正文 -->
      <el-card class="content-card">
        <div class="chapter-content">
          <p v-for="(para, idx) in paragraphs" :key="idx" class="paragraph">
            {{ para }}
          </p>
        </div>
      </el-card>

      <!-- 导航按钮 -->
      <div class="nav-buttons">
        <el-button
          :disabled="!prevChapterId"
          @click="goToChapter(prevChapterId)"
        >
          <el-icon><ArrowLeft /></el-icon>
          上一章
        </el-button>
        <el-button
          :disabled="!nextChapterId"
          @click="goToChapter(nextChapterId)"
        >
          下一章
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </template>

    <el-empty v-else description="章节不存在" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getChapter, getChapters } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()

const novelId = computed(() => route.params.novelId)
const chapterId = computed(() => route.params.chapterId)

const chapter = ref(null)
const allChapters = ref([])
const loading = ref(false)

// 正文分段
const paragraphs = computed(() => {
  const content = chapter.value?.content || chapter.value?.text || ''
  return content.split('\n').filter(p => p.trim())
})

// 章节导航
const currentIndex = computed(() =>
  allChapters.value.findIndex(c => String(c.id) === String(chapterId.value))
)

const prevChapterId = computed(() => {
  if (currentIndex.value <= 0) return null
  return allChapters.value[currentIndex.value - 1]?.id
})

const nextChapterId = computed(() => {
  if (currentIndex.value < 0 || currentIndex.value >= allChapters.value.length - 1) return null
  return allChapters.value[currentIndex.value + 1]?.id
})

// 状态
const statusMap = {
  pending: { label: '待写作', type: 'info' },
  writing: { label: '写作中', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  done: { label: '已完成', type: 'success' }
}

const statusLabel = computed(() => statusMap[chapter.value?.status]?.label || chapter.value?.status || '-')
const statusType = computed(() => statusMap[chapter.value?.status]?.type || 'info')

const goToChapter = (id) => {
  if (id) router.push(`/novel/${novelId.value}/chapter/${id}`)
}

const loadChapter = async () => {
  loading.value = true
  try {
    const [ch, chaptersList] = await Promise.all([
      getChapter(chapterId.value),
      getChapters(novelId.value).catch(() => [])
    ])
    chapter.value = ch
    allChapters.value = chaptersList
  } catch (e) {
    ElMessage.error('加载章节失败')
  } finally {
    loading.value = false
  }
}

watch(chapterId, loadChapter)
onMounted(loadChapter)
</script>

<style scoped>
.meta-card {
  margin-bottom: 20px;
  background: var(--bg-card);
  border-color: var(--border);
}

.meta-item {
  text-align: center;
}

.meta-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.meta-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.meta-value.score {
  color: var(--warning);
}

.chapter-summary {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.chapter-summary h4 {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.chapter-summary p {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.8;
}

.content-card {
  background: var(--bg-card);
  border-color: var(--border);
  margin-bottom: 20px;
}

.chapter-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px 0;
}

.paragraph {
  font-size: 16px;
  line-height: 2;
  color: var(--text-primary);
  text-indent: 2em;
  margin-bottom: 12px;
}

.nav-buttons {
  display: flex;
  justify-content: space-between;
  padding: 0 20px 20px;
}

.loading-state {
  padding: 20px;
}
</style>
