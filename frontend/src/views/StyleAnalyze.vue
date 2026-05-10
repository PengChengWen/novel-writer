<template>
  <div class="page-container">
    <div class="page-header">
      <h2>🔍 风格分析</h2>
      <el-button @click="router.push('/')">返回仪表盘</el-button>
    </div>

    <el-row :gutter="24">
      <!-- 左侧：上传参考文本 -->
      <el-col :xs="24" :lg="10">
        <el-card class="section-card">
          <template #header>
            <span>📖 参考小说文本</span>
          </template>

          <el-input
            v-model="referenceText"
            type="textarea"
            :rows="12"
            placeholder="粘贴参考小说的文本内容，建议 5000 字以上以获得更准确的分析结果..."
            class="reference-input"
          />

          <div class="upload-section">
            <el-upload
              :auto-upload="false"
              :show-file-list="false"
              accept=".txt,.md"
              @change="handleFileUpload"
            >
              <el-button>
                <el-icon><Upload /></el-icon>
                上传 .txt 文件
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

          <!-- 分析进度 -->
          <div v-if="analyzing" class="progress-section">
            <el-progress :percentage="analysisProgress" :stroke-width="10" />
            <p class="progress-text">{{ progressText }}</p>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：分析结果 -->
      <el-col :xs="24" :lg="14">
        <el-card class="section-card">
          <template #header>
            <span>📊 分析结果</span>
          </template>

          <!-- 无结果状态 -->
          <el-empty v-if="!result" description="请先上传参考文本并开始分析" />

          <!-- 分析结果 -->
          <div v-else>
            <!-- 雷达图 -->
            <h3 class="result-title">文笔特征雷达图</h3>
            <StyleRadar :data="radarData" />

            <!-- 爽点分布 -->
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

            <!-- 风格指南 -->
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
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { uploadReferenceText, analyzeStyle, getAnalysisResult, getStyleGuide } from '../api'
import { ElMessage } from 'element-plus'
import StyleRadar from '../components/StyleRadar.vue'

const router = useRouter()
const route = useRoute()
const novelId = route.params.id

const referenceText = ref('')
const analyzing = ref(false)
const analysisProgress = ref(0)
const progressText = ref('')
const result = ref(null)
const styleGuide = ref({})

// 雷达图数据
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

// 读取上传文件
const handleFileUpload = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    referenceText.value = e.target.result
  }
  reader.readAsText(file.raw)
}

// 开始分析
const startAnalyze = async () => {
  if (!referenceText.value.trim()) {
    ElMessage.warning('请先输入或上传参考文本')
    return
  }

  analyzing.value = true
  analysisProgress.value = 0
  progressText.value = '正在上传文本...'

  try {
    // 1. 上传文本
    analysisProgress.value = 20
    await uploadReferenceText(novelId, referenceText.value)

    // 2. 触发分析
    progressText.value = '正在进行风格分析...'
    analysisProgress.value = 40
    await analyzeStyle(novelId)

    // 3. 模拟进度（实际可能需要轮询）
    analysisProgress.value = 70
    progressText.value = '正在生成分析报告...'

    // 4. 获取结果
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

// 加载已有结果
const loadExistingResult = async () => {
  try {
    const [analysisRes, guideRes] = await Promise.all([
      getAnalysisResult(novelId),
      getStyleGuide(novelId)
    ])
    if (analysisRes) result.value = analysisRes
    if (guideRes) styleGuide.value = guideRes
  } catch {
    // 没有已有结果，正常
  }
}

onMounted(loadExistingResult)
</script>

<style scoped>
.section-card {
  background: var(--bg-card);
  border-color: var(--border);
  height: 100%;
}

.reference-input :deep(textarea) {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-color: var(--border);
}

.upload-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.analyze-btn {
  width: 100%;
}

.progress-section {
  margin-top: 16px;
}

.progress-text {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
  text-align: center;
}

.result-title {
  font-size: 15px;
  font-weight: 600;
  margin: 20px 0 12px;
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
  margin-bottom: 16px;
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
  margin-top: 4px;
}

.style-guide {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.guide-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.guide-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}
</style>
