<template>
  <div class="page-container">
    <div class="page-header">
      <h2>📋 大纲编辑器</h2>
      <div class="header-actions">
        <el-button :loading="generating" type="primary" size="small" @click="handleGenerate">
          <el-icon><MagicStick /></el-icon>
          <span class="btn-text">生成大纲</span>
        </el-button>
        <el-button type="success" size="small" :disabled="!outline" @click="handleStartWriting">
          <el-icon><VideoPlay /></el-icon>
          <span class="btn-text">开始写作</span>
        </el-button>
      </div>
    </div>

    <!-- 手机端：Tab 切换 / 桌面端：左右布局 -->
    <div class="outline-layout">
      <!-- 大纲树 -->
      <div class="outline-left">
        <div class="section-card">
          <div class="section-header">
            <span class="section-title">大纲结构</span>
            <el-button size="small" @click="addNode(null)">
              <el-icon><Plus /></el-icon>添加卷
            </el-button>
          </div>

          <div v-if="outline" class="tree-container">
            <div v-for="(vol, vi) in treeData" :key="vol.id" class="tree-volume">
              <div
                class="tree-node volume-node"
                :class="{ active: selectedNode?.id === vol.id }"
                @click="selectNode(vol)"
              >
                <span class="node-label">{{ vol.label }}</span>
                <span class="node-actions">
                  <el-button size="small" text @click.stop="addNode(vol)">
                    <el-icon><Plus /></el-icon>
                  </el-button>
                  <el-button size="small" text type="danger" @click.stop="removeNode(vol)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </span>
              </div>
              <div class="tree-children">
                <div
                  v-for="ch in vol.children"
                  :key="ch.id"
                  class="tree-node chapter-node"
                  :class="{ active: selectedNode?.id === ch.id }"
                  @click="selectNode(ch)"
                >
                  <span class="node-label">{{ ch.label }}</span>
                  <el-button size="small" text type="danger" @click.stop="removeNode(ch)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <el-empty v-else description="暂无大纲">
            <el-button type="primary" :loading="generating" @click="handleGenerate">
              生成大纲
            </el-button>
          </el-empty>
        </div>
      </div>

      <!-- 节点编辑 -->
      <div class="outline-right">
        <div class="section-card">
          <div class="section-title">{{ selectedNode ? '编辑节点' : '选择节点进行编辑' }}</div>

          <div v-if="selectedNode" class="node-editor">
            <el-form label-position="top" size="large">
              <el-form-item label="标题">
                <el-input v-model="selectedNode.label" />
              </el-form-item>
              <el-form-item label="内容摘要">
                <el-input
                  v-model="selectedNode.summary"
                  type="textarea"
                  :rows="4"
                  placeholder="描述这一部分的主要内容..."
                />
              </el-form-item>
              <el-form-item label="类型">
                <el-tag>{{ nodeTypeLabel }}</el-tag>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" class="save-btn" @click="saveNode">保存修改</el-button>
              </el-form-item>
            </el-form>
          </div>

          <el-empty v-else description="从左侧选择一个节点" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { generateOutline, getOutline, startWriting } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const novelId = route.params.id

const outline = ref(null)
const generating = ref(false)
const selectedNode = ref(null)

