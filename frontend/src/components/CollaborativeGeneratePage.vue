<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import {
  createConversationTitle,
  getConversationHistoryItem,
  saveConversationHistoryItem,
} from '../api/conversationHistory'
import { addMistake, listCategories, listResources, saveGeneratedResource } from '../api/client'
import { loadSiliconFlowConfig, saveSiliconFlowConfig } from '../api/settings'
import { loadUserProfile } from '../api/userProfile'
import type { CollaborativeExerciseItem, CollaborativeLearningRequest, CollaborativeLearningResponse, CollaborativeResourceType, UploadedResource } from '../types'
import MarkdownRenderer from './MarkdownRenderer.vue'
import MermaidRenderer from './MermaidRenderer.vue'

type ResultKey = 'lectureDoc' | 'mindmap' | 'exercises' | 'reading' | 'codeCase' | 'learningPath' | 'review'
type ProcessState = 'running' | 'done'

interface AgentProcessStep {
  id: string
  agent: string
  message: string
  detail: string
  state: ProcessState
}

interface ConversationTurn {
  id: string
  question: string
  resourceTypes: CollaborativeResourceType[]
  result: CollaborativeLearningResponse | null
  streamContent: Record<ResultKey, string>
  thinkingSteps: string[]
  processSteps: AgentProcessStep[]
  processCollapsed: boolean
  processCompleted: boolean
}

interface ComposerModelOption {
  label: string
  model: string
}

interface ComposerModeOption extends ComposerModelOption {
  key: 'smart' | 'fast' | 'balanced' | 'advanced'
}

const props = defineProps<{
  historyId?: string | null
  conversationSeed?: number
}>()

const emit = defineEmits<{
  newConversation: []
}>()

const resourceOptions: {
  key: CollaborativeResourceType | 'chat'
  resultKey: ResultKey | null
  label: string
  description: string
  icon: string
}[] = [
  { key: 'chat', resultKey: null, label: '普通对话', description: '普通问答对话', icon: '◯' },
  { key: 'lecture', resultKey: 'lectureDoc', label: '课程讲解', description: '生成概念、原理和示例讲解', icon: '▣' },
  { key: 'mindmap', resultKey: 'mindmap', label: '思维导图', description: '生成结构化知识导图', icon: '◇' },
  { key: 'exercise', resultKey: 'exercises', label: '练习题', description: '生成分层题目和答案解析', icon: '✓' },
  { key: 'reading', resultKey: 'reading', label: '拓展阅读', description: '生成延伸知识和学习路径', icon: '○' },
  { key: 'code', resultKey: 'codeCase', label: '代码实操', description: '生成可运行代码案例与讲解', icon: '⟨⟩' },
  { key: 'path', resultKey: 'learningPath', label: '学习路线', description: '生成阶段划分和个性化学习路径', icon: '↗' },
]

const modelModes: ComposerModeOption[] = [
  { key: 'smart', label: '智能', model: 'zai-org/GLM-5.2' },
  { key: 'fast', label: '极速', model: 'deepseek-ai/DeepSeek-V4-Flash' },
  { key: 'balanced', label: '均衡', model: 'Pro/deepseek-ai/DeepSeek-V3.2' },
  { key: 'advanced', label: '高级', model: 'deepseek-ai/DeepSeek-V4-Pro' },
]

const composerModels: ComposerModelOption[] = [
  { label: 'DeepSeek-V4-Pro', model: 'deepseek-ai/DeepSeek-V4-Pro' },
  { label: 'DeepSeek-V4-Flash', model: 'deepseek-ai/DeepSeek-V4-Flash' },
  { label: 'DeepSeek-V3.2 Pro', model: 'Pro/deepseek-ai/DeepSeek-V3.2' },
  { label: 'GLM-5.2', model: 'zai-org/GLM-5.2' },
]

const prompt = ref('')
const currentQuestion = ref('')
const conversationTurns = ref<ConversationTurn[]>([])
const currentConversationId = ref('')
const activeTurnId = ref('')
const streamingTurnId = ref('')
const modelConfig = ref(loadSiliconFlowConfig())
const userProfile = ref(loadUserProfile())
const resources = ref<UploadedResource[]>([])
const promptInput = ref<HTMLTextAreaElement | null>(null)
const selectedTypes = ref<CollaborativeResourceType[]>([])
const selectedType = ref<CollaborativeResourceType | 'chat'>('chat')
const selectedFileIds = ref<string[]>([])
const submittedTypes = ref<CollaborativeResourceType[]>([])
const menuOpen = ref(false)
const modelMenuOpen = ref(false)
const modelSubmenuOpen = ref(false)
const loading = ref(false)
const error = ref('')
const result = ref<CollaborativeLearningResponse | null>(null)
const activeTab = ref<ResultKey>('lectureDoc')
const exerciseAnswers = ref<Record<string, string>>({})
const exerciseSubmitted = ref<Record<string, boolean>>({})
const streamContent = ref<Record<ResultKey, string>>({
  lectureDoc: '',
  mindmap: '',
  exercises: '',
  reading: '',
  codeCase: '',
  learningPath: '',
  review: '',
})
const thinkingSteps = ref<string[]>([])
const processSteps = ref<AgentProcessStep[]>([])
const processQueue = ref<AgentProcessStep[]>([])
const processCollapsed = ref(false)
const processCompleted = ref(false)
let processTimer: ReturnType<typeof setTimeout> | null = null
const PROCESS_STEP_DELAY_MS = 460

const emptyStreamContent = (): Record<ResultKey, string> => ({
  lectureDoc: '',
  mindmap: '',
  exercises: '',
  reading: '',
  codeCase: '',
  learningPath: '',
  review: '',
})

const availableTabs = computed(() => [

  ...(!submittedTypes.value.length ? [{ key: 'lectureDoc' as ResultKey, label: '对话回答' }] : []),
  ...resourceOptions
    .filter(item => item.key !== 'chat' && submittedTypes.value.includes(item.key as CollaborativeResourceType))
    .map(item => ({ key: item.resultKey as ResultKey, label: item.label })),
  ...(submittedTypes.value.length ? [{ key: 'review' as ResultKey, label: '审核结果' }] : []),
])

void availableTabs.value

const selectedOptions = computed(() => resourceOptions.filter(item => item.key !== 'chat' && selectedTypes.value.includes(item.key as CollaborativeResourceType)))
const selectedFiles = computed(() => resources.value.filter(item => selectedFileIds.value.includes(item.id)))
const hasStreamingOutput = computed(() => conversationTurns.value.length > 0 || Object.values(streamContent.value).some(Boolean) || thinkingSteps.value.length > 0)
const activeMode = computed(() => modelModes.find(item => item.model === modelConfig.value.model) || modelModes[3])
const activeComposerModel = computed(() => composerModels.find(item => item.model === modelConfig.value.model))
const activeModelLabel = computed(() => activeComposerModel.value?.label || modelConfig.value.model.split('/').pop() || '自定义模型')

