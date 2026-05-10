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
    <el-empty
      v-else-if="novels.length === 0"
      description="还没有小说项目"
    >
      <el-button type="primary" @click="router.push('/novel/create')">
        创建第一部小说
      </el-button>
    </el-empty>

    <!-- 小说卡片网格 -->
    <el-row v-else :gutter="20">
      <el-col
        v-for="novel in novels"
        :key="novel.id"
        :xs="24"
        :sm="12"
        :lg="8"
        :xl="6"
        class="card-col"
      >
        <ProgressCard :novel="novel" @click="goToNovel(novel.id)" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getNovels } from '../api'
import ProgressCard from '../components/ProgressCard.vue'

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
  localStorage.setItem('currentNovelId', id)
  router.push(`/novel/${id}/style`)
}

onMounted(loadNovels)
</script>

<style scoped>
.card-col {
  margin-bottom: 20px;
}

.loading-state {
  padding: 20px;
}
</style>
