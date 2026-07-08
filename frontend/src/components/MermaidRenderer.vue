<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import mermaid from 'mermaid'

interface MindMapNode {
  id: string
  label: string
  depth: number
  children: MindMapNode[]
}

const props = defineProps<{
  chart: string
  className?: string
}>()

const chartId = ref(`mermaid-${Date.now()}`)
const svgContent = ref('')
const hasError = ref(false)

const cleanedChart = computed(() => cleanChartSource(props.chart))
const mindMap = computed(() => parseMindMap(cleanedChart.value))

function cleanChartSource(value: string) {
  let source = value.trim()
  if (!source) return ''

  const fenced = source.match(/```(?:mermaid)?\s*([\s\S]*?)```/i)
  if (fenced?.[1]) source = fenced[1].trim()

  const validStarts = [
    'mindmap',
    'graph ',
    'graph\n',
    'flowchart',
    'sequenceDiagram',
    'classDiagram',
    'stateDiagram',
    'erDiagram',
    'journey',
    'gantt',
    'pie',
    'gitGraph',
  ]
  const lines = source.split(/\r?\n/)
  const startIndex = lines.findIndex(line => validStarts.some(prefix => line.trim().startsWith(prefix)))
  if (startIndex > 0) source = lines.slice(startIndex).join('\n').trim()
  return source
}

