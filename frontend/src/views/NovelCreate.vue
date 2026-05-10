<template>
  <div class="page-container">
    <div class="page-header">
      <h2>✨ 创建新小说</h2>
      <el-button @click="router.back()">返回</el-button>
    </div>

    <el-card class="form-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        label-position="top"
        size="large"
      >
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12">
            <el-form-item label="书名" prop="title">
              <el-input v-model="form.title" placeholder="请输入书名" maxlength="50" show-word-limit />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12">
            <el-form-item label="题材" prop="genre">
              <el-select v-model="form.genre" placeholder="选择题材" style="width: 100%">
                <el-option
                  v-for="g in genres"
                  :key="g"
                  :label="g"
                  :value="g"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="目标字数" prop="targetWords">
          <el-slider
            v-model="form.targetWords"
            :min="10000"
            :max="5000000"
            :step="10000"
            :format-tooltip="formatWords"
            show-input
          />
          <div class="word-hint">
            约 {{ (form.targetWords / 3000).toFixed(0) }} 章（每章3000字）
          </div>
        </el-form-item>

        <el-form-item label="简介" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="简要描述小说内容..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="风格偏好" prop="stylePreference">
          <el-select
            v-model="form.stylePreference"
            multiple
            placeholder="选择期望的写作风格"
            style="width: 100%"
          >
            <el-option
              v-for="s in styleOptions"
              :key="s"
              :label="s"
              :value="s"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="核心卖点" prop="sellingPoint">
          <el-input
            v-model="form.sellingPoint"
            placeholder="这部小说最吸引读者的点是什么？"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="submitting"
            @click="handleSubmit"
          >
            创建小说，开始风格分析
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { createNovel } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)

// 题材选项
const genres = [
  '玄幻', '仙侠', '都市', '科幻', '历史',
  '悬疑', '言情', '武侠', '奇幻', '末世',
  '游戏', '军事', '灵异', '同人', '轻小说'
]

// 风格选项
const styleOptions = [
  '轻松幽默', '热血爽文', '虐恋情深', '权谋宫斗',
  '升级流', '无敌流', '扮猪吃虎', '系统流',
  '重生复仇', '穿越异界', '种田经营', '探案推理',
  '暗黑风', '文艺风', '快节奏', '慢热型'
]

// 表单数据
const form = reactive({
  title: '',
  genre: '',
  targetWords: 500000,
  description: '',
  stylePreference: [],
  sellingPoint: ''
})

// 表单验证规则
const rules = {
  title: [
    { required: true, message: '请输入书名', trigger: 'blur' },
    { min: 2, max: 50, message: '书名长度 2-50 个字符', trigger: 'blur' }
  ],
  genre: [
    { required: true, message: '请选择题材', trigger: 'change' }
  ],
  targetWords: [
    { required: true, message: '请设置目标字数', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入简介', trigger: 'blur' }
  ]
}

// 格式化字数显示
const formatWords = (val) => {
  if (val >= 10000) return (val / 10000).toFixed(0) + '万字'
  return val + '字'
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const novel = await createNovel({
      ...form,
      currentWords: 0,
      status: 'created'
    })
    localStorage.setItem('currentNovelId', novel.id)
    ElMessage.success('小说创建成功！')
    router.push(`/novel/${novel.id}/style`)
  } catch (e) {
    ElMessage.error('创建失败: ' + (e.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.form-card {
  max-width: 800px;
  background: var(--bg-card);
  border-color: var(--border);
}

.word-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}
</style>
