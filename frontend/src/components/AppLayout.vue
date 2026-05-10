<template>
  <div class="app-layout">
    <!-- 桌面端侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: isCollapse }">
      <div class="logo" @click="router.push('/')">
        <el-icon :size="24"><EditPen /></el-icon>
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
        <el-menu-item v-if="currentNovelId" :index="`/novel/${currentNovelId}/style`">
          <el-icon><DataAnalysis /></el-icon>
          <span>风格分析</span>
        </el-menu-item>
        <el-menu-item v-if="currentNovelId" :index="`/novel/${currentNovelId}/outline`">
          <el-icon><List /></el-icon>
          <span>大纲编辑</span>
        </el-menu-item>
        <el-menu-item v-if="currentNovelId" :index="`/novel/${currentNovelId}/chapters`">
          <el-icon><Document /></el-icon>
          <span>章节管理</span>
        </el-menu-item>
        <el-menu-item v-if="currentNovelId" :index="`/novel/${currentNovelId}/publish`">
          <el-icon><Upload /></el-icon>
          <span>发布管理</span>
        </el-menu-item>
      </el-menu>

      <div class="collapse-btn" @click="isCollapse = !isCollapse">
        <el-icon><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-wrapper">
      <!-- 顶部栏（手机端显示） -->
      <header class="topbar">
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
          <span v-else class="topbar-title">AI 小说工坊</span>
        </div>
        <div class="topbar-right">
          <el-button type="primary" size="small" @click="router.push('/novel/create')">
            <el-icon><Plus /></el-icon>
            <span class="btn-text">新建</span>
          </el-button>
        </div>
      </header>

      <!-- 主内容 -->
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- 手机端底部导航栏 -->
    <nav class="bottom-nav">
      <div
        class="nav-item"
        :class="{ active: activeMenu === '/' }"
        @click="router.push('/')"
      >
        <el-icon :size="20"><Odometer /></el-icon>
        <span>仪表盘</span>
      </div>
      <div
        v-if="currentNovelId"
        class="nav-item"
        :class="{ active: activeMenu.includes('/style') }"
        @click="router.push(`/novel/${currentNovelId}/style`)"
      >
        <el-icon :size="20"><DataAnalysis /></el-icon>
        <span>风格</span>
      </div>
      <div
        v-if="currentNovelId"
        class="nav-item"
        :class="{ active: activeMenu.includes('/outline') }"
        @click="router.push(`/novel/${currentNovelId}/outline`)"
      >
        <el-icon :size="20"><List /></el-icon>
        <span>大纲</span>
      </div>
      <div
        v-if="currentNovelId"
        class="nav-item"
        :class="{ active: activeMenu.includes('/chapters') }"
        @click="router.push(`/novel/${currentNovelId}/chapters`)"
      >
        <el-icon :size="20"><Document /></el-icon>
        <span>章节</span>
      </div>
      <div
        v-if="currentNovelId"
        class="nav-item"
        :class="{ active: activeMenu.includes('/publish') }"
        @click="router.push(`/novel/${currentNovelId}/publish`)"
      >
        <el-icon :size="20"><Upload /></el-icon>
        <span>发布</span>
      </div>
    </nav>
  </div>
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

const activeMenu = computed(() => route.path)

const loadNovels = async () => {
  try {
    novels.value = await getNovels()
    if (!currentNovelId.value && novels.value.length > 0) {
      currentNovelId.value = novels.value[0].id
      localStorage.setItem('currentNovelId', currentNovelId.value)
    }
  } catch (e) {
    console.error('加载小说列表失败:', e)
  }
}

const onNovelChange = (id) => {
  if (id) {
    localStorage.setItem('currentNovelId', id)
  } else {
    localStorage.removeItem('currentNovelId')
  }
  if (route.params.id && route.params.id !== String(id)) {
    router.push('/')
  }
}

watch(() => route.path, () => loadNovels())
onMounted(() => loadNovels())
</script>

<style scoped>
.app-layout {
  height: 100vh;
  height: 100dvh;
  display: flex;
  overflow: hidden;
}

/* ===== 桌面端侧边栏 ===== */
.sidebar {
  width: 220px;
  background: #161b22;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 64px;
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
  font-size: 15px;
  font-weight: 700;
  white-space: nowrap;
}

.sidebar .el-menu {
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

/* ===== 主内容区 ===== */
.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.topbar {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 48px;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.topbar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--accent);
}

.novel-selector {
  width: 200px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

/* ===== 底部导航栏（手机端） ===== */
.bottom-nav {
  display: none;
}

/* ===== 手机端适配 ===== */
@media (max-width: 768px) {
  .sidebar {
    display: none;
  }

  .topbar {
    padding: 0 12px;
    height: 44px;
  }

  .novel-selector {
    width: 140px;
  }

  .btn-text {
    display: none;
  }

  .bottom-nav {
    display: flex;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #161b22;
    border-top: 1px solid var(--border);
    z-index: 100;
    padding-bottom: env(safe-area-inset-bottom);
  }

  .nav-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 8px 0;
    gap: 2px;
    color: var(--text-muted);
    font-size: 10px;
    cursor: pointer;
    transition: color 0.2s;
    -webkit-tap-highlight-color: transparent;
  }

  .nav-item.active {
    color: var(--accent);
  }

  .nav-item:active {
    opacity: 0.7;
  }

  .main-content {
    padding-bottom: calc(56px + env(safe-area-inset-bottom));
  }
}

/* ===== 小屏手机 ===== */
@media (max-width: 375px) {
  .novel-selector {
    width: 120px;
  }
}
</style>