function stripNodeSyntax(value: string) {
  return value
    .trim()
    .replace(/^[-*]\s+/, '')
    .replace(/^root\s*/i, '')
    .replace(/^[([]+|[)\]]+$/g, '')
    .replace(/^["']|["']$/g, '')
    .trim()
}

function parseMindMap(source: string): MindMapNode | null {
  const lines = source.split(/\r?\n/).filter(line => line.trim())
  if (!lines.length || !lines[0].trim().startsWith('mindmap')) return null

  const contentLines = lines.slice(1)
  const fallbackRoot: MindMapNode = { id: 'root', label: '思维导图', depth: 0, children: [] }
  const stack: MindMapNode[] = [fallbackRoot]

  contentLines.forEach((line, index) => {
    const label = stripNodeSyntax(line)
    if (!label) return

    const indent = line.match(/^\s*/)?.[0].length || 0
    const depth = Math.max(0, Math.floor(indent / 2) + 1)
    const node: MindMapNode = {
      id: `${index}-${depth}-${label}`,
      label,
      depth,
      children: [],
    }

    while (stack.length > depth) stack.pop()
    const parent = stack[stack.length - 1] || fallbackRoot
    parent.children.push(node)
    stack[depth] = node
  })

  if (fallbackRoot.children.length === 1) {
    const [root] = fallbackRoot.children
    root.depth = 0
    return root
  }
  return fallbackRoot
}

function isMermaidSource(value: string) {
  return /^(graph\s|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|journey|gantt|pie|gitGraph)/.test(value.trim())
}

function initMermaid() {
  mermaid.initialize({
    startOnLoad: false,
    theme: 'default',
    securityLevel: 'loose',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    flowchart: {
      curve: 'basis',
      htmlLabels: true,
      useMaxWidth: true,
    },
  })
}

async function renderMermaid() {
  if (!cleanedChart.value || mindMap.value) {
    svgContent.value = ''
    hasError.value = false
    return
  }

  hasError.value = false
  svgContent.value = ''

  if (!isMermaidSource(cleanedChart.value)) {
    hasError.value = true
    return
  }

  try {
    await mermaid.parse(cleanedChart.value)
    const { svg } = await mermaid.render(`${chartId.value}-${Date.now()}`, cleanedChart.value)
    svgContent.value = svg
  } catch (err) {
    console.error('Mermaid render error:', err)
    hasError.value = true
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
  <div class="diagram-container" :class="className">
    <div v-if="mindMap" class="code-mindmap">
      <div class="mind-node mind-root">
        <span>{{ mindMap.label }}</span>
      </div>
      <div class="mind-branches">
        <div v-for="branch in mindMap.children" :key="branch.id" class="mind-branch">
          <div class="mind-node">
            <span>{{ branch.label }}</span>
          </div>
          <div v-if="branch.children.length" class="mind-children">
            <div v-for="child in branch.children" :key="child.id" class="mind-child">
              <div class="mind-node mind-node-small">
                <span>{{ child.label }}</span>
              </div>
              <div v-if="child.children.length" class="mind-leaves">
                <span v-for="leaf in child.children" :key="leaf.id">{{ leaf.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!hasError && svgContent" class="mermaid-chart" v-html="svgContent"></div>

    <div v-else-if="hasError" class="diagram-error">
      <strong>图表暂时无法渲染</strong>
      <p>模型返回的内容不是完整图表源码，已保留原始内容。</p>
      <pre>{{ cleanedChart || chart }}</pre>
    </div>

    <div v-else class="diagram-loading">
      <span></span>
      正在生成代码图...
    </div>
  </div>
</template>

<style scoped>
.diagram-container {
  width: 100%;
  padding: 22px;
  overflow: auto;
  border: 1px solid #ececec;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 8px 28px rgba(0, 0, 0, .05);
}

.code-mindmap {
  min-width: 680px;
  display: grid;
  grid-template-columns: 180px 1fr;
  align-items: center;
  gap: 34px;
}

.mind-root {
  min-height: 92px;
  font-size: 18px;
}

.mind-branches {
  display: grid;
  gap: 18px;
  position: relative;
}

.mind-branch,
.mind-child {
  position: relative;
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 22px;
  align-items: center;
  animation: branchIn .46s ease both;
}

.mind-branch::before,
.mind-child::before {
  content: "";
  position: absolute;
  left: -26px;
  top: 50%;
  width: 24px;
  height: 1px;
  background: #d6d6d6;
  transform-origin: left center;
  animation: lineGrow .5s ease both;
}

.mind-children {
  display: grid;
  gap: 12px;
}

.mind-leaves {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mind-leaves span {
  padding: 6px 10px;
  border: 1px solid #e6e6e6;
  border-radius: 999px;
  color: #555;
  background: #fafafa;
  font-size: 12px;
  animation: leafIn .35s ease both;
}

.mind-node {
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 14px;
  border: 1px solid #dedede;
  border-radius: 14px;
  color: #222;
  background: linear-gradient(180deg, #fff, #f7f7f7);
  box-shadow: 0 8px 18px rgba(0, 0, 0, .06);
  text-align: center;
  font-weight: 650;
  animation: nodePop .38s ease both;
}

.mind-node-small {
  min-height: 40px;
  color: #333;
  font-size: 13px;
  font-weight: 600;
  box-shadow: none;
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

.mermaid-chart :deep(.node rect),
.mermaid-chart :deep(.node polygon),
.mermaid-chart :deep(.node circle) {
  fill: #f9fafb;
  stroke: #d4d4d4;
  stroke-width: 2px;
}

.mermaid-chart :deep(.node text) {
  fill: #222;
  font-weight: 500;
  font-size: 14px;
}

.mermaid-chart :deep(.edgePath path) {
  stroke: #8a8a8a;
  stroke-width: 2px;
  fill: none;
  stroke-dasharray: 8;
  animation: dashMove 1.6s linear infinite;
}

.diagram-error {
  padding: 1rem;
  color: #5f5f5f;
  border: 1px solid #ececec;
  border-radius: 12px;
  background: #fafafa;
}

.diagram-error strong {
  display: block;
  color: #333;
  font-size: 14px;
}

.diagram-error p {
  margin: 6px 0 10px;
  font-size: 12px;
}

.diagram-error pre {
  max-height: 260px;
  margin: 0;
  padding: 12px;
  overflow: auto;
  border-radius: 10px;
  color: #555;
  background: #fff;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
}

.diagram-loading {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #777;
}

.diagram-loading span {
  width: 18px;
  height: 18px;
  border: 2px solid #ddd;
  border-top-color: #333;
  border-radius: 999px;
  animation: spin .8s linear infinite;
}

@keyframes nodePop {
  from { opacity: 0; transform: translateY(8px) scale(.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes branchIn {
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes leafIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes lineGrow {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}

@keyframes dashMove {
  to { stroke-dashoffset: -32; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
