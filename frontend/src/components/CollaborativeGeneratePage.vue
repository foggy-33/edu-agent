<script setup lang="ts">
import { computed, defineComponent, h, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  createConversationTitle,
  getConversationHistoryItem,
  saveConversationHistoryItem,
} from '../api/conversationHistory'
import { addMistake, exportOfficeFile, listCategories, listResources, saveGeneratedResource } from '../api/client'
import { loadSiliconFlowConfig, saveSiliconFlowConfig } from '../api/settings'
import { loadUserProfile } from '../api/userProfile'
import type { CollaborativeExerciseItem, CollaborativeLearningRequest, CollaborativeLearningResponse, CollaborativeResourceType, UploadedResource } from '../types'
import MarkdownRenderer from './MarkdownRenderer.vue'
import MermaidRenderer from './MermaidRenderer.vue'
import sparkOfficialLogo from '../assets/spark-official.ico'

type ResultKey = 'lectureDoc' | 'mindmap' | 'exercises' | 'reading' | 'codeCase' | 'learningPath' | 'presentation' | 'wordDocument' | 'review'
type ProcessState = 'running' | 'done'
type ResponseSpeed = 'fast' | 'balanced' | 'deep'

const toolIconPaths = {
  chat: ['M7 17.2 4.3 19l.9-3.3A7.2 7.2 0 1 1 7 17.2Z'],
  lecture: ['M4.5 5.2h5.2c1.4 0 2.3.8 2.3 2.1v11c0-1.3-.9-2.1-2.3-2.1H4.5V5.2Zm15 0h-5.2c-1.4 0-2.3.8-2.3 2.1v11c0-1.3.9-2.1 2.3-2.1h5.2V5.2Z'],
  mindmap: ['M12 4v4m0 0H7m5 0h5M7 8v4m10-4v4M5 12h4v4H5v-4Zm10 0h4v4h-4v-4Zm-5 6h4v3h-4v-3Zm2-2v2'],
  exercise: ['M6 3.8h12a2 2 0 0 1 2 2v12.4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5.8a2 2 0 0 1 2-2Zm2 8.1 2.4 2.4 5.3-5.5'],
  reading: ['M3.8 5.2h5.5c1.6 0 2.7.9 2.7 2.3v11.2c0-1.4-1.1-2.3-2.7-2.3H3.8V5.2Zm16.4 0h-5.5c-1.6 0-2.7.9-2.7 2.3v11.2c0-1.4 1.1-2.3 2.7-2.3h5.5V5.2Z'],
  code: ['m8.6 5-5 7 5 7m6.8-14 5 7-5 7M13.7 3.8l-3.4 16.4'],
  path: ['M5 5.2v4.3c0 1.6 1.2 2.7 2.8 2.7h5.8c1.6 0 2.8 1.1 2.8 2.7v3.9m0 0-2.6-2.6m2.6 2.6 2.6-2.6M5 5.2l-2 2m2-2 2 2'],
  ppt: ['M4 4.8h16v10.4H4V4.8Zm8 10.4v4.2m-3.5 0h7M7.2 8h9.6M7.2 11h6.4'],
  word: ['M6 3.8h8l4 4v12.4H6V3.8Zm8 0v4h4M8.8 11h6.4m-6.4 3h6.4m-6.4 3h4.2'],
} as const

type ToolIconName = keyof typeof toolIconPaths

const ToolGlyph = defineComponent({
  props: { name: { type: String, required: true } },
  setup(props) {
    return () => h(
      'svg',
      { viewBox: '0 0 24 24', 'aria-hidden': 'true', focusable: 'false' },
      (toolIconPaths[props.name as ToolIconName] || toolIconPaths.chat).map(path => h('path', { d: path }))
    )
  },
})

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
  provider: 'siliconflow' | 'spark' | 'openai'
  responseSpeed: ResponseSpeed
}

interface ComposerModelOption {
  label: string
  model: string
  provider?: 'siliconflow' | 'spark' | 'openai'
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
  icon: ToolIconName
}[] = [
  { key: 'chat', resultKey: null, label: '普通对话', description: '普通问答对话', icon: 'chat' },
  { key: 'lecture', resultKey: 'lectureDoc', label: '课程讲解', description: '生成概念、原理和示例讲解', icon: 'lecture' },
  { key: 'mindmap', resultKey: 'mindmap', label: '思维导图', description: '生成结构化知识导图', icon: 'mindmap' },
  { key: 'exercise', resultKey: 'exercises', label: '练习题', description: '生成分层题目和答案解析', icon: 'exercise' },
  { key: 'reading', resultKey: 'reading', label: '拓展阅读', description: '生成延伸知识和学习路径', icon: 'reading' },
  { key: 'code', resultKey: 'codeCase', label: '代码实操', description: '生成可运行代码案例与讲解', icon: 'code' },
  { key: 'path', resultKey: 'learningPath', label: '学习路线', description: '生成阶段划分和个性化学习路径', icon: 'path' },
  { key: 'ppt', resultKey: 'presentation', label: 'PPT讲解', description: '生成可下载的演示文稿', icon: 'ppt' },
  { key: 'word', resultKey: 'wordDocument', label: 'Word 文档', description: '生成可下载的学习文档', icon: 'word' },
]

const speedOptions: Array<{ key: ResponseSpeed; label: string; description: string }> = [
  { key: 'fast', label: '极速', description: '优先快速、简洁回答' },
  { key: 'balanced', label: '中', description: '兼顾速度与完整性' },
  { key: 'deep', label: '高', description: '更充分分析与核对' },
]

