<template>
  <div class="style-radar" ref="chartRef"></div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({})
  }
})

const chartRef = ref(null)
let chart = null

// 默认雷达图维度
const defaultIndicators = [
  { name: '文笔优美度', max: 100 },
  { name: '情节紧凑度', max: 100 },
  { name: '人物塑造', max: 100 },
  { name: '对话质量', max: 100 },
  { name: '世界观设定', max: 100 },
  { name: '节奏把控', max: 100 },
  { name: '爽点密度', max: 100 }
]

const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chart) return

  const indicators = props.data.indicators || defaultIndicators
  const values = props.data.values || [60, 70, 65, 55, 50, 72, 68]

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1c2128',
      borderColor: '#30363d',
      textStyle: { color: '#e6edf3' }
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: '#8b949e',
        fontSize: 12
      },
      splitLine: {
        lineStyle: { color: '#30363d' }
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(88, 166, 255, 0.02)', 'rgba(88, 166, 255, 0.05)']
        }
      },
      axisLine: {
        lineStyle: { color: '#30363d' }
      }
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: values,
            name: '文笔特征',
            areaStyle: {
              color: 'rgba(88, 166, 255, 0.2)'
            },
            lineStyle: {
              color: '#58a6ff',
              width: 2
            },
            itemStyle: {
              color: '#58a6ff'
            }
          }
        ]
      }
    ]
  }

  chart.setOption(option)
}

// 监听数据变化
watch(() => props.data, () => {
  nextTick(updateChart)
}, { deep: true })

// 窗口大小变化时重绘
const handleResize = () => {
  chart?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
.style-radar {
  width: 100%;
  height: 360px;
}
</style>
