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
            <div class="excitement-timeline">
              <div
                v-for="(point, idx) in result.excitementPoints || []"
                :key="idx"
                class="excitement-point"
              >
                <div class="point-marker"></div>
                <div class="point-content">
                  <span class="point-position">{{ point.position }}%</span>
                  <span class="point-type">{{ point.type }}</span>
                  <p class="point-desc">{{ point.description }}</p>
                </div>
              </div>
            </div>

            <h3 class="result-title">风格指南</h3>
            <div class="style-guide">
              <div
                v-for="(item, idx) in styleGuide.items || []"
                :key="idx"
                class="guide-item"
              >
                <el-tag :type="item.tagType || ''" size="small">{{ item.category }}</el-tag>
                <span class="guide-text">{{ item.content }}</span>
              </div>
            </div>
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

const radarData = computed(() => {
  if (!result.value) return {}
  return {
    indicators: result.value.indicators || [
      { name: '文笔优美度', max: 100 },
      { name: '情节紧凑度', max: 100 },
      { name: '人物塑造', max: 100 },
      { name: '对话质量', max: 100 },
      { name: '世界观设定', max: 100 },
      { name: '节奏把控', max: 100 },
      { name: '爽点密度', max: 100 }
    ],
    values: result.value.values || [60, 70, 65, 55, 50, 72, 68]
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
    const [analysisRes, guideRes] = await Promise.all([
      getAnalysisResult(novelId),
      getStyleGuide(novelId)
    ])
    if (analysisRes) result.value = analysisRes
    if (guideRes) styleGuide.value = guideRes
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