function tabsForTurn(turn: ConversationTurn) {
  return [
    ...(!turn.resourceTypes.length ? [{ key: 'lectureDoc' as ResultKey, label: '对话回答' }] : []),
    ...resourceOptions
      .filter(item => item.key !== 'chat' && turn.resourceTypes.includes(item.key as CollaborativeResourceType))
      .map(item => ({ key: item.resultKey as ResultKey, label: item.label })),
    ...(turn.resourceTypes.length ? [{ key: 'review' as ResultKey, label: '审核结果' }] : []),
  ]
}

function contentForTurn(turn: ConversationTurn, key: ResultKey) {
  return turn.streamContent[key] || turn.result?.[key] || ''
}

function exerciseItemsForTurn(turn: ConversationTurn) {
  return turn.result?.exerciseItems || []
}

function uniqueSources(sources: Array<{ id: string; name: string }> | undefined) {
  if (!sources || !sources.length) return []
  const seen = new Set<string>()
  const result: Array<{ id: string; name: string }> = []
  for (const s of sources) {
    if (s.id && !seen.has(s.id)) {
      seen.add(s.id)
      result.push(s)
    } else if (!s.id && !result.some(item => item.name === s.name)) {
      result.push(s)
    }
  }
  return result
}

const saveDialogVisible = ref(false)
const saveTargetTurn = ref<ConversationTurn | null>(null)
const saveResourceName = ref('')
const saveCategory = ref('AI生成')
const saveCategories = ref<Array<{ name: string; count: number }>>([])
const savingResource = ref(false)
const saveSuccess = ref(false)
const saveError = ref('')

const resultTypeLabelMap: Record<string, { label: string; type: string }> = {
  lectureDoc: { label: '讲义', type: 'lecture' },
  mindmap: { label: '思维导图', type: 'mindmap' },
  exercises: { label: '练习题', type: 'markdown' },
  reading: { label: '阅读材料', type: 'reading' },
  codeCase: { label: '代码案例', type: 'markdown' },
  learningPath: { label: '学习路径', type: 'markdown' },
  review: { label: '复习总结', type: 'markdown' },
}

const activeTabLabel = computed(() => resultTypeLabelMap[activeTab.value]?.label || activeTab.value)
const activeTabType = computed(() => resultTypeLabelMap[activeTab.value]?.type || 'markdown')

async function openSaveDialog(turn: ConversationTurn) {
  saveTargetTurn.value = turn
  saveResourceName.value = `${currentQuestion.value || '学习资料'}-${activeTabLabel.value}`
  saveError.value = ''
  saveSuccess.value = false
  savingResource.value = false
  try {
    const result = await listCategories(userProfile.value.userId)
    saveCategories.value = result.categories || []
    if (!saveCategories.value.some(c => c.name === 'AI生成')) {
      saveCategory.value = saveCategories.value[0]?.name || 'AI生成'
    } else {
      saveCategory.value = 'AI生成'
    }
  } catch {
    saveCategories.value = []
  }
  saveDialogVisible.value = true
}

function closeSaveDialog() {
  saveDialogVisible.value = false
  saveTargetTurn.value = null
  saveResourceName.value = ''
  saveError.value = ''
  saveSuccess.value = false
}

async function confirmSave() {
  if (!saveTargetTurn.value || !saveResourceName.value.trim()) return
  const content = contentForTurn(saveTargetTurn.value, activeTab.value as ResultKey)
  if (!content.trim()) {
    saveError.value = '当前内容为空，无法保存'
    return
  }
  savingResource.value = true
  saveError.value = ''
  try {
    await saveGeneratedResource({
      user_id: userProfile.value.userId,
      name: saveResourceName.value.trim(),
      content: content,
      resource_type: activeTabType.value,
      course_folder: saveCategory.value.trim() || 'AI生成',
    })
    saveSuccess.value = true
    setTimeout(() => {
      closeSaveDialog()
    }, 1200)
  } catch (reason) {
    saveError.value = reason instanceof Error ? reason.message : '保存失败'
  } finally {
    savingResource.value = false
  }
}

function isActiveTurn(turn: ConversationTurn) {
  return turn.id === activeTurnId.value
}

function activeProcessSummary(turn: ConversationTurn) {
  const running = turn.processSteps.find(step => step.state === 'running')
  const last = turn.processSteps[turn.processSteps.length - 1]
  if (running) return `${running.agent}：${running.message}`
  if (turn.processCompleted) return '已完成，点击展开'
  return last ? `${last.agent}：${last.message}` : '处理中'
}

function syncActiveTurn(targetId = streamingTurnId.value || activeTurnId.value) {
  const id = targetId
  if (!id) return
  conversationTurns.value = conversationTurns.value.map(turn => (
    turn.id === id
      ? {
          ...turn,
          result: result.value,
          streamContent: { ...streamContent.value },
          thinkingSteps: [...thinkingSteps.value],
          processSteps: processSteps.value.map(step => ({ ...step })),
          processCollapsed: processCollapsed.value,
          processCompleted: processCompleted.value,
        }
      : turn
  ))
}

function setTurnCollapsed(turnId: string, collapsed: boolean) {
  conversationTurns.value = conversationTurns.value.map(turn => (
    turn.id === turnId ? { ...turn, processCollapsed: collapsed } : turn
  ))
  if (turnId === activeTurnId.value) processCollapsed.value = collapsed
}

function toggleResource(key: CollaborativeResourceType | 'chat') {
  selectedType.value = key
  selectedTypes.value = key === 'chat' ? [] : [key]
}

function removeResource(key: CollaborativeResourceType) {
  selectedTypes.value = selectedTypes.value.filter(item => item !== key)
}

function toggleFile(fileId: string) {
  selectedFileIds.value = selectedFileIds.value.includes(fileId)
    ? selectedFileIds.value.filter(item => item !== fileId)
    : [...selectedFileIds.value, fileId]
}

function selectComposerModel(option: ComposerModelOption) {
  modelConfig.value = { ...modelConfig.value, model: option.model }
  saveSiliconFlowConfig(modelConfig.value)
  modelMenuOpen.value = false
  modelSubmenuOpen.value = false
}

function normalizeAnswer(value: string) {
  return value.trim().replace(/\s+/g, '').toLowerCase()
}

function setExerciseAnswer(questionId: string, answer: string) {
  exerciseAnswers.value = { ...exerciseAnswers.value, [questionId]: answer }
}

