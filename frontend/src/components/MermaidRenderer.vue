<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import mermaid from 'mermaid'

const props = defineProps<{
  chart: string
  className?: string
}>()

const chartId = ref(`mermaid-${Date.now()}`)
const svgContent = ref('')
const hasError = ref(false)

function initMermaid() {
  mermaid.initialize({
    startOnLoad: false,
    theme: 'default',
    securityLevel: 'loose',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    flowchart: {
      curve: 'basis',
      htmlLabels: true,
      useMaxWidth: true
    }
  })
}

async function renderMermaid() {
  if (!props.chart) return

  hasError.value = false

  try {
    const { svg } = await mermaid.render(`${chartId.value}-${Date.now()}`, props.chart)
    svgContent.value = svg
  } catch (err) {
    console.error('Mermaid render error:', err)
    hasError.value = true
    svgContent.value = ''
  }
}

onMounted(async () => {
  initMermaid()
  await nextTick()
  renderMermaid()
})

watch(() => props.chart, async () => {
  await nextTick()
  renderMermaid()
})
</script>

<template>
  <div
    class="mermaid-container"
    :class="className"
  >
    <div v-if="!hasError && svgContent" class="mermaid-chart" v-html="svgContent"></div>
    <div v-else-if="hasError" class="mermaid-error">
      <div class="text-amber-500 text-sm mb-2">⚠️ 思维导图渲染失败</div>
      <div class="text-gray-500 text-sm">原始内容：</div>
      <pre class="mt-2 p-3 bg-gray-100 rounded-lg text-xs text-gray-700 overflow-x-auto">{{ chart }}</pre>
    </div>
    <div v-else class="mermaid-loading">
      <div class="flex items-center justify-center gap-2 text-gray-500">
        <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>正在渲染思维导图...</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mermaid-container {
  width: 100%;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  border: 1px solid #e5e7eb;
  border-radius: 1rem;
  padding: 2rem;
  overflow: auto;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.mermaid-chart {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.mermaid-chart :deep(svg) {
  max-width: 100%;
  height: auto;
}

.mermaid-chart :deep(.node rect) {
  fill: #6366f1;
  stroke: #4f46e5;
  stroke-width: 2px;
  filter: drop-shadow(0 2px 4px rgba(99, 102, 241, 0.3));
}

.mermaid-chart :deep(.node polygon) {
  fill: #8b5cf6;
  stroke: #7c3aed;
  stroke-width: 2px;
  filter: drop-shadow(0 2px 4px rgba(139, 92, 246, 0.3));
}

.mermaid-chart :deep(.node circle) {
  fill: #ec4899;
  stroke: #db2777;
  stroke-width: 2px;
  filter: drop-shadow(0 2px 4px rgba(236, 72, 153, 0.3));
}

.mermaid-chart :deep(.node text) {
  fill: #ffffff;
  font-weight: 500;
  font-size: 14px;
}

.mermaid-chart :deep(.edgePath path) {
  stroke: #6b7280;
  stroke-width: 2px;
  fill: none;
}

.mermaid-chart :deep(.arrowhead) {
  fill: #6b7280;
  stroke: #6b7280;
}

.mermaid-chart :deep(.edgeLabel) {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 2px 8px;
}

.mermaid-error {
  padding: 1rem;
}

.mermaid-loading {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
