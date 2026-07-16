<script setup lang="ts">
import { computed, nextTick, onBeforeUpdate, onMounted, onUnmounted, ref, watch, getCurrentInstance } from 'vue'
import mermaid from 'mermaid'

interface MindMapNode {
  id: string
  label: string
  depth: number
  children: MindMapNode[]
}

interface MindMapConnection {
  id: string
  color: string
  d: string
}

let mermaidInitialized = false
let renderQueue: Promise<void> = Promise.resolve()

function ensureMermaidInitialized() {
  if (!mermaidInitialized) {
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
    mermaidInitialized = true
  }
}

async function queueMermaidRender(id: string, source: string): Promise<{ svg: string }> {
  return new Promise((resolve, reject) => {
    renderQueue = renderQueue.then(async () => {
      try {
        const result = await mermaid.render(id, source)
        resolve(result)
      } catch (err) {
        reject(err)
      }
    })
  })
}

const props = defineProps<{
  chart: string
  className?: string
}>()

const instance = getCurrentInstance()
const instanceId = instance?.uid ?? Math.random().toString(36).slice(2, 10)
const chartId = ref(`mermaid-${instanceId}`)
const svgContent = ref('')
const hasError = ref(false)
const mindMapEl = ref<HTMLElement | null>(null)
const rootEl = ref<HTMLElement | null>(null)
const branchNodeEls = new Map<string, HTMLElement>()
const connectionPaths = ref<MindMapConnection[]>([])

const cleanedChart = computed(() => cleanChartSource(props.chart))
const mindMap = computed(() => parseMindMap(cleanedChart.value))
const leftBranches = computed(() => mindMap.value?.children.filter((_, index) => index % 2 === 1) || [])
const rightBranches = computed(() => mindMap.value?.children.filter((_, index) => index % 2 === 0) || [])

const branchPalette = ['#75b8d8', '#efc94c', '#78b785', '#d48b71', '#c891c8', '#8fb8e8']

function branchColor(index: number, side: 'left' | 'right') {
  const offset = side === 'left' ? 3 : 0
  return branchPalette[(index + offset) % branchPalette.length]
}

function setBranchNode(el: unknown, id: string) {
  if (el instanceof HTMLElement) branchNodeEls.set(id, el)
}

function branchEntries() {
  return [
    ...leftBranches.value.map((branch, index) => ({ branch, side: 'left' as const, index, color: branchColor(index, 'left') })),
    ...rightBranches.value.map((branch, index) => ({ branch, side: 'right' as const, index, color: branchColor(index, 'right') })),
  ]
}

async function updateMindMapConnections() {
  await nextTick()
  if (!mindMapEl.value || !rootEl.value || !mindMap.value) {
    connectionPaths.value = []
    return
  }

  const canvas = mindMapEl.value.getBoundingClientRect()
  const root = rootEl.value.getBoundingClientRect()
  const rootLeft = root.left - canvas.left
  const rootRight = root.right - canvas.left
  const rootY = root.top - canvas.top + root.height / 2

  connectionPaths.value = branchEntries().flatMap(({ branch, side, color }) => {
    const target = branchNodeEls.get(branch.id)
    if (!target) return []
    const rect = target.getBoundingClientRect()
    const targetY = rect.top - canvas.top + rect.height / 2
    const targetX = side === 'left' ? rect.right - canvas.left : rect.left - canvas.left
    const startX = side === 'left' ? rootLeft : rootRight
    const curve = Math.max(80, Math.abs(targetX - startX) * 0.55)
    const c1x = side === 'left' ? startX - curve : startX + curve
    const c2x = side === 'left' ? targetX + curve : targetX - curve
    return [{
      id: branch.id,
      color,
      d: `M ${startX} ${rootY} C ${c1x} ${rootY}, ${c2x} ${targetY}, ${targetX} ${targetY}`,
    }]
  })
}

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
  ensureMermaidInitialized()
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
    const renderId = `${chartId.value}-${Date.now()}`
    const { svg } = await queueMermaidRender(renderId, cleanedChart.value)
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
  updateMindMapConnections()
  window.addEventListener('resize', updateMindMapConnections)
})

onBeforeUpdate(() => {
  branchNodeEls.clear()
})

onUnmounted(() => {
  window.removeEventListener('resize', updateMindMapConnections)
})

watch(() => props.chart, async () => {
  await nextTick()
  renderMermaid()
  updateMindMapConnections()
})

watch(mindMap, updateMindMapConnections)
</script>

