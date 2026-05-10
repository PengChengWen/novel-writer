<template>
  <div class="page-container">
    <div class="page-header">
      <h2>🔍 风格分析</h2>
    </div>

    <!-- 手机端：上下布局 / 桌面端：左右布局 -->
    <div class="analyze-layout">
      <!-- 左侧：上传参考文本 -->
      <div class="analyze-left">
        <div class="section-card">
          <div class="section-title">📖 参考小说文本</div>

          <el-input
            v-model="referenceText"
            type="textarea"
            :rows="8"
            placeholder="粘贴参考小说的文本内容，建议 5000 字以上..."
            class="reference-input"
          />

          <div class="upload-section">
            <el-upload
              :auto-upload="false"
              :show-file-list="false"
              accept=".txt,.md"
              @change="handleFileUpload"
            >
              <el-button size="small">
                <el-icon><Upload /></el-icon>
                上传 .txt
              </el-button>
            </el-upload>
            <span class="upload-hint">支持 .txt 格式</span>
          </div>

          <el-button
            type="primary"
            size="large"
            :loading="analyzing"
            :disabled="!referenceText.trim()"
            class="analyze-btn"
            @click="startAnalyze"
          >
            {{ analyzing ? '分析中...' : '开始风格分析' }}
          </el-button>

          <div v-if="analyzing" class="progress-section">
            <el-progress :percentage="analysisProgress" :stroke-width="8" />
            <p class="progress-text">{{ progressText }}</p>
          </div>
        </div>
      </div>

      <!-- 右侧：分析结果 -->
      <div class="analyze-right">
        <div class="section-card">
          <div class="section-title">📊 分析结果</div>

          <el-empty v-if="!result" description="请先上传参考文本并开始分析" />

          <div v-else>
            <h3 class="result-title">文笔特征雷达图</h3>
            <StyleRadar :data="radarData" />

            <h3 class="result-title">爽点分布</h3>
            <div v-if="excitementPoints.length > 0" class="excitement-timeline">
              <div
                v-for="(point, idx) in excitementPoints"
                :key="idx"
                class="excitement-point"
              >
                <div class="point-marker"></div>
                <div class="point-content">
                  <span class="point-position">{{ point.position }}%</span>
                  <el-tag size="small" type="warning">{{ point.type }}</el-tag>
                  <span v-if="point.intensity" class="point-intensity">强度 {{ point.intensity }}/10</span>
                  <p class="point-desc">{{ point.description }}</p>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无爽点数据" :image-size="60" />

            <h3 class="result-title">风格指南</h3>
            <div v-if="guideText" class="style-guide-text">
              <div v-for="(section, idx) in guideSections" :key="idx" class="guide-section">
                <h4 class="guide-section-title">{{ section.title }}</h4>
                <div class="guide-section-content" v-html="section.content"></div>
              </div>
            </div>
            <el-empty v-else description="暂无风格指南" :image-size="60" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { uploadReferenceText, analyzeStyle, getAnalysisResult, getStyleGuide } from '../api'
import { ElMessage } from 'element-plus'
import StyleRadar from '../components/StyleRadar.vue'

const route = useRoute()
const novelId = route.params.id

const referenceText = ref('')
const analyzing = ref(false)
const analysisProgress = ref(0)
const progressText = ref('')
const result = ref(null)
const styleGuide = ref({})

// 爽点数据（从 profile.hook_analysis 提取）
const excitementPoints = computed(() => {
  if (!result.value) return []
  const profile = result.value.profile || {}
  const hooks = profile.hook_analysis || []
  if (Array.isArray(hooks)) {
    return hooks.map(h => ({
      position: h.position || 0,
      type: h.type || '未知',
      description: h.description || '',
      intensity: h.intensity || 0,
    }))
  }
  return []
})

// 风格指南文本
const guideText = computed(() => {
  return styleGuide.value?.style_guide || result.value?.style_guide || ''
})