const composerModels: ComposerModelOption[] = [
  { label: 'DeepSeek-V4-Pro', model: 'deepseek-ai/DeepSeek-V4-Pro' },
  { label: 'DeepSeek-V4-Flash', model: 'deepseek-ai/DeepSeek-V4-Flash' },
  { label: 'DeepSeek-V3.2 Pro', model: 'Pro/deepseek-ai/DeepSeek-V3.2' },
  { label: 'GLM-5.2', model: 'zai-org/GLM-5.2' },
  { label: 'GPT-5.6 Sol', model: 'gpt-5.6-sol', provider: 'openai' },
  { label: '讯飞星火 X2', model: 'spark-x', provider: 'spark' },
  { label: '讯飞星火 Lite', model: 'lite', provider: 'spark' },
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
const fileSearch = ref('')
const promptInput = ref<HTMLTextAreaElement | null>(null)
const addButton = ref<HTMLButtonElement | null>(null)
const toolMenuPlacement = ref<'up' | 'down'>('up')
const toolMenuMaxHeight = ref(420)
const selectedTypes = ref<CollaborativeResourceType[]>([])
const selectedType = ref<CollaborativeResourceType | 'chat'>('chat')
const selectedFileIds = ref<string[]>([])
const submittedTypes = ref<CollaborativeResourceType[]>([])
const menuOpen = ref(false)
const speedMenuOpen = ref(false)
const modelMenuOpen = ref(false)
const storedSpeed = localStorage.getItem('studyflow_response_speed')
const responseSpeed = ref<ResponseSpeed>(storedSpeed === 'fast' || storedSpeed === 'deep' ? storedSpeed : 'balanced')
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
  presentation: '',
  wordDocument: '',
  review: '',
})
const thinkingSteps = ref<string[]>([])
const processSteps = ref<AgentProcessStep[]>([])
const processQueue = ref<AgentProcessStep[]>([])
const processCollapsed = ref(false)
const processCompleted = ref(false)
const processElapsedSeconds = ref(0)
let processTimer: ReturnType<typeof setTimeout> | null = null
let processClock: ReturnType<typeof setInterval> | null = null
const PROCESS_STEP_DELAY_MS = 760
const PROCESS_AUTO_COLLAPSE_MS = 1600