<template>
  <div class="diagram-container" :class="className">
    <div v-if="mindMap" ref="mindMapEl" class="code-mindmap">
      <svg class="mind-connections" aria-hidden="true">
        <path
          v-for="path in connectionPaths"
          :key="path.id"
          :d="path.d"
          :stroke="path.color"
        />
      </svg>

      <div class="mind-side mind-side-left">
        <div
          v-for="(branch, index) in leftBranches"
          :key="branch.id"
          class="mind-branch mind-branch-left"
          :style="{ '--branch-color': branchColor(index, 'left') }"
        >
          <div class="mind-branch-node" :ref="el => setBranchNode(el, branch.id)">
            <span>{{ branch.label }}</span>
          </div>
          <div class="mind-items">
            <div v-for="child in branch.children" :key="child.id" class="mind-item">
              <span>{{ child.label }}</span>
              <small v-for="leaf in child.children" :key="leaf.id">{{ leaf.label }}</small>
            </div>
          </div>
        </div>
      </div>

      <div class="mind-center">
        <div ref="rootEl" class="mind-root">
          {{ mindMap.label }}
        </div>
      </div>

      <div class="mind-side mind-side-right">
        <div
          v-for="(branch, index) in rightBranches"
          :key="branch.id"
          class="mind-branch mind-branch-right"
          :style="{ '--branch-color': branchColor(index, 'right') }"
        >
          <div class="mind-branch-node" :ref="el => setBranchNode(el, branch.id)">
            <span>{{ branch.label }}</span>
          </div>
          <div class="mind-items">
            <div v-for="child in branch.children" :key="child.id" class="mind-item">
              <span>{{ child.label }}</span>
              <small v-for="leaf in child.children" :key="leaf.id">{{ leaf.label }}</small>
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
  position: relative;
  min-width: 1040px;
  min-height: 560px;
  display: grid;
  grid-template-columns: minmax(360px, 1fr) 210px minmax(360px, 1fr);
  align-items: center;
  gap: 32px;
  padding: 36px 8px;
}

.mind-connections {
  position: absolute;
  inset: 0;
  z-index: 1;
  width: 100%;
  height: 100%;
  overflow: visible;
  pointer-events: none;
}

.mind-connections path {
  fill: none;
  stroke-width: 4;
  stroke-linecap: round;
  opacity: .82;
  filter: drop-shadow(0 2px 5px rgba(0, 0, 0, .05));
  stroke-dasharray: 900;
  stroke-dashoffset: 900;
  animation: pathDraw .9s ease forwards;
}

.mind-side {
  position: relative;
  z-index: 2;
  display: grid;
  gap: 24px;
  align-content: center;
}

.mind-side-left {
  justify-items: end;
}

.mind-side-right {
  justify-items: start;
}

.mind-center {
  position: relative;
  z-index: 3;
  display: flex;
  justify-content: center;
  align-items: center;
}

.mind-root {
  position: relative;
  z-index: 2;
  min-width: 160px;
  padding: 18px 24px;
  border: 1px solid #b9d6d7;
  color: #4b6668;
  background: #dceff0;
  box-shadow: 0 8px 20px rgba(78, 130, 132, .12);
  text-align: center;
  font-size: 24px;
  font-weight: 500;
  letter-spacing: 0;
  animation: nodePop .42s ease both;
}

.mind-center::before,
.mind-center::after {
  display: none;
}

.mind-branch {
  --branch-color: #75b8d8;
  position: relative;
  display: flex;
  align-items: center;
  gap: 18px;
  width: min(100%, 430px);
  animation: branchIn .46s ease both;
}

.mind-branch-left {
  flex-direction: row-reverse;
  text-align: right;
}

.mind-branch-right {
  text-align: left;
}

.mind-branch::before {
  display: none;
}

.mind-branch-right::before {
  right: 100%;
  border-left: 4px solid var(--branch-color);
  border-top-left-radius: 38px;
}

.mind-branch-left::before {
  left: 100%;
  border-right: 4px solid var(--branch-color);
  border-top-right-radius: 38px;
}

.mind-branch-node {
  position: relative;
  min-width: 128px;
  padding: 10px 18px;
  border: 1px solid color-mix(in srgb, var(--branch-color) 62%, #ffffff);
  color: #4e5054;
  background: color-mix(in srgb, var(--branch-color) 18%, #ffffff);
  text-align: center;
  font-size: 18px;
  font-weight: 500;
  box-shadow: 0 6px 18px rgba(0, 0, 0, .04);
  animation: nodePop .38s ease both;
}

.mind-branch-node::before {
  content: "";
  position: absolute;
  top: 50%;
  width: 22px;
  height: 3px;
  background: var(--branch-color);
  transform: translateY(-50%);
}

.mind-branch-right .mind-branch-node::before {
  left: -22px;
}

.mind-branch-left .mind-branch-node::before {
  right: -22px;
}

.mind-items {
  display: grid;
  gap: 8px;
  min-width: 180px;
}

.mind-item {
  position: relative;
  display: grid;
  gap: 4px;
  padding-bottom: 5px;
  color: #555f66;
  font-size: 14px;
  line-height: 1.45;
  animation: leafIn .35s ease both;
}

.mind-item::after {
  content: "";
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 3px;
  background: color-mix(in srgb, var(--branch-color) 72%, #ffffff);
  border-radius: 999px;
  transform-origin: left center;
  animation: lineGrow .5s ease both;
}

.mind-branch-left .mind-item::after {
  transform-origin: right center;
}

.mind-item small {
  display: block;
  color: #8a8f94;
  font-size: 12px;
  line-height: 1.4;
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

@keyframes centerLineGrow {
  from { transform: translateY(-50%) scaleX(0); }
  to { transform: translateY(-50%) scaleX(1); }
}

@keyframes pathDraw {
  to { stroke-dashoffset: 0; }
}

@keyframes curveDraw {
  from { opacity: 0; transform: translateY(-50%) scaleX(.2); }
  to { opacity: .86; transform: translateY(-50%) scaleX(1); }
}

@keyframes dashMove {
  to { stroke-dashoffset: -32; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