const treeData = computed(() => {
  if (!outline.value) return []
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

const selectNode = (data) => {
  selectedNode.value = { ...data }
}

const addNode = (parent) => {
  ElMessageBox.prompt('请输入标题', '添加节点', {
    confirmButtonText: '添加',
    cancelButtonText: '取消',
    inputPlaceholder: '节点标题'
  }).then(({ value }) => {
    if (!value) return
    if (!parent) {
      if (outline.value && outline.value.volumes) {
        outline.value.volumes.push({ title: value, summary: '', chapters: [] })
      }
    } else if (parent.type === 'volume') {
      const vi = treeData.value.findIndex(n => n.id === parent.id)
      if (vi !== -1 && outline.value.volumes[vi]) {
        outline.value.volumes[vi].chapters.push({ title: value, summary: '' })
      }
    }
    ElMessage.success('已添加')
  }).catch(() => {})
}

const removeNode = (data) => {
  ElMessageBox.confirm('确定删除此节点？', '确认', { type: 'warning' }).then(() => {
    if (data.type === 'volume') {
      const vi = treeData.value.findIndex(n => n.id === data.id)
      if (vi !== -1) outline.value.volumes.splice(vi, 1)
    }
    if (selectedNode.value?.id === data.id) selectedNode.value = null
    ElMessage.success('已删除')
  }).catch(() => {})
}

const saveNode = () => {
  if (!selectedNode.value) return
  const findAndUpdate = (nodes, id, updates) => {
    for (const node of nodes) {
      if (node.id === id) { Object.assign(node, updates); return true }
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

const handleGenerate = async () => {
  generating.value = true
  try {
    await generateOutline(novelId)
    ElMessage.success('大纲生成完成！')
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

const handleStartWriting = async () => {
  try {
    await ElMessageBox.confirm('确认大纲后将开始 AI 自动写作，是否继续？', '确认', { type: 'info' })
    await startWriting(novelId)
    ElMessage.success('写作任务已启动！')
    router.push(`/novel/${novelId}/chapters`)
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('启动写作失败: ' + (e.message || ''))
  }
}

const loadOutline = async () => {
  try {
    const res = await getOutline(novelId)
    if (!res) return

    // API 返回 { novel_id, outlines: [{level, content, ...}] }
    // 需要从中提取并转换为 { volumes: [...] } 格式
    const outlines = res.outlines || res
    if (Array.isArray(outlines)) {
      // 找到 master 层级的总纲
      const master = outlines.find(o => o.level === 'master')
      if (master && master.content) {
        let parsed = master.content
        // content 可能是 JSON 字符串
        if (typeof parsed === 'string') {
          try {
            parsed = JSON.parse(parsed)
          } catch {}
        }
        if (parsed && parsed.volumes) {
          outline.value = parsed
          return
        }
      }
      // 尝试从 volume 层级组装
      const volumeOutlines = outlines.filter(o => o.level === 'volume')
      if (volumeOutlines.length > 0) {
        const volumes = volumeOutlines.map(vo => {
          let content = vo.content
          if (typeof content === 'string') {
            try { content = JSON.parse(content) } catch {}
          }
          return {
            title: vo.title || `第${vo.volume_number}卷`,
            summary: content?.volume_title || '',
            chapters: (content?.chapter_outlines || []).map(ch => ({
              title: ch.title || `第${ch.chapter_number}章`,
              summary: ch.summary || '',
            }))
          }
        })
        outline.value = { volumes }
        return
      }
    }
    // fallback: 直接赋值
    outline.value = res
  } catch {}
}

onMounted(loadOutline)
</script>

<style scoped>
.header-actions {
  display: flex;
  gap: 8px;
}

.btn-text {
  display: inline;
}

.outline-layout {
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

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.section-header .section-title {
  margin-bottom: 0;
}

.tree-container {
  max-height: 60vh;
  overflow-y: auto;
}

.tree-volume {
  margin-bottom: 4px;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  -webkit-tap-highlight-color: transparent;
}

.tree-node:active {
  background: var(--bg-hover);
}

.tree-node.active {
  background: var(--bg-hover);
  border-left: 3px solid var(--accent);
}

.volume-node {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.chapter-node {
  padding-left: 28px;
  font-size: 13px;
  color: var(--text-secondary);
}

.node-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-actions {
  flex-shrink: 0;
  opacity: 0.6;
}

.tree-node:hover .node-actions {
  opacity: 1;
}

.node-editor .save-btn {
  width: 100%;
}

/* 桌面端 */
@media (min-width: 769px) {
  .outline-layout {
    flex-direction: row;
  }

  .outline-left {
    width: 40%;
    flex-shrink: 0;
  }

  .outline-right {
    flex: 1;
  }

  .btn-text {
    display: inline;
  }

  .tree-node:hover {
    background: var(--bg-hover);
  }

  .node-actions {
    opacity: 0;
  }

  .tree-node:hover .node-actions {
    opacity: 1;
  }
}

/* 手机端 */
@media (max-width: 768px) {
  .btn-text {
    display: none;
  }
}
</style>