const emptyStreamContent = (): Record<ResultKey, string> => ({
  lectureDoc: '',
  mindmap: '',
  exercises: '',
  reading: '',
  codeCase: '',
  learningPath: '',
  presentation: '',
  wordDocument: '',
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

const selectedFiles = computed(() => resources.value.filter(item => selectedFileIds.value.includes(item.id)))
const filteredResources = computed(() => {
  const keyword = fileSearch.value.trim().toLowerCase()
  return resources.value
    .filter(item => !keyword || item.name.toLowerCase().includes(keyword) || item.course_folder?.toLowerCase().includes(keyword))
    .sort((left, right) => Number(selectedFileIds.value.includes(right.id)) - Number(selectedFileIds.value.includes(left.id)))
})
const hasStreamingOutput = computed(() => conversationTurns.value.length > 0 || Object.values(streamContent.value).some(Boolean) || thinkingSteps.value.length > 0)
const activeSpeed = computed(() => speedOptions.find(item => item.key === responseSpeed.value) || speedOptions[1])
const activeComposerModel = computed(() => composerModels.find(item =>
  modelConfig.value.active_provider === 'spark'
    ? item.provider === 'spark' && item.model === (modelConfig.value.spark_model || 'spark-x')
    : modelConfig.value.active_provider === 'openai'
      ? item.provider === 'openai' && item.model === (modelConfig.value.openai_model || 'gpt-5.6-sol')
    : !item.provider && item.model === modelConfig.value.model))
const activeModelLabel = computed(() => activeComposerModel.value?.label || (modelConfig.value.active_provider === 'openai' ? modelConfig.value.openai_model : modelConfig.value.model).split('/').pop() || '自定义模型')

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

function isOfficeTurn(turn: ConversationTurn) {
  return turn.resourceTypes.includes('ppt') || turn.resourceTypes.includes('word')
}

function officeTurnLabel(turn: ConversationTurn) {
  if (turn.resourceTypes.includes('ppt')) return 'PPT讲解'
  return 'Word学习文档'
}

function officeTurnDescription(turn: ConversationTurn) {
  const format = turn.resourceTypes.includes('ppt') ? 'PPTX演示文稿' : 'DOCX学习文档'
  const rawTopic = (turn.question || '本次学习主题').replace(/\s+/g, ' ').trim()
  const topic = rawTopic.length > 54 ? `${rawTopic.slice(0, 54)}…` : rawTopic
  return `已围绕“${topic}”完成内容组织与排版，完整内容已写入${format}。`
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
const officeDownloading = ref<ResultKey | ''>('')
const officeDownloadError = ref('')

const resultTypeLabelMap: Record<string, { label: string; type: string }> = {
  lectureDoc: { label: '讲义', type: 'lecture' },
  mindmap: { label: '思维导图', type: 'mindmap' },
  exercises: { label: '练习题', type: 'markdown' },
  reading: { label: '阅读材料', type: 'reading' },
  codeCase: { label: '代码案例', type: 'markdown' },
  learningPath: { label: '学习路径', type: 'path' },
  presentation: { label: 'PPT讲解', type: 'markdown' },
  wordDocument: { label: 'Word 文档', type: 'markdown' },
  review: { label: '复习总结', type: 'markdown' },
}

const activeTabLabel = computed(() => resultTypeLabelMap[activeTab.value]?.label || activeTab.value)
const activeTabType = computed(() => resultTypeLabelMap[activeTab.value]?.type || 'markdown')

async function downloadOffice(turn: ConversationTurn, key: ResultKey) {
  if (key !== 'presentation' && key !== 'wordDocument') return
  const content = contentForTurn(turn, key)
  if (!content.trim()) {
    officeDownloadError.value = '当前内容为空，无法生成文件'
    return
  }

  officeDownloading.value = key
  officeDownloadError.value = ''
  const format = key === 'presentation' ? 'pptx' : 'docx'
  const typeLabel = key === 'presentation' ? '演示文稿' : '学习文档'
  const rawTitle = `${turn.question || 'AI 学习资料'}-${typeLabel}`
  const safeTitle = rawTitle.replace(/[\\/:*?"<>|]/g, '-').replace(/\s+/g, ' ').trim().slice(0, 80) || 'AI 学习资料'

  try {
    const blob = await exportOfficeFile({
      title: safeTitle,
      subtitle: '智学 AI · 根据学习任务生成',
      content,
      format,
    })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${safeTitle}.${format}`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (reason) {
    officeDownloadError.value = reason instanceof Error ? reason.message : '文件生成失败，请稍后重试'
  } finally {
    officeDownloading.value = ''
  }
}

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

function visibleProcessAgents(turn: ConversationTurn) {
  const latestByAgent = new Map<string, AgentProcessStep>()
  turn.processSteps.forEach(step => latestByAgent.set(step.agent, step))
  return [...latestByAgent.values()].slice(-6)
}

function agentInitial(agent: string) {
  return agent.replace(/\s*Agent$/i, '').slice(0, 2)
}

function agentLabel(agent: string) {
  return agent.replace(/\s*Agent$/i, '')
}

function startProcessClock() {
  processElapsedSeconds.value = 0
  if (processClock) clearInterval(processClock)
  processClock = window.setInterval(() => {
    processElapsedSeconds.value += 1
  }, 1000)
}

function stopProcessClock() {
  if (processClock) {
    clearInterval(processClock)
    processClock = null
  }
}

function toggleToolMenu() {
  menuOpen.value = !menuOpen.value
  if (menuOpen.value) {
    speedMenuOpen.value = false
    modelMenuOpen.value = false
    void nextTick(updateToolMenuLayout)
  }
}

function updateToolMenuLayout() {
  if (!menuOpen.value || !addButton.value) return
  const rect = addButton.value.getBoundingClientRect()
  const viewportGap = 14
  const menuGap = 12
  const availableAbove = Math.max(0, rect.top - viewportGap - menuGap)
  const availableBelow = Math.max(0, window.innerHeight - rect.bottom - viewportGap - menuGap)
  const openDown = availableAbove < 340 && availableBelow > availableAbove
  toolMenuPlacement.value = openDown ? 'down' : 'up'
  toolMenuMaxHeight.value = Math.max(180, Math.min(520, openDown ? availableBelow : availableAbove))
}

const toolMenuStyle = computed(() => ({
  '--tool-menu-max-height': `${toolMenuMaxHeight.value}px`,
}))

function toggleFile(fileId: string) {
  selectedFileIds.value = selectedFileIds.value.includes(fileId)
    ? selectedFileIds.value.filter(item => item !== fileId)
    : [...selectedFileIds.value, fileId]
}

function selectComposerModel(option: ComposerModelOption) {
  modelConfig.value = option.provider === 'spark'
    ? { ...modelConfig.value, active_provider: 'spark', spark_api_password: '', spark_base_url: '', spark_model: option.model }
    : option.provider === 'openai'
      ? { ...modelConfig.value, active_provider: 'openai', openai_model: option.model }
    : { ...modelConfig.value, active_provider: 'siliconflow', model: option.model }
  saveSiliconFlowConfig(modelConfig.value)
  modelMenuOpen.value = false
  speedMenuOpen.value = false
}

function selectResponseSpeed(speed: ResponseSpeed) {
  responseSpeed.value = speed
  localStorage.setItem('studyflow_response_speed', speed)
  speedMenuOpen.value = false
}

function toggleModelSpeedMenu() {
  speedMenuOpen.value = !speedMenuOpen.value
  modelMenuOpen.value = false
  menuOpen.value = false
}

function toggleModelSubmenu() {
  modelMenuOpen.value = !modelMenuOpen.value
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
  processElapsedSeconds.value = 0
  stopProcessClock()
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
        responseSpeed: 'balanced' as ResponseSpeed,
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
    learningPath: lastTurn.result.learningPath || '',
    presentation: lastTurn.result.presentation || '',
    wordDocument: lastTurn.result.wordDocument || '',
    review: lastTurn.result.review || '',
  }
  thinkingSteps.value = [...lastTurn.thinkingSteps]
  responseSpeed.value = lastTurn.responseSpeed || 'balanced'
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
      codeCase: turn.result.codeCase || '',
      learningPath: turn.result.learningPath || '',
      presentation: turn.result.presentation || '',
      wordDocument: turn.result.wordDocument || '',
      review: turn.result.review || '',
    },
    thinkingSteps: [...turn.thinkingSteps],
    processSteps: buildHistoryProcessSteps(turn.thinkingSteps, `${turn.id}-history`),
    processCollapsed: true,
    processCompleted: true,
    provider: turn.provider || 'siliconflow',
    responseSpeed: turn.responseSpeed || 'balanced',
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
      responseSpeed: turn.responseSpeed,
      provider: turn.provider,
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
  }, PROCESS_AUTO_COLLAPSE_MS)
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
    stopProcessClock()
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
    response_speed: responseSpeed.value,
    ...config,
  }

  loading.value = true
  error.value = ''
  result.value = null
  prompt.value = ''
  resetStreamState()
  startProcessClock()
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
      provider: config.active_provider,
      responseSpeed: responseSpeed.value,
    },
  ]
  exerciseAnswers.value = {}
  exerciseSubmitted.value = {}
  menuOpen.value = false
  modelMenuOpen.value = false
  speedMenuOpen.value = false
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
    stopProcessClock()
  }
}

onMounted(() => {
  loadUploadedResources()
  hydrateFromHistory(props.historyId)
  resizePromptInput()
  window.addEventListener('resize', updateToolMenuLayout)
})

onBeforeUnmount(() => {
  stopProcessClock()
  if (processTimer) clearTimeout(processTimer)
  window.removeEventListener('resize', updateToolMenuLayout)
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

      <article class="chat-message assistant-message spark-response">
        <div class="spark-mark" title="讯飞星火" aria-label="讯飞星火 AI 回复">
          <img :src="sparkOfficialLogo" alt="" aria-hidden="true" />
        </div>
        <div class="assistant-body">
          <div v-if="turn.processSteps.length" :class="['thinking-trace', turn.processCollapsed ? 'thinking-trace-collapsed' : '', turn.processCompleted ? 'thinking-trace-completed' : '']">
            <div class="trace-head" role="button" tabindex="0" @click="setTurnCollapsed(turn.id, !turn.processCollapsed)">
              <span><i class="collab-live-dot"></i>多 Agent 协作</span>
              <b>
                {{ turn.processCollapsed
                  ? activeProcessSummary(turn)
                  : turn.processCompleted
                    ? `已完成 ${turn.processSteps.filter(step => step.state === 'done').length} 个阶段`
                    : `${turn.processSteps.filter(step => step.state === 'done').length} 个阶段 · ${processElapsedSeconds}s` }}
              </b>
            </div>
            <template v-if="!turn.processCollapsed">
              <div class="agent-handoff" :class="{ completed: turn.processCompleted }">
                <div class="agent-cluster">
                  <span
                    v-for="step in visibleProcessAgents(turn)"
                    :key="`${turn.id}-${step.agent}`"
                    :class="['agent-chip', `agent-chip-${step.state}`]"
                    :title="step.agent"
                  >
                    <em>{{ agentInitial(step.agent) }}</em>
                    <small>{{ agentLabel(step.agent) }}</small>
                  </span>
                </div>
                <div v-if="!turn.processCompleted" class="handoff-wave" aria-label="Agent 正在交接任务"><i></i><i></i><i></i></div>
              </div>
              <ol class="agent-flow">
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
            </template>
          </div>

          <div v-if="!isOfficeTurn(turn) && uniqueSources(turn.result?.sources).length" class="result-sources">
            <span>参考资料</span>
            <b v-for="source in uniqueSources(turn.result?.sources)" :key="source.id">{{ source.name }}</b>
          </div>

          <div v-if="isOfficeTurn(turn)" class="office-delivery-card">
            <span class="office-delivery-icon" aria-hidden="true">
              <ToolGlyph :name="turn.resourceTypes.includes('ppt') ? 'ppt' : 'word'" />
            </span>
            <div class="office-delivery-copy">
              <small>{{ turn.processCompleted ? '文件已生成' : '正在生成文件' }}</small>
              <h3>{{ officeTurnLabel(turn) }}</h3>
              <p>{{ turn.processCompleted ? officeTurnDescription(turn) : '正在整理核心内容并生成最终文件，请稍候。' }}</p>
            </div>
            <div v-if="turn.processCompleted && turn.result" class="office-delivery-actions">
              <button
                v-if="turn.resourceTypes.includes('ppt')"
                type="button"
                class="office-primary-download"
                :disabled="Boolean(officeDownloading)"
                @click="downloadOffice(turn, 'presentation')"
              >
                <span aria-hidden="true">↓</span>
                {{ officeDownloading === 'presentation' ? '正在生成文件…' : '下载 PPT' }}
              </button>
              <button
                v-if="turn.resourceTypes.includes('word')"
                type="button"
                class="office-primary-download"
                :disabled="Boolean(officeDownloading)"
                @click="downloadOffice(turn, 'wordDocument')"
              >
                <span aria-hidden="true">↓</span>
                {{ officeDownloading === 'wordDocument' ? '正在生成文件…' : '下载 Word' }}
              </button>
            </div>
          </div>

          <div
            v-else-if="tabsForTurn(turn).length > 1"
            class="result-tabs"
          >
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
          <p v-if="isActiveTurn(turn) && officeDownloadError" class="office-download-error">{{ officeDownloadError }}</p>

          <div v-if="!isOfficeTurn(turn)" class="result-content">
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

      <div class="composer">
        <div v-if="selectedType !== 'chat' || selectedFiles.length" class="selected-tools">
          <button
            v-if="selectedType !== 'chat'"
            type="button"
            class="selected-capability"
            :disabled="loading"
            @click="toggleResource('chat')"
          >
            <span><ToolGlyph :name="resourceOptions.find(item => item.key === selectedType)?.icon || 'chat'" /></span>
            {{ resourceOptions.find(item => item.key === selectedType)?.label }}
            <i>×</i>
          </button>
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
              ref="addButton"
              class="add-button"
              :class="{ open: menuOpen }"
              type="button"
              :disabled="loading"
              aria-label="选择生成内容"
              :aria-expanded="menuOpen"
              @click="toggleToolMenu"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 5v14M5 12h14" />
              </svg>
            </button>

            <Transition name="tool-pop">
              <div
                v-if="menuOpen"
                :class="['tool-menu', { 'tool-menu-down': toolMenuPlacement === 'down' }]"
                :style="toolMenuStyle"
              >
                <div class="tool-menu-head">
                  <div>
                    <strong>选择功能</strong>
                    <span>功能与资料可以组合使用</span>
                  </div>
                  <small>{{ selectedFiles.length ? `已选 ${selectedFiles.length} 份资料` : '未选择资料' }}</small>
                </div>
                <div class="capability-grid">
                  <button
                    v-for="(item, index) in resourceOptions"
                    :key="item.key"
                    type="button"
                    class="capability-option"
                    :class="{ selected: selectedType === item.key }"
                    :style="{ animationDelay: `${index * 38 + 40}ms` }"
                    @click="toggleResource(item.key)"
                  >
                    <span class="tool-icon"><ToolGlyph :name="item.icon" /></span>
                    <span><b>{{ item.label }}</b></span>
                    <i>{{ selectedType === item.key ? '✓' : '' }}</i>
                  </button>
                </div>

                <div class="menu-divider"></div>
                <div class="file-tools-head">
                  <div class="menu-title">引用资料库文件 <span>{{ filteredResources.length }}/{{ resources.length }}</span></div>
                  <label class="file-search">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="m20 20-4-4"></path></svg>
                    <input v-model="fileSearch" type="search" placeholder="搜索文件或课程" />
                  </label>
                </div>
                <TransitionGroup v-if="resources.length && filteredResources.length" name="file-row" tag="div" class="file-options">
                  <button
                    v-for="file in filteredResources"
                    :key="file.id"
                    type="button"
                    :title="file.name"
                    :class="{ selected: selectedFileIds.includes(file.id) }"
                    @click="toggleFile(file.id)"
                  >
                    <span class="tool-icon pdf">PDF</span>
                    <span><b>{{ file.name }}</b><small>{{ file.page_count }} 页 · 已解析</small></span>
                    <i>{{ selectedFileIds.includes(file.id) ? '✓' : '' }}</i>
                  </button>
                </TransitionGroup>
                <div v-else-if="resources.length" class="no-files">没有匹配的资料，换个关键词试试</div>
                <div v-else class="no-files">资料库暂无 PDF，请先上传文件</div>
              </div>
            </Transition>
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

          <div class="model-picker combined-picker">
            <button
              type="button"
              class="model-button combined-trigger"
              :disabled="loading"
              @click="toggleModelSpeedMenu"
            >
              {{ activeSpeed.label }}
              <span>⌄</span>
            </button>

            <div v-if="speedMenuOpen" class="model-menu combined-menu">
              <div class="combined-menu-title">智能</div>
              <button
                v-for="speed in speedOptions"
                :key="speed.key"
                type="button"
                class="model-menu-item speed-choice"
                @click="selectResponseSpeed(speed.key)"
              >
                <span>{{ speed.label }}</span>
                <b v-if="responseSpeed === speed.key">✓</b>
              </button>
              <div class="combined-divider"></div>
              <button type="button" class="model-menu-item model-entry" @click.stop="toggleModelSubmenu">
                <span>{{ activeModelLabel }}</span>
                <b>›</b>
              </button>

              <div v-if="modelMenuOpen" class="model-menu model-list-menu model-submenu">
                <button
                  v-for="model in composerModels"
                  :key="`${model.provider || 'siliconflow'}-${model.model}`"
                  type="button"
                  class="model-menu-item"
                  @click="selectComposerModel(model)"
                >
                  <span>{{ model.label }}</span>
                  <b v-if="model.provider === 'spark' ? modelConfig.active_provider === 'spark' && (modelConfig.spark_model || 'spark-x') === model.model : model.provider === 'openai' ? modelConfig.active_provider === 'openai' && (modelConfig.openai_model || 'gpt-5.6-sol') === model.model : modelConfig.active_provider === 'siliconflow' && modelConfig.model === model.model">✓</b>
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
.spark-response { gap: 12px; }
.spark-response .assistant-body { padding: 16px 18px; border: 1px solid #eeeeee; border-radius: 18px; background: #ffffff; }
.spark-mark { width: 34px; height: 42px; flex: 0 0 34px; display: grid; place-items: center; }
.spark-mark img { width: 30px; height: 30px; object-fit: contain; }
.result-sources { display: flex; align-items: center; flex-wrap: wrap; gap: 7px; padding: 0 0 10px; color: #858585; font-size: 10px; }
.result-sources b { padding: 5px 8px; border-radius: 999px; color: #7d3434; background: #fff0f0; font-weight: 650; }
.result-tabs { display: flex; gap: 4px; margin-bottom: 16px; overflow-x: auto; border-bottom: 1px solid #ececec; }
.result-tabs button { padding: 11px 14px; border: 0; border-radius: 9px 9px 0 0; color: #6d6d6d; background: transparent; white-space: nowrap; font-weight: 600; }
.result-tabs button.active { color: #202123; background: #f2f2f2; }
.result-content { padding: 0; }
.thinking-trace { width: min(560px, 62vw); max-width: 100%; margin-bottom: 12px; padding: 10px 12px; overflow: hidden; border: 1px solid #e8e8e8; border-radius: 16px; color: #606060; background: #fff; box-shadow: 0 9px 30px rgba(0, 0, 0, .045); font-size: 11px; line-height: 1.45; transition: padding .2s ease, box-shadow .2s ease; }
.thinking-trace-collapsed { padding: 7px 11px; box-shadow: none; }
.trace-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 7px; cursor: pointer; user-select: none; }
.thinking-trace-collapsed .trace-head { margin-bottom: 0; }
.trace-head span { display: inline-flex; align-items: center; gap: 7px; color: #555; font-size: 11px; font-weight: 800; }
.trace-head b { min-width: 0; overflow: hidden; color: #9a9a9a; font-size: 10px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.thinking-trace-collapsed .trace-head { max-width: 100%; }
.collab-live-dot { width: 7px; height: 7px; flex: 0 0 auto; border-radius: 50%; background: #202123; box-shadow: 0 0 0 0 rgba(32,33,35,.24); animation: collaborationPulse 1.5s ease-out infinite; }
.thinking-trace-completed .collab-live-dot { background: #888; animation: none; }
.agent-handoff { position: relative; display: flex; align-items: center; min-height: 62px; margin: 4px 0 9px; padding: 9px 11px; overflow: hidden; border-radius: 13px; background: linear-gradient(105deg, #f6f6f6, #fff 42%, #f4f4f4); }
.agent-handoff::before { content: ""; position: absolute; inset: 0; background: linear-gradient(105deg, transparent 28%, rgba(255,255,255,.94) 48%, transparent 68%); transform: translateX(-100%); animation: collaborationSweep 2.8s ease-in-out infinite; }
.agent-handoff.completed::before { display: none; }
.agent-cluster { position: relative; z-index: 1; display: flex; align-items: center; min-width: 0; }
.agent-chip { position: relative; display: grid; justify-items: center; gap: 3px; width: 60px; color: #888; opacity: .7; transition: color .25s ease, opacity .25s ease, transform .35s cubic-bezier(.16,1,.3,1); }
.agent-chip + .agent-chip::before { content: ""; position: absolute; top: 16px; right: calc(50% + 16px); width: 28px; height: 1px; background: repeating-linear-gradient(90deg, #aaa 0 4px, transparent 4px 7px); animation: agentLinkFlow .8s linear infinite; }
.agent-chip em { display: grid; place-items: center; width: 32px; height: 32px; border: 1px solid #d6d6d6; border-radius: 10px; color: #555; background: #fff; font-size: 10px; font-style: normal; font-weight: 850; box-shadow: 0 3px 10px rgba(0,0,0,.04); }
.agent-chip small { width: 58px; overflow: hidden; text-align: center; text-overflow: ellipsis; white-space: nowrap; font-size: 9px; }
.agent-chip-running { color: #202123; opacity: 1; transform: translateY(-2px); }
.agent-chip-running em { color: #fff; border-color: #202123; background: #202123; animation: activeAgentFloat 1.5s ease-in-out infinite; }
.agent-chip-done { opacity: 1; }
.handoff-wave { position: relative; z-index: 1; display: flex; align-items: center; gap: 3px; margin-left: auto; padding: 0 5px 12px 12px; }
.handoff-wave i { width: 4px; border-radius: 99px; background: #303030; animation: handoffBars .9s ease-in-out infinite; }
.handoff-wave i:nth-child(1) { height: 9px; animation-delay: -.18s; }
.handoff-wave i:nth-child(2) { height: 17px; animation-delay: -.09s; }
.handoff-wave i:nth-child(3) { height: 12px; }
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
.selected-tools button.selected-capability { border-color: #d5d5d5; color: #202123; background: #f3f3f3; }
.selected-tools button.selected-capability > span { display: grid; place-items: center; width: 18px; height: 18px; color: #202123; }
.selected-tools button.selected-capability svg { width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }
.selected-tools button.selected-file { max-width: 260px; border-color: #dedede; color: #555; background: #fafafa; }
.selected-tools button.selected-file span { font-size: 9px; font-weight: 850; }
.composer-actions { display: flex; align-items: center; gap: 8px; }
.tool-picker { position: relative; }
.add-button { display: inline-grid; place-items: center; width: 36px; height: 36px; flex: 0 0 auto; padding: 0; border: 0; border-radius: 50%; color: #303030; background: #f0f0f0; line-height: 1; }
.add-button svg { width: 19px; height: 19px; display: block; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; transition: transform .3s cubic-bezier(.16, 1, .3, 1); }
.add-button:hover { background: #e6e6e6; }
.add-button.open { color: #fff; background: #202123; box-shadow: 0 7px 20px rgba(0, 0, 0, .2); }
.add-button.open svg { transform: rotate(45deg); }
.tool-menu { position: absolute; left: 0; bottom: 48px; display: flex; flex-direction: column; width: min(720px, calc(100vw - 40px)); max-height: min(520px, var(--tool-menu-max-height, 420px)); padding: 16px; overflow-x: hidden; overflow-y: auto; overscroll-behavior: contain; border: 1px solid #dadada; border-radius: 20px; background: rgba(255, 255, 255, .985); box-shadow: 0 24px 70px rgba(0, 0, 0, .16); z-index: 20; transform-origin: left bottom; backdrop-filter: blur(18px); scrollbar-width: thin; will-change: transform, opacity, filter; }
.tool-menu-down { top: 48px; bottom: auto; transform-origin: left top; }
.tool-menu-head { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 12px; }
.tool-menu-head > div { display: grid; gap: 2px; }
.tool-menu-head strong { color: #222; font-size: 15px; }
.tool-menu-head span, .tool-menu-head small { color: #929292; font-size: 10px; }
.tool-menu-head small { flex: 0 0 auto; padding: 5px 8px; border-radius: 999px; background: #f2f2f2; }
.menu-title { color: #777; font-size: 11px; font-weight: 700; }
.menu-title span { color: #aaa; font-weight: 500; }
.file-tools-head { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin: 11px 2px 9px; }
.file-search { width: min(260px, 48%); height: 34px; display: flex; align-items: center; gap: 7px; padding: 0 10px; border: 1px solid #dedede; border-radius: 999px; background: #f8f8f8; transition: border-color .2s ease, background .2s ease, box-shadow .2s ease; }
.file-search:focus-within { border-color: #aaa; background: #fff; box-shadow: 0 0 0 3px rgba(0,0,0,.04); }
.file-search svg { width: 14px; height: 14px; flex: 0 0 auto; fill: none; stroke: #888; stroke-width: 1.8; stroke-linecap: round; }
.file-search input { min-width: 0; width: 100%; border: 0; outline: 0; color: #333; background: transparent; font-size: 11px; }
.file-search input::-webkit-search-cancel-button { cursor: pointer; }
.file-options { position: relative; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 5px; flex: 1 1 150px; min-height: 68px; max-height: 150px; padding-right: 3px; overflow-y: auto; overscroll-behavior: contain; scrollbar-width: thin; }
.file-options button > span:nth-child(2) { min-width: 0; }
.file-options button b { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.no-files { display: grid; place-items: center; min-height: 76px; color: #969696; font-size: 11px; }
.menu-divider { height: 1px; margin: 13px 2px 0; background: #ececec; }
.capability-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.tool-menu button { display: grid; grid-template-columns: 32px 1fr 20px; align-items: center; gap: 9px; width: 100%; padding: 9px; border: 0; border-radius: 11px; color: #282828; text-align: left; background: transparent; transition: background .18s ease, border-color .18s ease, transform .18s cubic-bezier(.16,1,.3,1); }
.tool-menu button:hover, .tool-menu button.selected { background: #f2f2f2; }
.tool-menu button:active { transform: scale(.975); }
.tool-menu .capability-option { grid-template-columns: 30px minmax(0, 1fr) 16px; width: 100%; min-width: 0; height: 54px; padding: 8px 12px; border: 1px solid #e3e3e3; border-radius: 999px; opacity: 0; animation: capabilityItemIn .36s cubic-bezier(.16, 1, .3, 1) forwards; }
.tool-menu .capability-option.selected { color: #fff; border-color: #202123; background: #202123; }
.tool-menu .capability-option.selected .tool-icon, .tool-menu .capability-option.selected i { color: #fff; border-color: rgba(255,255,255,.28); }
.tool-icon { display: grid; place-items: center; width: 30px; height: 30px; border: 1px solid #dedede; border-radius: 9px; font-size: 13px; }
.capability-option .tool-icon { width: 30px; height: 30px; border-radius: 50%; color: #373737; }
.capability-option .tool-icon svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 1.65; stroke-linecap: round; stroke-linejoin: round; }
.tool-icon.pdf { color: #555; background: #f5f5f5; font-size: 9px; font-weight: 850; }
.tool-menu button > span:nth-child(2) { display: grid; gap: 2px; }
.tool-menu b { overflow: hidden; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.tool-menu small { color: #8a8a8a; font-size: 10px; }
.tool-menu i { color: #202123; text-align: center; font-style: normal; }
.tool-pop-enter-active { animation: toolMenuIn .32s cubic-bezier(.16, 1, .3, 1); }
.tool-pop-leave-active { animation: toolMenuOut .16s ease both; }
.file-row-enter-active, .file-row-leave-active, .file-row-move { transition: opacity .2s ease, transform .24s cubic-bezier(.16,1,.3,1); }
.file-row-enter-from, .file-row-leave-to { opacity: 0; transform: translateY(6px) scale(.98); }
.file-row-leave-active { position: absolute; }
.model-picker { position: relative; flex: 0 0 auto; }
.model-button { display: inline-flex; align-items: center; justify-content: center; gap: 5px; height: 36px; min-width: 76px; padding: 0 12px; border: 0; border-radius: 999px; color: #777; background: #f1f1f1; font-size: 15px; font-weight: 650; white-space: nowrap; }
.model-button:hover { color: #333; background: #e9e9e9; }
.model-name-button { max-width: 190px; overflow: hidden; text-overflow: ellipsis; }
.model-button span { color: #8c8c8c; font-size: 13px; line-height: 1; }
.model-menu { position: absolute; min-width: 160px; padding: 8px; border: 1px solid #d9d9d9; border-radius: 17px; background: #fff; box-shadow: 0 18px 44px rgba(0, 0, 0, .14); }
.model-menu { right: 0; bottom: 46px; z-index: 12; }
.combined-trigger { min-width: 64px; color: #5f5f5f; font-size: 16px; font-weight: 500; }
.combined-menu { width: 202px; padding: 10px; }
.combined-menu-title { padding: 5px 12px 7px; color: #999; font-size: 14px; }
.combined-menu .speed-choice { min-height: 42px; font-size: 16px; }
.combined-menu .speed-choice b { font-size: 20px; }
.combined-divider { height: 1px; margin: 6px 12px 7px; background: #e4e4e4; }
.combined-menu .model-entry { font-size: 15px; }
.combined-menu .model-entry span { max-width: 142px; overflow: hidden; text-overflow: ellipsis; }
.combined-menu .model-entry b { font-size: 27px; font-weight: 300; line-height: 1; }
.model-list-menu { min-width: 225px; }
.model-submenu { right: calc(100% + 10px); bottom: 0; z-index: 13; }
.generate-page.idle .model-menu { top: 46px; bottom: auto; }
.generate-page.idle .model-submenu { top: 0; bottom: auto; }
.model-menu-item { display: flex; align-items: center; justify-content: space-between; gap: 14px; width: 100%; min-height: 42px; padding: 9px 12px; border: 0; border-radius: 11px; color: #222; background: transparent; text-align: left; font-size: 15px; line-height: 1.25; white-space: nowrap; }
.model-menu-item:hover { background: #f2f2f2; }
.model-menu-item b { color: #111; font-size: 18px; font-weight: 500; }
.send-button { display: grid; place-items: center; width: 36px; height: 36px; flex: 0 0 auto; border: 0; border-radius: 50%; color: #fff; background: #202123; font-size: 20px; line-height: 1; }
.send-button:disabled { background: #d0d0d0; cursor: default; }
.composer-section:focus-within, .composer:focus, .composer textarea:focus, .add-button:focus, .model-button:focus, .model-menu-item:focus, .send-button:focus { outline: none; }

.composer-hint { margin: 7px 0 0; color: rgba(80, 80, 80, .62); text-align: center; font-size: 10px; text-shadow: 0 1px 8px rgba(255, 255, 255, .9); }
.composer-error { margin: 0 auto 9px; padding: 9px 12px; border-radius: 10px; color: #a13838; background: #fff0f0; font-size: 12px; }
button { cursor: pointer; }
button:disabled { cursor: default; opacity: .65; }
@keyframes pulse { 50% { transform: scale(.94); opacity: .65; } }
@keyframes toolMenuIn {
  from { opacity: 0; transform: translateY(14px) scale(.9); filter: blur(6px); }
  to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
}
@keyframes toolMenuOut {
  from { opacity: 1; transform: translateY(0) scale(1); }
  to { opacity: 0; transform: translateY(7px) scale(.96); }
}
@keyframes capabilityItemIn {
  from { opacity: 0; transform: translateY(9px) scale(.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes tracePulse {
  0% { box-shadow: 0 0 0 0 rgba(32, 33, 35, .28); }
  70% { box-shadow: 0 0 0 7px rgba(32, 33, 35, 0); }
  100% { box-shadow: 0 0 0 0 rgba(32, 33, 35, 0); }
}
@keyframes traceStepIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes collaborationPulse {
  70% { box-shadow: 0 0 0 7px rgba(32,33,35,0); }
  100% { box-shadow: 0 0 0 0 rgba(32,33,35,0); }
}
@keyframes collaborationSweep {
  0%, 18% { transform: translateX(-110%); }
  70%, 100% { transform: translateX(110%); }
}
@keyframes activeAgentFloat {
  0%, 100% { transform: translateY(0); box-shadow: 0 4px 12px rgba(0,0,0,.12); }
  50% { transform: translateY(-3px); box-shadow: 0 8px 18px rgba(0,0,0,.2); }
}
@keyframes agentLinkFlow { to { background-position: 7px 0; } }
@keyframes handoffBars {
  0%, 100% { transform: scaleY(.55); opacity: .45; }
  50% { transform: scaleY(1); opacity: 1; }
}
@media (prefers-reduced-motion: reduce) {
  .collab-live-dot, .agent-handoff::before, .agent-chip + .agent-chip::before, .agent-chip-running em, .handoff-wave i { animation: none; }
}
@media (max-width: 620px) {
  .generate-page { min-height: calc(100vh - 64px); }
  .chat-thread { padding-top: 10px; }
  .message-bubble { max-width: 88%; }
  .thinking-trace { width: min(320px, 88vw); }
  .tool-menu { width: calc(100vw - 32px); max-height: min(520px, var(--tool-menu-max-height, 72vh)); padding: 12px; }
  .tool-menu-head span { display: none; }
  .capability-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .tool-menu .capability-option { min-width: 0; height: 52px; }
  .file-tools-head { align-items: stretch; flex-direction: column; gap: 8px; }
  .file-search { width: 100%; }
  .file-options { grid-template-columns: 1fr; max-height: 138px; }
  .model-button { min-width: 62px; padding: 0 9px; font-size: 13px; }
  .model-menu { right: -48px; }
  .combined-menu { right: 0; }
  .model-submenu, .generate-page.idle .model-submenu { top: calc(100% + 8px); right: 0; bottom: auto; }
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

.office-delivery-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  margin: 12px 0 6px;
  padding: 18px;
  border: 1px solid #e4e0ff;
  border-radius: 18px;
  background: linear-gradient(135deg, #ffffff 0%, #faf9ff 58%, #f3f0ff 100%);
  box-shadow: 0 12px 34px rgba(70, 55, 150, .08);
  animation: officeCardIn .38s cubic-bezier(.16, 1, .3, 1) both;
}
.office-delivery-icon {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border: 1px solid #dad4ff;
  border-radius: 14px;
  color: #5b45c6;
  background: #fff;
}
.office-delivery-icon :deep(svg) { width: 22px; height: 22px; }
.office-delivery-copy { min-width: 0; }
.office-delivery-copy small { color: #6d5bd0; font-size: 11px; font-weight: 700; }
.office-delivery-copy h3 { margin: 3px 0 5px; color: #202123; font-size: 16px; }
.office-delivery-copy p { margin: 0; color: #6f7280; font-size: 12px; line-height: 1.65; }
.office-delivery-actions { display: flex; align-items: center; gap: 8px; }
.office-primary-download {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-width: 154px;
  padding: 12px 20px;
  border: 1px solid #5b45c6;
  border-radius: 999px;
  color: #fff;
  background: #5b45c6;
  box-shadow: 0 10px 28px rgba(91, 69, 198, .2);
  font-size: 14px;
  font-weight: 750;
  cursor: pointer;
  transition: transform .2s cubic-bezier(.16, 1, .3, 1), box-shadow .2s ease, background .2s ease;
}
.office-primary-download span { font-size: 17px; line-height: 1; }
.office-primary-download:hover:not(:disabled) { transform: translateY(-2px); background: #4e39bb; box-shadow: 0 14px 34px rgba(91, 69, 198, .28); }
.office-primary-download:disabled { cursor: wait; opacity: .62; }
.office-download-error { margin: 8px 0 14px; color: #b42318; font-size: 12px; }
@keyframes officeCardIn {
  from { opacity: 0; transform: translateY(8px) scale(.99); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
@media (max-width: 720px) {
  .office-delivery-card { grid-template-columns: auto minmax(0, 1fr); }
  .office-delivery-actions { grid-column: 1 / -1; }
  .office-primary-download { width: 100%; }
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