function updateExerciseAnswer(questionId: string, event: Event) {
  setExerciseAnswer(questionId, (event.target as HTMLInputElement | HTMLTextAreaElement).value)
}

async function submitExercise(item: CollaborativeExerciseItem) {
  const answer = exerciseAnswers.value[item.id]?.trim()
  if (!answer) return
  exerciseSubmitted.value = { ...exerciseSubmitted.value, [item.id]: true }

  if (!isExerciseCorrect(item)) {
    await saveMistakeToServer(item, answer)
  }
}

async function saveMistakeToServer(item: CollaborativeExerciseItem, studentAnswer: string) {
  try {
    await addMistake({
      user_id: userProfile.value.userId,
      course: currentQuestion.value || '自定义学习',
      question_id: String(item.id),
      question: item.question,
      type: item.type,
      chapter: '综合',
      level: item.level || '',
      options: item.options || null,
      answer: studentAnswer,
      correct_answer: String(item.answer),
      analysis: item.explanation || '',
      topic: item.level || '综合',
    })
  } catch (e) {
    console.error('保存错题失败:', e)
  }
}

function retryExercise(questionId: string) {
  exerciseSubmitted.value = { ...exerciseSubmitted.value, [questionId]: false }
}

async function resizePromptInput() {
  await nextTick()
  const input = promptInput.value
  if (!input) return
  input.style.height = 'auto'
  input.style.height = `${Math.min(input.scrollHeight, 150)}px`
}

function isExerciseCorrect(item: CollaborativeExerciseItem) {
  const selected = normalizeAnswer(exerciseAnswers.value[item.id] || '')
  const expected = normalizeAnswer(item.answer)
  if (item.type === 'single' || item.type === 'judge') {
    return selected === expected || expected.startsWith(selected)
  }
  return selected === expected
}

async function loadUploadedResources() {
  try {
    resources.value = (await listResources(userProfile.value.userId)).resources
  } catch {
    resources.value = []
  }
}

function resetStreamState() {
  streamContent.value = emptyStreamContent()
  thinkingSteps.value = []
  processSteps.value = []
  processQueue.value = []
  processCollapsed.value = false
  processCompleted.value = false
  if (processTimer) {
    clearTimeout(processTimer)
    processTimer = null
  }
}

function resetConversation() {
  persistCurrentConversation()
  prompt.value = ''
  currentQuestion.value = ''
  conversationTurns.value = []
  currentConversationId.value = ''
  activeTurnId.value = ''
  streamingTurnId.value = ''
  result.value = null
  error.value = ''
  submittedTypes.value = []
  activeTab.value = 'lectureDoc'
  exerciseAnswers.value = {}
  exerciseSubmitted.value = {}
  resetStreamState()
  emit('newConversation')
}

function buildHistoryProcessSteps(steps: string[], prefix: string): AgentProcessStep[] {
  return steps.map((step, index) => ({
    id: `${prefix}-${index}`,
    agent: '流程记录',
    message: step,
    detail: '历史对话中的执行记录',
    state: 'done',
  }))
}

function hydrateFromHistory(id: string | null | undefined) {
  if (!id) {
    return
  }
  const item = getConversationHistoryItem(id)
  if (!item) return
  const turns = item.turns?.length
    ? item.turns
    : [{
        id,
        question: item.question,
        resourceTypes: item.resourceTypes,
        result: item.result,
        thinkingSteps: item.thinkingSteps,
      }]
  const lastTurn = turns[turns.length - 1]
  prompt.value = ''
  currentConversationId.value = id
  currentQuestion.value = lastTurn.question
  result.value = lastTurn.result
  submittedTypes.value = [...lastTurn.resourceTypes]
  activeTab.value = resourceOptions.find(option => option.key !== 'chat' && submittedTypes.value.includes(option.key as CollaborativeResourceType))?.resultKey as ResultKey || 'lectureDoc'
  streamContent.value = {
    lectureDoc: lastTurn.result.lectureDoc || '',
    mindmap: lastTurn.result.mindmap || '',
    exercises: lastTurn.result.exercises || '',
    reading: lastTurn.result.reading || '',
    codeCase: lastTurn.result.codeCase || '',
    review: lastTurn.result.review || '',
  }
  thinkingSteps.value = [...lastTurn.thinkingSteps]
  processSteps.value = buildHistoryProcessSteps(lastTurn.thinkingSteps, 'history')
  processCollapsed.value = true
  activeTurnId.value = lastTurn.id
  streamingTurnId.value = ''
  conversationTurns.value = turns.map(turn => ({
    id: turn.id,
    question: turn.question,
    resourceTypes: [...turn.resourceTypes],
    result: turn.result,
    streamContent: {
      lectureDoc: turn.result.lectureDoc || '',
      mindmap: turn.result.mindmap || '',
      exercises: turn.result.exercises || '',
      reading: turn.result.reading || '',
      review: turn.result.review || '',
    },
    thinkingSteps: [...turn.thinkingSteps],
    processSteps: buildHistoryProcessSteps(turn.thinkingSteps, `${turn.id}-history`),
    processCollapsed: true,
    processCompleted: true,
  }))
  exerciseAnswers.value = {}
  exerciseSubmitted.value = {}
  error.value = ''
}