// 将风格指南 Markdown 拆分为段落
const guideSections = computed(() => {
  const text = guideText.value
  if (!text) return []
  const sections = []
  const parts = text.split(/#{2,3}\s+/).filter(Boolean)
  const titles = text.match(/#{2,3}\s+.+/g) || []
  for (let i = 0; i < parts.length; i++) {
    const title = titles[i]?.replace(/^#+\s+/, '') || `段落${i + 1}`
    const content = parts[i].trim().replace(/\n/g, '<br>')
    sections.push({ title, content })
  }
  return sections
})

const radarData = computed(() => {
  if (!result.value) return {}
  const profile = result.value.profile || {}
  const sa = profile.sentence_analysis || {}
  const ta = profile.tone_analysis || {}
  // 从分析结果构造雷达图数据
  const shortRatio = parseFloat(sa.short_sentence_ratio) || 35
  const mediumRatio = parseFloat(sa.medium_sentence_ratio) || 45
  const dialogueRatio = parseFloat((result.value.profile?.dialogue_analysis?.dialogue_char_ratio || '0').replace('%', '')) || 10
  return {
    indicators: [
      { name: '短句风格', max: 100 },
      { name: '中句风格', max: 100 },
      { name: '对话密度', max: 100 },
      { name: '语气基调', max: 100 },
      { name: '词汇丰富度', max: 100 },
      { name: '节奏感', max: 100 },
      { name: '爽点密度', max: 100 }
    ],
    values: [
      shortRatio,
      mediumRatio,
      Math.min(dialogueRatio * 2, 100),
      ta.tone_variety ? ta.tone_variety * 30 : 60,
      (profile.vocabulary_analysis?.vocabulary_richness || 50),
      70,
      excitementPoints.value.length * 15
    ]
  }
})

const handleFileUpload = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => { referenceText.value = e.target.result }
  reader.readAsText(file.raw)
}

const startAnalyze = async () => {
  if (!referenceText.value.trim()) {
    ElMessage.warning('请先输入或上传参考文本')
    return
  }

  analyzing.value = true
  analysisProgress.value = 0
  progressText.value = '正在上传文本...'

  try {
    analysisProgress.value = 20
    await uploadReferenceText(novelId, referenceText.value)

    progressText.value = '正在进行风格分析...'
    analysisProgress.value = 40
    await analyzeStyle(novelId)

    analysisProgress.value = 70
    progressText.value = '正在生成分析报告...'

    const [analysisRes, guideRes] = await Promise.all([
      getAnalysisResult(novelId),
      getStyleGuide(novelId)
    ])

    result.value = analysisRes
    styleGuide.value = guideRes
    analysisProgress.value = 100
    progressText.value = '分析完成！'
    ElMessage.success('风格分析完成')
  } catch (e) {
    ElMessage.error('分析失败: ' + (e.message || '未知错误'))
  } finally {
    analyzing.value = false
  }
}

const loadExistingResult = async () => {
  try {
    const analysisRes = await getAnalysisResult(novelId)
    if (analysisRes) {
      result.value = analysisRes
      // 风格指南在分析结果中
      if (analysisRes.style_guide) {
        styleGuide.value = { style_guide: analysisRes.style_guide }
      }
    }
  } catch {}
}

onMounted(loadExistingResult)
</script>

<style scoped>
.analyze-layout {
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
  margin-bottom: 12px;
  color: var(--text-primary);
}

.reference-input :deep(textarea) {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-color: var(--border);
  font-size: 14px;
}

.upload-section {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 0;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.analyze-btn {
  width: 100%;
}

.progress-section {
  margin-top: 12px;
}

.progress-text {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 6px;
  text-align: center;
}

.result-title {
  font-size: 14px;
  font-weight: 600;
  margin: 16px 0 10px;
  color: var(--text-primary);
}

.result-title:first-child {
  margin-top: 0;
}

.excitement-timeline {
  position: relative;
  padding-left: 20px;
}

.excitement-timeline::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--border);
}

.excitement-point {
  position: relative;
  margin-bottom: 12px;
  padding-left: 16px;
}

.point-marker {
  position: absolute;
  left: -17px;
  top: 4px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
}

.point-position {
  font-size: 12px;
  color: var(--accent);
  font-weight: 600;
}

.point-type {
  font-size: 12px;
  color: var(--warning);
  margin-left: 8px;
}

.point-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.style-guide {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.guide-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.guide-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.point-intensity {
  font-size: 11px;
  color: var(--text-muted);
  margin-left: 8px;
}

.style-guide-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.guide-section {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.guide-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.guide-section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent);
  margin-bottom: 6px;
}

.guide-section-content {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  white-space: pre-wrap;
}

/* 桌面端左右布局 */
@media (min-width: 769px) {
  .analyze-layout {
    flex-direction: row;
  }

  .analyze-left {
    width: 40%;
    flex-shrink: 0;
  }

  .analyze-right {
    flex: 1;
  }

  .section-card {
    height: 100%;
  }
}
</style>
