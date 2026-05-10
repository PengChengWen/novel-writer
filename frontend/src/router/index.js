import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'

const routes = [
  {
    path: '/',
    component: AppLayout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'novel/create',
        name: 'NovelCreate',
        component: () => import('../views/NovelCreate.vue'),
        meta: { title: '创建小说' }
      },
      {
        path: 'novel/:id/style',
        name: 'StyleAnalyze',
        component: () => import('../views/StyleAnalyze.vue'),
        meta: { title: '风格分析' }
      },
      {
        path: 'novel/:id/outline',
        name: 'OutlineEditor',
        component: () => import('../views/OutlineEditor.vue'),
        meta: { title: '大纲编辑' }
      },
      {
        path: 'novel/:id/chapters',
        name: 'ChapterList',
        component: () => import('../views/ChapterList.vue'),
        meta: { title: '章节管理' }
      },
      {
        path: 'novel/:novelId/chapter/:chapterId',
        name: 'ChapterRead',
        component: () => import('../views/ChapterRead.vue'),
        meta: { title: '章节阅读' }
      },
      {
        path: 'novel/:id/publish',
        name: 'PublishPanel',
        component: () => import('../views/PublishPanel.vue'),
        meta: { title: '发布管理' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：设置页面标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - AI小说创作工坊` : 'AI小说创作工坊'
  next()
})

export default router