function persistCurrentConversation(fallbackQuestion = '') {
  const id = currentConversationId.value || `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  const turns = conversationTurns.value
    .filter(turn => turn.result)
    .map(turn => ({
      id: turn.id,
      question: turn.question,
      resourceTypes: [...turn.resourceTypes],
      result: turn.result!,
      thinkingSteps: [...turn.thinkingSteps],
    }))
  const latestTurn = turns[turns.length - 1]
  if (!latestTurn) return ''
  currentConversationId.value = id
  saveConversationHistoryItem({
    id,
    title: createConversationTitle(turns[0]?.question || fallbackQuestion),
    question: latestTurn.question,
    createdAt: new Date().toISOString(),
    resourceTypes: [...latestTurn.resourceTypes],
    result: latestTurn.result,
    thinkingSteps: [...latestTurn.thinkingSteps],
    turns,
  })
  return id
}

function saveCompletedConversation(question: string) {
  persistCurrentConversation(question)
}

function buildProcessStep(data: any): AgentProcessStep | null {
  if (!data.message) return null
  return {
    id: `${Date.now()}-${processSteps.value.length}-${processQueue.value.length}`,
    agent: data.agent || '协作调度',
    message: data.message,
    detail: data.detail || '正在推进多 Agent 协作流程',
    state: data.state === 'done' ? 'done' : 'running',
  }
}

function showProcessStep(step: AgentProcessStep) {
  const next = processSteps.value.map(step => (
    step.state === 'running' ? { ...step, state: 'done' as ProcessState } : step
  ))
  const last = next[next.length - 1]
  if (last && last.agent === step.agent && last.message === step.message) {
    processSteps.value = [...next.slice(0, -1), step]
    syncActiveTurn()
    return
  }
  processSteps.value = [...next, step]
  syncActiveTurn()
}

function collapseCompletedProcess() {
  const targetId = streamingTurnId.value || activeTurnId.value
  processSteps.value = processSteps.value.map(step => ({ ...step, state: 'done' }))
  syncActiveTurn(targetId)
  window.setTimeout(() => {
    if (processCompleted.value) {
      processCollapsed.value = true
      syncActiveTurn(targetId)
    }
  }, PROCESS_STEP_DELAY_MS)
}

function pumpProcessQueue() {
  if (processTimer) return
  if (!processQueue.value.length) {
    if (processCompleted.value && processSteps.value.length) collapseCompletedProcess()
    return
  }
  processTimer = window.setTimeout(() => {
    const [step, ...rest] = processQueue.value
    processQueue.value = rest
    if (step) showProcessStep(step)
    processTimer = null
    pumpProcessQueue()
  }, PROCESS_STEP_DELAY_MS)
}

function appendProcessStep(data: any) {
  const step = buildProcessStep(data)
  if (!step) return
  processCollapsed.value = false
  processQueue.value = [...processQueue.value, step]
  syncActiveTurn()
  pumpProcessQueue()
}

function applyStreamEvent(event: string, data: any) {
  if (event === 'status') {
    if (data.message) {
      thinkingSteps.value = [...thinkingSteps.value, data.agent ? `${data.agent}：${data.message}` : data.message]
      appendProcessStep(data)
    }
    return
  }
  if (event === 'content' && data.key && typeof data.text === 'string') {
    const key = data.key as ResultKey
    streamContent.value = { ...streamContent.value, [key]: (streamContent.value[key] || '') + data.text }
    syncActiveTurn()
    return
  }
  if (event === 'done') {
    result.value = data.result
    processCompleted.value = true
    syncActiveTurn()
    pumpProcessQueue()
    return
  }
  if (event === 'error') {
    throw new Error(data.message || '资源生成失败')
  }
}

async function readStream(response: Response) {
  if (!response.body) throw new Error('浏览器不支持流式读取')
  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''
    for (const block of blocks) {
      const lines = block.split('\n')
      const event = lines.find(line => line.startsWith('event: '))?.slice(7).trim() || 'message'
      const dataLine = lines.find(line => line.startsWith('data: '))
      if (!dataLine) continue
      applyStreamEvent(event, JSON.parse(dataLine.slice(6)))
    }
  }
}

async function submit() {
  const question = prompt.value.trim()
  if (!question) {
    error.value = '请输入你想学习的内容'
    return
  }
  const config = { ...modelConfig.value }
  currentQuestion.value = question
  const turnId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  const payload: CollaborativeLearningRequest = {
    user_id: userProfile.value.userId,
    major: '未指定',
    course: '自定义学习主题',
    chapter: '用户当前问题',
    weakness: question,
    goal: '理解并掌握相关知识',
    resourceTypes: [...selectedTypes.value],
    fileIds: [...selectedFileIds.value],
    ...config,
  }

  loading.value = true
  error.value = ''
  result.value = null
  prompt.value = ''
  resetStreamState()
  activeTurnId.value = turnId
  streamingTurnId.value = turnId
  conversationTurns.value = [
    ...conversationTurns.value,
    {
      id: turnId,
      question,
      resourceTypes: [...payload.resourceTypes],
      result: null,
      streamContent: emptyStreamContent(),
      thinkingSteps: [],
      processSteps: [],
      processCollapsed: false,
      processCompleted: false,
    },
  ]
  exerciseAnswers.value = {}
  exerciseSubmitted.value = {}
  menuOpen.value = false
  modelMenuOpen.value = false
  modelSubmenuOpen.value = false
  submittedTypes.value = [...selectedTypes.value]
  activeTab.value = resourceOptions.find(item => item.key !== 'chat' && submittedTypes.value.includes(item.key as CollaborativeResourceType))?.resultKey as ResultKey || 'lectureDoc'

  try {
    const response = await fetch('/api/learning/generate/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const data = await response.json().catch(() => null)
      throw new Error(data?.detail || `请求失败: ${response.status}`)
    }
    await readStream(response)
    saveCompletedConversation(question)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '资源生成失败'
  } finally {
    loading.value = false
    streamingTurnId.value = ''
  }
}

onMounted(() => {
  loadUploadedResources()
  hydrateFromHistory(props.historyId)
  resizePromptInput()
})

watch(() => props.historyId, hydrateFromHistory)
watch(() => props.conversationSeed, () => resetConversation())
watch(prompt, resizePromptInput)
</script>

<template>
  <div :class="['generate-page', { 'has-result': result || loading || hasStreamingOutput, idle: !result && !loading && !hasStreamingOutput }]">
    <section v-if="!conversationTurns.length && !result && !loading" class="empty-state">
      <h2>准备好了，随时开始</h2>
    </section>

    <section v-if="loading && !conversationTurns.length && !hasStreamingOutput" class="generating-state">
      <span class="generating-mark">✦</span>
      <div>
        <strong>正在理解问题</strong>
        <p>正在连接协作 Agent...</p>
      </div>
    </section>

    <section v-if="conversationTurns.length" class="chat-thread">
      <template v-for="turn in conversationTurns" :key="turn.id">
      <article class="chat-message user-message">
        <div class="message-bubble">{{ turn.question }}</div>
      </article>

      <article class="chat-message assistant-message">
        <div class="assistant-body">
          <div v-if="turn.processSteps.length" :class="['thinking-trace', turn.processCollapsed ? 'thinking-trace-collapsed' : '']">
            <div class="trace-head" role="button" tabindex="0" @click="setTurnCollapsed(turn.id, !turn.processCollapsed)">
              <span>处理过程</span>
              <b>
                {{ turn.processCollapsed ? activeProcessSummary(turn) : `${turn.processSteps.filter(step => step.state === 'done').length}/${turn.processSteps.length}` }}
              </b>
            </div>
            <ol v-if="!turn.processCollapsed" class="agent-flow">
              <li
                v-for="step in turn.processSteps"
                :key="step.id"
                :class="['agent-step', `agent-step-${step.state}`]"
              >
                <i></i>
                <div>
                  <strong>{{ step.agent }}</strong>
                  <p>{{ step.message }}</p>
                  <small>{{ step.detail }}</small>
                </div>
              </li>
            </ol>
          </div>

          <div v-if="uniqueSources(turn.result?.sources).length" class="result-sources">
            <span>参考资料</span>
            <b v-for="source in uniqueSources(turn.result?.sources)" :key="source.id">{{ source.name }}</b>
          </div>

          <div v-if="tabsForTurn(turn).length > 1" class="result-tabs">
            <button
              v-for="tab in tabsForTurn(turn)"
              :key="tab.key"
              :class="{ active: isActiveTurn(turn) && activeTab === tab.key }"
              @click="activeTurnId = turn.id; activeTab = tab.key"
            >
              {{ tab.label }}
            </button>
            <button
              v-if="turn.result && isActiveTurn(turn)"
              class="save-to-library-btn"
              title="保存到资料库"
              @click="openSaveDialog(turn)"
            >
              💾 保存到资料库
            </button>
          </div>

          <div class="result-content">
            <template v-if="isActiveTurn(turn)">
              <MermaidRenderer v-if="activeTab === 'mindmap'" :chart="contentForTurn(turn, 'mindmap')" />
              <div v-else-if="activeTab === 'exercises' && exerciseItemsForTurn(turn).length" class="practice-list">
                <article
                  v-for="(item, index) in exerciseItemsForTurn(turn)"
                  :key="item.id"
                  :class="[
                    'practice-card',
                    exerciseSubmitted[item.id] ? (isExerciseCorrect(item) ? 'practice-correct' : 'practice-wrong') : ''
                  ]"
                >
                  <div class="practice-head">
                    <span>{{ item.level }}</span>
                    <b>{{ index + 1 }}</b>
                  </div>
                  <h3>{{ item.question }}</h3>

                  <div v-if="item.type === 'single' || item.type === 'judge'" class="practice-options">
                    <button
                      v-for="option in item.options"
                      :key="option.label"
                      type="button"
                      :class="{ selected: exerciseAnswers[item.id] === option.label }"
                      :disabled="exerciseSubmitted[item.id]"
                      @click="setExerciseAnswer(item.id, option.label)"
                    >
                      <span>{{ option.label }}</span>
                      {{ option.text }}
                    </button>
                  </div>

                  <textarea
                    v-else-if="item.type === 'short'"
                    :value="exerciseAnswers[item.id] || ''"
                    :disabled="exerciseSubmitted[item.id]"
                    rows="3"
                    placeholder="请输入你的答案"
                    @input="updateExerciseAnswer(item.id, $event)"
                  ></textarea>

                  <input
                    v-else
                    :value="exerciseAnswers[item.id] || ''"
                    :disabled="exerciseSubmitted[item.id]"
                    placeholder="请输入答案"
                    @input="updateExerciseAnswer(item.id, $event)"
                  />

                  <div class="practice-actions">
                    <button
                      v-if="!exerciseSubmitted[item.id]"
                      type="button"
                      :disabled="!exerciseAnswers[item.id]?.trim()"
                      @click="submitExercise(item)"
                    >
                      提交答案
                    </button>
                    <button v-else type="button" @click="retryExercise(item.id)">重新作答</button>
                  </div>

                  <div v-if="exerciseSubmitted[item.id]" class="practice-feedback">
                    <strong>{{ isExerciseCorrect(item) ? '回答正确' : '回答错误' }}</strong>
                    <p>正确答案：{{ item.answer }}</p>
                    <p>{{ item.explanation }}</p>
                  </div>
                </article>
              </div>
              <MarkdownRenderer v-else :content="contentForTurn(turn, activeTab)" />
            </template>
            <template v-else>
              <MermaidRenderer
                v-if="contentForTurn(turn, tabsForTurn(turn)[0]?.key || 'lectureDoc') && tabsForTurn(turn)[0]?.key === 'mindmap'"
                :chart="contentForTurn(turn, 'mindmap')"
              />
              <MarkdownRenderer
                v-else
                :content="contentForTurn(turn, tabsForTurn(turn)[0]?.key || 'lectureDoc')"
              />
            </template>
          </div>
        </div>
      </article>
      </template>
    </section>

    <section class="composer-section">
      <div v-if="error" class="composer-error">{{ error }}</div>

      <div class="resource-type-bar">
        <button
          v-for="item in resourceOptions"
          :key="item.key"
          type="button"
          :class="{ active: selectedType === item.key }"
          :disabled="loading"
          @click="toggleResource(item.key)"
        >
          <span class="rt-icon">{{ item.icon }}</span>
          <span class="rt-label">{{ item.label }}</span>
        </button>
      </div>

      <div class="composer">
        <div v-if="selectedFiles.length" class="selected-tools">
          <button
            v-for="file in selectedFiles"
            :key="file.id"
            type="button"
            class="selected-file"
            :disabled="loading"
            @click="toggleFile(file.id)"
          >
            <span>PDF</span>{{ file.name }}<i>×</i>
          </button>
        </div>

        <div class="composer-actions">
          <div class="tool-picker">
            <button
              class="add-button"
              type="button"
              :disabled="loading"
              aria-label="选择生成内容"
              @click="menuOpen = !menuOpen"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 5v14M5 12h14" />
              </svg>
            </button>

            <div v-if="menuOpen" class="tool-menu">
              <div class="menu-title">引用资料库文件</div>
              <div v-if="resources.length" class="file-options">
                <button
                  v-for="file in resources"
                  :key="file.id"
                  type="button"
                  :class="{ selected: selectedFileIds.includes(file.id) }"
                  @click="toggleFile(file.id)"
                >
                  <span class="tool-icon pdf">PDF</span>
                  <span><b>{{ file.name }}</b><small>{{ file.page_count }} 页 · 已解析</small></span>
                  <i>{{ selectedFileIds.includes(file.id) ? '✓' : '' }}</i>
                </button>
              </div>
              <div v-else class="no-files">资料库暂无 PDF，请先上传文件</div>
            </div>
          </div>

          <textarea
            ref="promptInput"
            v-model="prompt"
            rows="1"
            :disabled="loading"
            placeholder="有问题，尽管问"
            @input="resizePromptInput"
            @keydown.enter.exact.prevent="submit"
          ></textarea>

          <div class="model-picker">
            <button
              type="button"
              class="model-button"
              :disabled="loading"
              @click="modelMenuOpen = !modelMenuOpen"
            >
              {{ activeMode.label }}
              <span>⌄</span>
            </button>

            <div v-if="modelMenuOpen" class="model-menu">
              <button
                v-for="mode in modelModes"
                :key="mode.key"
                type="button"
                class="model-menu-item"
                @click="selectComposerModel(mode)"
              >
                <span>{{ mode.label }}</span>
                <b v-if="modelConfig.model === mode.model">✓</b>
              </button>

              <div class="model-menu-divider"></div>

              <button
                type="button"
                class="model-menu-item model-menu-parent"
                @click="modelSubmenuOpen = !modelSubmenuOpen"
              >
                <span>{{ activeModelLabel }}</span>
                <b>›</b>
              </button>

              <div v-if="modelSubmenuOpen" class="model-submenu">
                <button
                  v-for="model in composerModels"
                  :key="model.model"
                  type="button"
                  class="model-menu-item"
                  @click="selectComposerModel(model)"
                >
                  <span>{{ model.label }}</span>
                  <b v-if="modelConfig.model === model.model">✓</b>
                </button>
              </div>
            </div>
          </div>

          <button class="send-button" :disabled="loading || !prompt.trim()" aria-label="发送" @click="submit">
            {{ loading ? '…' : '↑' }}
          </button>
        </div>
      </div>

      <p class="composer-hint">Enter 发送 · Shift + Enter 换行</p>
    </section>

    <Teleport to="body">
      <div v-if="saveDialogVisible" class="save-modal-overlay" @click.self="closeSaveDialog">
        <div class="save-modal">
          <header class="save-modal-header">
            <h3>保存到资料库</h3>
            <button class="save-modal-close" @click="closeSaveDialog">×</button>
          </header>
          <div class="save-modal-body">
            <div v-if="saveSuccess" class="save-success">
              <div class="success-icon">✓</div>
              <p>保存成功！</p>
            </div>
            <template v-else>
              <div class="save-form-group">
                <label>资料名称</label>
                <input v-model.trim="saveResourceName" type="text" placeholder="输入资料名称" />
              </div>
              <div class="save-form-group">
                <label>资料类型</label>
                <div class="save-type-info">{{ activeTabLabel }}</div>
              </div>
              <div class="save-form-group">
                <label>选择分类</label>
                <div class="save-category-list">
                  <button
                    v-for="cat in saveCategories"
                    :key="cat.name"
                    type="button"
                    :class="['save-category-btn', saveCategory === cat.name ? 'active' : '']"
                    @click="saveCategory = cat.name"
                  >
                    {{ cat.name }}
                    <small>{{ cat.count }} 个</small>
                  </button>
                </div>
                <div class="save-new-category">
                  <input
                    v-model.trim="saveCategory"
                    type="text"
                    placeholder="或输入新分类名称..."
                  />
                </div>
              </div>
              <div v-if="saveError" class="save-error">{{ saveError }}</div>
            </template>
          </div>
          <div v-if="!saveSuccess" class="save-modal-footer">
            <button class="save-btn-cancel" @click="closeSaveDialog">取消</button>
            <button
              class="save-btn-confirm"
              :disabled="savingResource || !saveResourceName.trim() || !saveCategory.trim()"
              @click="confirmSave"
            >
              {{ savingResource ? '保存中...' : '确认保存' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.generate-page { display: grid; grid-template-rows: 1fr auto; width: min(980px, 100%); min-height: calc(100vh - 80px); margin: 0 auto; color: #202123; }
.generate-page.idle { grid-template-rows: auto auto; width: min(640px, 100%); align-content: center; gap: 28px; padding-bottom: 8vh; }
.generate-page.has-result { gap: 24px; }
.empty-state { display: grid; place-items: center; padding: 0; }
.empty-state h2 { margin: 0; font-size: clamp(28px, 4vw, 38px); font-weight: 500; letter-spacing: 0; }
.generating-state { display: flex; align-items: center; justify-content: center; gap: 14px; min-height: 320px; }
.generating-mark { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 50%; color: #fff; background: #202123; animation: pulse 1.2s infinite; }
.generating-state strong { font-size: 16px; }
.generating-state p { margin: 5px 0 0; color: #8a8a8a; font-size: 13px; }
.chat-thread { display: grid; gap: 22px; min-height: 320px; padding: 22px 0 132px; }
.chat-message { display: flex; width: 100%; }
.user-message { justify-content: flex-end; }
.message-bubble { max-width: min(78%, 720px); padding: 12px 16px; border-radius: 22px; color: #202123; background: #f0f0f0; line-height: 1.65; white-space: pre-wrap; overflow-wrap: anywhere; }
.assistant-message { align-items: flex-start; }
.assistant-body { min-width: 0; flex: 1; }
.result-sources { display: flex; align-items: center; flex-wrap: wrap; gap: 7px; padding: 0 0 10px; color: #858585; font-size: 10px; }
.result-sources b { padding: 5px 8px; border-radius: 999px; color: #7d3434; background: #fff0f0; font-weight: 650; }
.result-tabs { display: flex; gap: 4px; margin-bottom: 16px; overflow-x: auto; border-bottom: 1px solid #ececec; }
.result-tabs button { padding: 11px 14px; border: 0; border-radius: 9px 9px 0 0; color: #6d6d6d; background: transparent; white-space: nowrap; font-weight: 600; }
.result-tabs button.active { color: #202123; background: #f2f2f2; }
.result-content { padding: 0; }
.thinking-trace { width: min(360px, 48vw); max-width: 100%; margin-bottom: 12px; padding: 7px 11px; border: 1px solid #eeeeee; border-radius: 14px; color: #606060; background: #fff; box-shadow: 0 3px 14px rgba(0, 0, 0, .03); font-size: 11px; line-height: 1.45; transition: padding .2s ease, box-shadow .2s ease; }
.thinking-trace-collapsed { padding: 7px 11px; box-shadow: none; }
.trace-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 7px; cursor: pointer; user-select: none; }
.thinking-trace-collapsed .trace-head { margin-bottom: 0; }
.trace-head span { color: #8a8a8a; font-size: 11px; font-weight: 750; }
.trace-head b { min-width: 0; overflow: hidden; color: #9a9a9a; font-size: 10px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.thinking-trace-collapsed .trace-head { max-width: 100%; }
.agent-flow { display: grid; gap: 5px; max-height: 170px; margin: 0; padding: 0 2px 0 0; overflow-y: auto; list-style: none; }
.agent-step { position: relative; display: grid; grid-template-columns: 16px 1fr; gap: 8px; padding: 6px 8px; border-radius: 10px; animation: traceStepIn .32s ease both; transition: background .2s ease, transform .2s ease; }
.agent-step::before { content: ""; position: absolute; left: 17px; top: 28px; bottom: -10px; width: 1px; background: #e7e7e7; }
.agent-step:last-child::before { display: none; }
.agent-step i { position: relative; z-index: 1; display: grid; place-items: center; width: 16px; height: 16px; margin-top: 2px; border: 1px solid #d5d5d5; border-radius: 50%; background: #fff; }
.agent-step i::after { content: ""; width: 5px; height: 5px; border-radius: 50%; background: #b8b8b8; }
.agent-step strong { display: block; color: #2a2a2a; font-size: 11px; font-weight: 760; }
.agent-step p { margin: 1px 0 0; color: #555; }
.agent-step small { display: block; margin-top: 1px; color: #9a9a9a; font-size: 10px; }
.agent-step-running { background: #f7f7f7; transform: translateX(2px); }
.agent-step-running i { border-color: #202123; }
.agent-step-running i::after { background: #202123; animation: tracePulse 1s infinite; }
.agent-step-done i { color: #fff; border-color: #202123; background: #202123; }
.agent-step-done i::after { content: "✓"; width: auto; height: auto; color: #fff; background: transparent; font-size: 10px; font-weight: 900; line-height: 1; }
.practice-list { display: grid; gap: 16px; }
.practice-card { display: grid; gap: 14px; padding: 18px; border: 1px solid #ececec; border-radius: 14px; background: #fff; }
.practice-card.practice-correct { border-color: #b8e6ca; background: #fbfffc; }
.practice-card.practice-wrong { border-color: #f1caca; background: #fffafa; }
.practice-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.practice-head span { padding: 4px 8px; border-radius: 999px; color: #555; background: #f2f2f2; font-size: 11px; font-weight: 700; }
.practice-head b { color: #aaa; font-size: 22px; }
.practice-card h3 { margin: 0; color: #202123; font-size: 16px; line-height: 1.65; font-weight: 650; }
.practice-options { display: grid; gap: 9px; }
.practice-options button { display: flex; align-items: flex-start; gap: 10px; width: 100%; padding: 11px 12px; border: 1px solid #e1e1e1; border-radius: 11px; color: #333; background: #fafafa; text-align: left; line-height: 1.55; }
.practice-options button:hover:not(:disabled), .practice-options button.selected { border-color: #202123; background: #f3f3f3; }
.practice-options button span { display: grid; place-items: center; width: 24px; height: 24px; flex: 0 0 auto; border-radius: 50%; color: #fff; background: #202123; font-size: 11px; font-weight: 800; }
.practice-card textarea, .practice-card input { width: 100%; padding: 12px; border: 1px solid #dedede; border-radius: 11px; color: #202123; background: #fff; line-height: 1.6; }
.practice-card textarea:disabled, .practice-card input:disabled, .practice-options button:disabled { opacity: .78; cursor: default; }
.practice-actions { display: flex; justify-content: flex-end; }
.practice-actions button { padding: 9px 14px; border: 0; border-radius: 10px; color: #fff; background: #202123; font-size: 13px; font-weight: 700; }
.practice-actions button:disabled { background: #d0d0d0; }
.practice-feedback { display: grid; gap: 6px; padding: 12px; border-radius: 12px; background: #f7f7f7; }
.practice-feedback strong { color: #202123; }
.practice-feedback p { margin: 0; color: #5f5f5f; font-size: 13px; line-height: 1.65; }
.composer-section { position: sticky; bottom: 18px; z-index: 5; width: min(760px, calc(100% - 32px)); margin: 0 auto; padding: 0; background: transparent; box-shadow: none; }
.generate-page.idle .composer-section { position: static; padding: 0; background: transparent; }
.composer { padding: 8px 10px; border: 1px solid #d9d9d9; border-radius: 26px; background: rgba(255, 255, 255, .98); box-shadow: 0 14px 44px rgba(15, 23, 42, .16); outline: none; backdrop-filter: blur(10px); }
.composer:focus-within { border-color: #d9d9d9; box-shadow: 0 16px 48px rgba(15, 23, 42, .2); }
.composer textarea { min-width: 0; width: 100%; min-height: 24px; max-height: 150px; padding: 6px 4px; overflow-y: auto; border: 0; outline: 0; resize: none; color: #202123; background: transparent; font: inherit; font-size: 16px; line-height: 1.5; }
.composer textarea::placeholder { color: #929292; }
.selected-tools { display: flex; flex-wrap: wrap; gap: 7px; padding: 0 4px 7px; }
.selected-tools button { display: flex; align-items: center; gap: 6px; padding: 6px 9px; border: 1px solid #dedede; border-radius: 999px; color: #555; background: #fafafa; font-size: 12px; }
.selected-tools button i { color: #929292; font-style: normal; font-size: 14px; }
.selected-tools button.selected-file { max-width: 260px; border-color: #f1caca; color: #8d3434; background: #fff5f5; }
.selected-tools button.selected-file span { font-size: 9px; font-weight: 850; }
.composer-actions { display: flex; align-items: center; gap: 8px; }
.tool-picker { position: relative; }
.add-button { display: inline-grid; place-items: center; width: 36px; height: 36px; flex: 0 0 auto; padding: 0; border: 0; border-radius: 50%; color: #303030; background: #f0f0f0; line-height: 1; }
.add-button svg { width: 19px; height: 19px; display: block; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; }
.add-button:hover { background: #e6e6e6; }
.tool-menu { position: absolute; left: 0; bottom: 46px; width: 310px; padding: 8px; border: 1px solid #dadada; border-radius: 16px; background: #fff; box-shadow: 0 14px 38px rgba(0, 0, 0, .16); z-index: 20; }
.generate-page.idle .tool-menu { top: 46px; bottom: auto; }
.menu-title { padding: 8px 10px 6px; color: #888; font-size: 11px; font-weight: 700; }
.file-options { display: grid; max-height: 190px; overflow-y: auto; }
.no-files { padding: 10px; color: #969696; font-size: 11px; }
.menu-divider { height: 1px; margin: 7px 5px; background: #ececec; }
.tool-menu button { display: grid; grid-template-columns: 32px 1fr 20px; align-items: center; gap: 9px; width: 100%; padding: 10px; border: 0; border-radius: 10px; color: #282828; text-align: left; background: transparent; }
.tool-menu button:hover, .tool-menu button.selected { background: #f2f2f2; }
.tool-icon { display: grid; place-items: center; width: 30px; height: 30px; border: 1px solid #dedede; border-radius: 9px; font-size: 13px; }
.tool-icon.pdf { color: #b83838; background: #fff1f1; font-size: 9px; font-weight: 850; }
.tool-menu button > span:nth-child(2) { display: grid; gap: 2px; }
.tool-menu b { font-size: 13px; }
.tool-menu small { color: #8a8a8a; font-size: 10px; }
.tool-menu i { color: #202123; text-align: center; font-style: normal; }
.model-picker { position: relative; flex: 0 0 auto; }
.model-button { display: inline-flex; align-items: center; justify-content: center; gap: 5px; height: 36px; min-width: 76px; padding: 0 12px; border: 0; border-radius: 999px; color: #777; background: #f1f1f1; font-size: 15px; font-weight: 650; white-space: nowrap; }
.model-button:hover { color: #333; background: #e9e9e9; }
.model-button span { color: #8c8c8c; font-size: 13px; line-height: 1; }
.model-menu, .model-submenu { position: absolute; min-width: 160px; padding: 8px; border: 1px solid #d9d9d9; border-radius: 17px; background: #fff; box-shadow: 0 18px 44px rgba(0, 0, 0, .14); }
.model-menu { right: 0; bottom: 46px; z-index: 12; }
.generate-page.idle .model-menu { top: 46px; bottom: auto; }
.model-submenu { left: calc(100% + 6px); bottom: 0; z-index: 13; min-width: 178px; }
.generate-page.idle .model-submenu { top: auto; bottom: 0; }
.model-menu-item { display: flex; align-items: center; justify-content: space-between; gap: 14px; width: 100%; min-height: 42px; padding: 9px 12px; border: 0; border-radius: 11px; color: #222; background: transparent; text-align: left; font-size: 15px; line-height: 1.25; white-space: nowrap; }
.model-menu-item:hover, .model-menu-parent { background: #f2f2f2; }
.model-menu-item b { color: #111; font-size: 18px; font-weight: 500; }
.model-menu-divider { height: 1px; margin: 7px 8px; background: #ededed; }
.send-button { display: grid; place-items: center; width: 36px; height: 36px; flex: 0 0 auto; border: 0; border-radius: 50%; color: #fff; background: #202123; font-size: 20px; line-height: 1; }
.send-button:disabled { background: #d0d0d0; cursor: default; }
.composer-section:focus-within, .composer:focus, .composer textarea:focus, .add-button:focus, .model-button:focus, .model-menu-item:focus, .send-button:focus { outline: none; }

.resource-type-bar {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.resource-type-bar button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: #555;
  font-size: 13px;
  transition: all 0.2s;
  backdrop-filter: blur(8px);
}
.resource-type-bar button:hover:not(:disabled) {
  border-color: #b8b8b8;
  background: #fff;
  color: #222;
}
.resource-type-bar button.active {
  border-color: #202123;
  background: #202123;
  color: #fff;
}
.resource-type-bar .rt-icon {
  font-size: 14px;
  line-height: 1;
}
.resource-type-bar .rt-label {
  font-weight: 500;
}

.composer-hint { margin: 7px 0 0; color: rgba(80, 80, 80, .62); text-align: center; font-size: 10px; text-shadow: 0 1px 8px rgba(255, 255, 255, .9); }
.composer-error { margin: 0 auto 9px; padding: 9px 12px; border-radius: 10px; color: #a13838; background: #fff0f0; font-size: 12px; }
button { cursor: pointer; }
button:disabled { cursor: default; opacity: .65; }
@keyframes pulse { 50% { transform: scale(.94); opacity: .65; } }
@keyframes tracePulse {
  0% { box-shadow: 0 0 0 0 rgba(32, 33, 35, .28); }
  70% { box-shadow: 0 0 0 7px rgba(32, 33, 35, 0); }
  100% { box-shadow: 0 0 0 0 rgba(32, 33, 35, 0); }
}
@keyframes traceStepIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (max-width: 620px) {
  .generate-page { min-height: calc(100vh - 64px); }
  .chat-thread { padding-top: 10px; }
  .message-bubble { max-width: 88%; }
  .thinking-trace { width: min(320px, 88vw); }
  .tool-menu { width: min(310px, calc(100vw - 60px)); }
  .model-button { min-width: 62px; padding: 0 9px; font-size: 13px; }
  .model-menu { right: -48px; }
  .model-submenu { left: auto; right: 0; bottom: calc(100% + 6px); }
}

.save-to-library-btn {
  margin-left: auto;
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  color: #4b5563;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.save-to-library-btn:hover {
  border-color: #8b5cf6;
  background: #f5f3ff;
  color: #7c3aed;
}

.save-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
  padding: 20px;
}

.save-modal {
  width: min(480px, 90vw);
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.18);
  overflow: hidden;
  animation: saveModalIn 0.25s ease;
}

@keyframes saveModalIn {
  from { opacity: 0; transform: translateY(16px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.save-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid #f3f4f6;
}

.save-modal-header h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #1f2937;
}

.save-modal-close {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 8px;
  background: #f3f4f6;
  color: #6b7280;
  font-size: 18px;
  cursor: pointer;
  transition: background 0.2s;
}

.save-modal-close:hover {
  background: #e5e7eb;
}

.save-modal-body {
  padding: 20px 22px;
  max-height: 60vh;
  overflow-y: auto;
}

.save-form-group {
  margin-bottom: 18px;
}

.save-form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #374151;
}

.save-form-group input[type="text"] {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  color: #1f2937;
  outline: none;
  transition: border-color 0.2s;
}

.save-form-group input[type="text"]:focus {
  border-color: #8b5cf6;
}

.save-type-info {
  padding: 10px 14px;
  border-radius: 10px;
  background: #f5f3ff;
  color: #7c3aed;
  font-size: 14px;
  font-weight: 600;
}

.save-category-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 10px;
}

.save-category-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
  color: #4b5563;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
}

.save-category-btn:hover {
  border-color: #c4b5fd;
  background: #faf8ff;
}

.save-category-btn.active {
  border-color: #8b5cf6;
  background: #f5f3ff;
  color: #7c3aed;
}

.save-category-btn small {
  color: #9ca3af;
  font-weight: 500;
  font-size: 11px;
}

.save-category-btn.active small {
  color: #a78bfa;
}

.save-new-category input {
  width: 100%;
  box-sizing: border-box;
  padding: 9px 12px;
  border: 1.5px dashed #d1d5db;
  border-radius: 10px;
  font-size: 13px;
  color: #4b5563;
  background: #fafafa;
  outline: none;
  transition: all 0.2s;
}

.save-new-category input:focus {
  border-color: #8b5cf6;
  border-style: solid;
  background: #fff;
}

.save-error {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  background: #fef2f2;
  color: #dc2626;
  font-size: 13px;
}

.save-success {
  display: grid;
  justify-items: center;
  padding: 20px 0;
  text-align: center;
}

.success-icon {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #dcfce7;
  color: #16a34a;
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
  animation: successPop 0.4s ease;
}

@keyframes successPop {
  0% { transform: scale(0.5); opacity: 0; }
  60% { transform: scale(1.1); }
  100% { transform: scale(1); opacity: 1; }
}

.save-success p {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #16a34a;
}

.save-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 22px;
  border-top: 1px solid #f3f4f6;
}

.save-btn-cancel {
  padding: 10px 18px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #4b5563;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 10px;
  transition: background 0.2s;
}

.save-btn-cancel:hover {
  background: #f9fafb;
}

.save-btn-confirm {
  padding: 10px 18px;
  border: 0;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.25);
  transition: all 0.2s;
}

.save-btn-confirm:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(139, 92, 246, 0.3);
}

.save-btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
