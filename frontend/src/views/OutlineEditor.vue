<template>
  <div class="page-container">
    <div class="page-header">
      <h2>📋 大纲编辑器</h2>
      <div class="header-actions">
        <el-button :loading="generating" type="primary" @click="handleGenerate">
          <el-icon><MagicStick /></el-icon>
          生成大纲
        </el-button>
        <el-button type="success" :disabled="!outline" @click="handleStartWriting">
          <el-icon><VideoPlay /></el-icon>
          确认大纲，开始写作
        </el-button>
      </div>
    </div>

    <el-row :gutter="24">
      <!-- 左侧：大纲树 -->
      <el-col :xs="24" :lg="10">
        <el-card class="section-card tree-card">
          <template #header>
            <div class="card-header-content">
              <span>大纲结构</span>
              <el-button size="small" @click="addNode(null)">
                <el-icon><Plus /></el-icon>添加卷
              </el-button>
            </div>
          </template>

          <el-tree
            v-if="outline"
            :data="treeData"
            node-key="id"
            default-expand-all
            highlight-current
            :expand-on-click-node="false"
            @node-click="selectNode"
          >
            <template #default="{ node, data }">
              <div class="tree-node">
                <span class="node-label">{{ data.label }}</span>
                <span class="node-actions">
                  <el-button size="small" text @click.stop="addNode(data)">
                    <el-icon><Plus /></el-icon>
                  </el-button>
                  <el-button size="small" text type="danger" @click.stop="removeNode(data)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </span>
              </div>
            </template>
          </el-tree>

          <el-empty v-else description="暂无大纲，点击「生成大纲」开始">
            <el-button type="primary" :loading="generating" @click="handleGenerate">
              生成大纲
            </el-button>
          </el-empty>
        </el-card>
      </el-col>

      <!-- 右侧：节点编辑 -->
      <el-col :xs="24" :lg="14">
        <el-card class="section-card">
          <template #header>
            <span>{{ selectedNode ? '编辑节点' : '选择节点进行编辑' }}</span>
          </template>

          <div v-if="selectedNode" class="node-editor">
            <el-form label-position="top" size="large">
              <el-form-item label="标题">
                <el-input v-model="selectedNode.label" />
              </el-form-item>

              <el-form-item label="内容摘要">
                <el-input
                  v-model="selectedNode.summary"
                  type="textarea"
                  :rows="6"
                  placeholder="描述这一部分的主要内容..."
                />
              </el-form-item>

              <el-form-item label="类型">
                <el-tag>{{ nodeTypeLabel }}</el-tag>
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="saveNode">保存修改</el-button>
              </el-form-item>
            </el-form>
          </div>

          <el-empty v-else description="从左侧选择一个节点" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { generateOutline, getOutline, updateOutline, startWriting } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const novelId = route.params.id

const outline = ref(null)
const generating = ref(false)
const selectedNode = ref(null)

// 将大纲转为树形结构
const treeData = computed(() => {
  if (!outline.value) return []

  // 假设大纲结构是 { volumes: [{ title, chapters: [{ title, summary }] }] }
  const data = outline.value
  if (data.volumes) {
    return data.volumes.map((vol, vi) => ({
      id: `vol-${vi}`,
      label: vol.title || `第${vi + 1}卷`,
      summary: vol.summary || '',
      type: 'volume',
      children: (vol.chapters || []).map((ch, ci) => ({
        id: `ch-${vi}-${ci}`,
        label: ch.title || `第${ci + 1}章`,
        summary: ch.summary || '',
        type: 'chapter'
      }))
    }))
  }

  // 兼容简单结构
  return [{
    id: 'root',
    label: data.title || '总纲',
    summary: data.summary || '',
    type: 'outline',
    children: []
  }]
})

const nodeTypeLabel = computed(() => {
  if (!selectedNode.value) return ''
  const map = { outline: '总纲', volume: '分卷', chapter: '章节' }
  return map[selectedNode.value.type] || '节点'
})

// 选择节点
const selectNode = (data) => {
  selectedNode.value = { ...data }
}

// 添加节点
const addNode = (parent) => {
  ElMessageBox.prompt('请输入标题', '添加节点', {
    confirmButtonText: '添加',
    cancelButtonText: '取消',
    inputPlaceholder: '节点标题'
  }).then(({ value }) => {
    if (!value) return
    if (!parent) {
      // 添加卷
      if (outline.value && outline.value.volumes) {
        outline.value.volumes.push({
          title: value,
          summary: '',
          chapters: []
        })
      }
    } else if (parent.type === 'volume') {
      // 在卷下添加章节
      const vi = treeData.value.findIndex(n => n.id === parent.id)
      if (vi !== -1 && outline.value.volumes[vi]) {
        outline.value.volumes[vi].chapters.push({
          title: value,
          summary: ''
        })
      }
    }
    ElMessage.success('已添加')
  }).catch(() => {})
}

// 删除节点
const removeNode = (data) => {
  ElMessageBox.confirm('确定删除此节点？', '确认', {
    type: 'warning'
  }).then(() => {
    if (data.type === 'volume') {
      const vi = treeData.value.findIndex(n => n.id === data.id)
      if (vi !== -1) outline.value.volumes.splice(vi, 1)
    }
    if (selectedNode.value?.id === data.id) selectedNode.value = null
    ElMessage.success('已删除')
  }).catch(() => {})
}

// 保存节点修改
const saveNode = () => {
  if (!selectedNode.value) return
  // 更新树数据（简单实现，实际可更精细）
  const findAndUpdate = (nodes, id, updates) => {
    for (const node of nodes) {
      if (node.id === id) {
        Object.assign(node, updates)
        return true
      }
      if (node.children && findAndUpdate(node.children, id, updates)) return true
    }
    return false
  }
  findAndUpdate(treeData.value, selectedNode.value.id, {
    label: selectedNode.value.label,
    summary: selectedNode.value.summary
  })
  ElMessage.success('已保存')
}

// 生成大纲
const handleGenerate = async () => {
  generating.value = true
  try {
    const res = await generateOutline(novelId)
    outline.value = res
    ElMessage.success('大纲生成完成！')
    // 重新获取大纲
    try {
      const fetched = await getOutline(novelId)
      if (fetched) outline.value = fetched
    } catch {}
  } catch (e) {
    ElMessage.error('生成失败: ' + (e.message || '未知错误'))
  } finally {
    generating.value = false
  }
}

// 确认大纲开始写作
const handleStartWriting = async () => {
  try {
    await ElMessageBox.confirm('确认大纲后将开始 AI 自动写作，是否继续？', '确认', {
      type: 'info'
    })
    await startWriting(novelId)
    ElMessage.success('写作任务已启动！')
    router.push(`/novel/${novelId}/chapters`)
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('启动写作失败: ' + (e.message || '未知错误'))
    }
  }
}

// 加载已有大纲
const loadOutline = async () => {
  try {
    const res = await getOutline(novelId)
    if (res) outline.value = res
  } catch {
    // 没有已有大纲
  }
}

onMounted(loadOutline)
</script>

<style scoped>
.section-card {
  background: var(--bg-card);
  border-color: var(--border);
}

.tree-card :deep(.el-tree) {
  background: transparent;
  color: var(--text-primary);
}

.tree-card :deep(.el-tree-node__content:hover) {
  background: var(--bg-hover);
}

.card-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 8px;
}

.node-label {
  font-size: 14px;
}

.node-actions {
  opacity: 0;
  transition: opacity 0.2s;
}

.tree-node:hover .node-actions {
  opacity: 1;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.node-editor {
  max-width: 600px;
}
</style>
