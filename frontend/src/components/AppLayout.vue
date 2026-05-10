<template>
  <el-container class="app-layout">
    <!-- 左侧导航栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo" @click="router.push('/')">
        <el-icon :size="28"><EditPen /></el-icon>
        <span v-show="!isCollapse" class="logo-text">AI 小说工坊</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        background-color="#161b22"
        text-color="#8b949e"
        active-text-color="#58a6ff"
        router
      >
        <el-menu-item index="/">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>

        <el-menu-item
          v-if="currentNovelId"
          :index="`/novel/${currentNovelId}/style`"
        >
          <el-icon><DataAnalysis /></el-icon>
          <span>风格分析</span>
        </el-menu-item>

        <el-menu-item
          v-if="currentNovelId"
          :index="`/novel/${currentNovelId}/outline`"
        >
          <el-icon><List /></el-icon>
          <span>大纲编辑</span>
        </el-menu-item>

        <el-menu-item
          v-if="currentNovelId"
          :index="`/novel/${currentNovelId}/chapters`"
        >
          <el-icon><Document /></el-icon>
          <span>章节管理</span>
        </el-menu-item>

        <el-menu-item
          v-if="currentNovelId"
          :index="`/novel/${currentNovelId}/publish`"
        >
          <el-icon><Upload /></el-icon>
          <span>发布管理</span>
        </el-menu-item>
      </el-menu>

      <div class="collapse-btn" @click="isCollapse = !isCollapse">
        <el-icon>
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
      </div>
    </el-aside>

    <!-- 右侧内容区 -->
    <el-container>
      <!-- 顶部栏 -->
      <el-header class="topbar">
        <div class="topbar-left">
          <el-select
            v-if="novels.length > 0"
            v-model="currentNovelId"
            placeholder="选择小说项目"
            clearable
            class="novel-selector"
            @change="onNovelChange"
          >
            <el-option
              v-for="novel in novels"
              :key="novel.id"
              :label="novel.title"
              :value="novel.id"
            />
          </el-select>
        </div>
        <div class="topbar-right">
          <el-button type="primary" @click="router.push('/novel/create')">
            <el-icon><Plus /></el-icon>
            <span>新建小说</span>
          </el-button>
        </div>
      </el-header>

      <!-- 主内容 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getNovels } from '../api'

const router = useRouter()
const route = useRoute()

const isCollapse = ref(false)
const novels = ref([])
const currentNovelId = ref(localStorage.getItem('currentNovelId') || '')

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 加载小说列表
const loadNovels = async () => {
  try {
    novels.value = await getNovels()
    // 如果没有选中的小说且有小说列表，默认选中第一个
    if (!currentNovelId.value && novels.value.length > 0) {
      currentNovelId.value = novels.value[0].id
      localStorage.setItem('currentNovelId', currentNovelId.value)
    }
  } catch (e) {
    console.error('加载小说列表失败:', e)
  }
}

// 切换当前小说
const onNovelChange = (id) => {
  if (id) {
    localStorage.setItem('currentNovelId', id)
  } else {
    localStorage.removeItem('currentNovelId')
  }
  // 如果当前在小说详情页，跳转到仪表盘
  if (route.params.id && route.params.id !== id) {
    router.push('/')
  }
}

// 监听路由变化，刷新小说列表（创建新小说后需要更新）
watch(() => route.path, () => {
  loadNovels()
})

onMounted(() => {
  loadNovels()
})
</script>

<style scoped>
.app-layout {
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background: #161b22;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  cursor: pointer;
  color: var(--accent);
  border-bottom: 1px solid var(--border);
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  white-space: nowrap;
}

.el-menu {
  flex: 1;
  border-right: none;
  overflow-y: auto;
}

.collapse-btn {
  padding: 12px;
  text-align: center;
  cursor: pointer;
  color: var(--text-secondary);
  border-top: 1px solid var(--border);
}

.collapse-btn:hover {
  color: var(--accent);
}

.topbar {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.novel-selector {
  width: 240px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-content {
  background: var(--bg-primary);
  overflow-y: auto;
  padding: 0;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    z-index: 100;
    height: 100vh;
  }

  .novel-selector {
    width: 160px;
  }
}
</style>
