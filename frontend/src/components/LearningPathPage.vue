<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { generateLearningResources, getResourceContent, listResources, saveGeneratedResource } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import { loadUserProfile } from '../api/userProfile'
import type { UploadedResource } from '../types'
import MarkdownRenderer from './MarkdownRenderer.vue'

defineEmits<{
  navigate: [page: 'home' | 'analyze' | 'collaborative' | 'evaluate' | 'courses' | 'account' | 'portrait' | 'resources']
}>()

const userProfile = ref(loadUserProfile())
const modelConfig = ref(loadSiliconFlowConfig())

type ViewMode = 'progress' | 'text'
const viewMode = ref<ViewMode>('progress')

const loading = ref(false)
const pathList = ref<UploadedResource[]>([])
const currentPathId = ref<string>('')
const currentPath = ref<UploadedResource | null>(null)
const pathContent = ref('')
const contentLoading = ref(false)

const showGenerateModal = ref(false)
const generating = ref(false)
const generateError = ref('')

const showPathSelector = ref(false)

const genCourse = ref('数据库系统')
const genChapter = ref('')
const genWeakness = ref('')
const genGoal = ref('考试复习')

const courseOptions = [
  '数据库系统',
  '数据结构',
  '计算机网络',
  '操作系统',
  '计算机组成原理',
]

const goalOptions = [
  '考试复习',
  '课程学习',
  '考研准备',
  '竞赛训练',
  '项目实践',
]

interface PathStage {
  index: number
  title: string
  goal: string
  knowledge: string[]
  resources: string[]
  duration: string
  dependency: string
  checkpoint: string
}

interface PathInfo {
  title: string
  totalGoal: string
  stages: PathStage[]
  tips: string[]
}

const STORAGE_KEY_PREFIX = 'edu_agent_path_progress_'

function getProgressStorageKey(): string {
  return `${STORAGE_KEY_PREFIX}${userProfile.value.userId}`
}

interface PathProgress {
  [pathId: string]: {
    completedStages: number[]
    currentStage: number
  }
}

function loadProgress(): PathProgress {
  try {
    const raw = localStorage.getItem(getProgressStorageKey())
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function saveProgress(progress: PathProgress) {
  localStorage.setItem(getProgressStorageKey(), JSON.stringify(progress))
}

const progress = ref<PathProgress>(loadProgress())

function getPathProgress(pathId: string) {
  if (!progress.value[pathId]) {
    progress.value[pathId] = { completedStages: [], currentStage: 1 }
  }
  return progress.value[pathId]
}

const currentProgress = computed(() => {
  if (!currentPathId.value) return { completedStages: [], currentStage: 1 }
  return getPathProgress(currentPathId.value)
})

const totalStages = computed(() => parsedPath.value?.stages.length || 0)
const completedCount = computed(() => currentProgress.value.completedStages.length)
const progressPercent = computed(() => {
  if (totalStages.value === 0) return 0
  return Math.round((completedCount.value / totalStages.value) * 100)
})

function toggleStageComplete(stageIndex: number) {
  const p = getPathProgress(currentPathId.value)
  const idx = p.completedStages.indexOf(stageIndex)
  if (idx > -1) {
    p.completedStages.splice(idx, 1)
  } else {
    p.completedStages.push(stageIndex)
    p.completedStages.sort((a, b) => a - b)
  }
  saveProgress(progress.value)
}

function isStageCompleted(stageIndex: number): boolean {
  return currentProgress.value.completedStages.includes(stageIndex)
}

function getCurrentStageIndex(): number {
  if (totalStages.value === 0) return 0
  for (let i = 1; i <= totalStages.value; i++) {
    if (!isStageCompleted(i)) return i
  }
  return totalStages.value
}

function setAsCurrentStage(stageIndex: number) {
  const p = getPathProgress(currentPathId.value)
  p.currentStage = stageIndex
  saveProgress(progress.value)
}

function toggleStageExpand(index: number, stageIndex: number) {
  setAsCurrentStage(stageIndex)
  if (activeStageIndex.value === index) {
    activeStageIndex.value = -1
  } else {
    activeStageIndex.value = index
  }
}

function resetProgress() {
  if (!currentPathId.value) return
  if (confirm('确定要重置当前学习路线的进度吗？')) {
    progress.value[currentPathId.value] = { completedStages: [], currentStage: 1 }
    saveProgress(progress.value)
  }
}

async function loadPathList() {
  loading.value = true
  try {
    const result = await listResources(userProfile.value.userId)
    pathList.value = result.resources.filter(r => r.type === 'path')
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    if (pathList.value.length > 0) {
      const saved = loadProgress()
      let targetId = ''
      for (const p of pathList.value) {
        if (saved[p.id]) {
          targetId = p.id
          break
        }
      }
      if (!targetId && pathList.value.length > 0) {
        targetId = pathList.value[0].id
      }
      if (targetId) {
        selectCurrentPath(targetId)
      }
    }
  } catch (e) {
    console.error('加载学习路径列表失败:', e)
  } finally {
    loading.value = false
  }
}

function selectCurrentPath(pathId: string) {
  currentPathId.value = pathId
  const path = pathList.value.find(p => p.id === pathId)
  if (path) {
    currentPath.value = path
    loadPathContent(pathId)
  }
  showPathSelector.value = false
}

async function loadPathContent(pathId: string) {
  pathContent.value = ''
  contentLoading.value = true
  try {
    const result = await getResourceContent(userProfile.value.userId, pathId)
    pathContent.value = result.content
  } catch (e) {
    console.error('加载学习路径内容失败:', e)
  } finally {
    contentLoading.value = false
  }
}

function cleanMd(text: string): string {
  return text
    .replace(/^#+\s*/, '')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/`(.+?)`/g, '$1')
    .replace(/\[(.+?)\]\(.*?\)/g, '$1')
    .replace(/^[-*•]\s*/g, '')
    .trim()
}

function extractFieldValue(line: string, keywords: string[]): string | null {
  const patterns = [
    new RegExp(`^[-*•]\\s*\\*?\\*?.*?(?:${keywords.join('|')}).*?\\*?\\*?[：: ]*\\s*`),
    new RegExp(`^\\d+[.、]\\s*\\*?\\*?.*?(?:${keywords.join('|')}).*?\\*?\\*?[：: ]*\\s*`),
  ]
  for (const pat of patterns) {
    const match = line.match(pat)
    if (match) {
      return line.replace(pat, '').trim()
    }
  }
  return null
}

const parsedPath = computed<PathInfo | null>(() => {
  if (!pathContent.value) return null

  let title = ''
  let totalGoal = ''
  const stages: PathStage[] = []
  const tips: string[] = []

  const lines = pathContent.value.split('\n')

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue

    if (/^#\s+/.test(trimmed)) {
      title = cleanMd(trimmed.replace(/^#+\s*/, ''))
    }
  }

  let inGoal = false
  let goalLines: string[] = []
  for (const line of lines) {
    const trimmed = line.trim()
    if (/^##+\s+/.test(trimmed)) {
      if (/总目标/.test(trimmed) || /一、/.test(trimmed)) {
        inGoal = true
        continue
      } else {
        if (inGoal) break
      }
    }
    if (inGoal && trimmed && !/^##+\s+/.test(trimmed)) {
      const clean = cleanMd(trimmed)
      if (clean && clean.length > 2) goalLines.push(clean)
    }
  }
  totalGoal = goalLines.join(' ')

  const stageHeadings: { title: string; startLine: number }[] = []
  let lineIdx = 0
  for (const line of lines) {
    const m = line.match(/^#{3}\s+(.+)$/)
    if (m) {
      stageHeadings.push({ title: m[1].trim(), startLine: lineIdx })
    }
    lineIdx++
  }

  for (let i = 0; i < stageHeadings.length; i++) {
    const heading = stageHeadings[i]
    let rawTitle = cleanMd(heading.title)
    rawTitle = rawTitle.replace(/^阶段\s*[一二三四五六七八九十百\d]+[.、：: ]*\s*/, '')
    rawTitle = rawTitle.replace(/^第[一二三四五六七八九十百\d]+阶段[.、：: ]*\s*/, '')
    rawTitle = rawTitle.replace(/^[一二三四五六七八九十百\d]+[.、：: ]\s*/, '')
    rawTitle = rawTitle.trim()
    if (!rawTitle) rawTitle = `第${stages.length + 1}阶段`

    if (/总目标|阶段划分|学习建议|整体建议|总结|说明/.test(rawTitle)) continue

    const stage: PathStage = {
      index: stages.length + 1,
      title: rawTitle,
      goal: '',
      knowledge: [],
      resources: [],
      duration: '',
      dependency: '无',
      checkpoint: '',
    }

    const endLine = i < stageHeadings.length - 1 ? stageHeadings[i + 1].startLine : lines.length
    for (let j = heading.startLine + 1; j < endLine; j++) {
      const tline = lines[j].trim()
      if (!tline) continue

      const goalVal = extractFieldValue(tline, ['学习目标', '目标'])
      if (goalVal) { stage.goal = cleanMd(goalVal); continue }

      const knowVal = extractFieldValue(tline, ['核心知识点', '知识点', '重点内容'])
      if (knowVal) {
        stage.knowledge = cleanMd(knowVal).split(/[、，,；;]+/).map(s => s.trim()).filter(Boolean).slice(0, 8)
        continue
      }

      const resVal = extractFieldValue(tline, ['推荐资源', '学习资源', '参考资料', '推荐资料'])
      if (resVal) {
        stage.resources = cleanMd(resVal).split(/[、，,；;]+/).map(s => s.trim()).filter(Boolean).slice(0, 5)
        continue
      }

      const durVal = extractFieldValue(tline, ['预计时长', '学习时长', '时长', '时间'])
      if (durVal) { stage.duration = cleanMd(durVal); continue }

      const depVal = extractFieldValue(tline, ['依赖关系', '前置依赖', '前置要求', '前置知识', '依赖'])
      if (depVal) { stage.dependency = cleanMd(depVal); continue }

      const checkVal = extractFieldValue(tline, ['检验标准', '验收标准', '考核标准', '达成标准', '检验'])
      if (checkVal) { stage.checkpoint = cleanMd(checkVal); continue }
    }

    if (!stage.goal) stage.goal = '按照计划完成本阶段学习内容'
    if (!stage.duration) stage.duration = '约3天'
    if (!stage.checkpoint) stage.checkpoint = '能够独立完成相关练习'

    stages.push(stage)
  }

  let inTips = false
  for (const line of lines) {
    const trimmed = line.trim()
    if (/^##+\s+/.test(trimmed)) {
      if (/建议/.test(trimmed) || /三、/.test(trimmed)) {
        inTips = true
        continue
      } else {
        if (inTips && tips.length > 0) break
      }
    }
    if (inTips && trimmed && !/^##+\s+/.test(trimmed)) {
      const clean = cleanMd(trimmed.replace(/^\d+[.、：: ]\s*/, '').replace(/^[-*•]\s*/, ''))
      if (clean && clean.length > 3) tips.push(clean)
    }
  }

  if (!totalGoal && title) {
    totalGoal = `掌握「${title}」相关核心知识，达成学习目标。`
  }

  return { title, totalGoal, stages, tips }
})

const totalDuration = computed(() => {
  if (!parsedPath.value) return '—'
  let totalDays = 0
  for (const stage of parsedPath.value.stages) {
    const match = stage.duration.match(/(\d+)\s*[-~至]\s*(\d+)\s*天/)
    if (match) {
      totalDays += (parseInt(match[1]) + parseInt(match[2])) / 2
    } else {
      const singleMatch = stage.duration.match(/(\d+)\s*天/)
      if (singleMatch) {
        totalDays += parseInt(singleMatch[1])
      }
    }
  }
  return totalDays ? `约 ${Math.round(totalDays)} 天` : '—'
})

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`
}

function openGenerateModal() {
  showGenerateModal.value = true
  generateError.value = ''
}

function closeGenerateModal() {
  showGenerateModal.value = false
  generating.value = false
}

async function generateNewPath() {
  if (!genChapter.value.trim()) {
    generateError.value = '请输入章节或知识点'
    return
  }
  generateError.value = ''
  generating.value = true

  try {
    const result = await generateLearningResources({
      user_id: userProfile.value.userId,
      major: '未指定',
      course: genCourse.value,
      chapter: genChapter.value,
      weakness: genWeakness.value || genChapter.value,
      goal: genGoal.value,
      resourceTypes: ['path'],
      fileIds: [],
      api_key: modelConfig.value.api_key,
      base_url: modelConfig.value.base_url,
      model: modelConfig.value.model,
    })

    if (result.learningPath) {
      const saveRes = await saveGeneratedResource({
        user_id: userProfile.value.userId,
        name: `${genChapter.value}-学习路径`,
        content: result.learningPath,
        resource_type: 'path',
        course_folder: genCourse.value,
      })

      await loadPathList()

      if (saveRes.resource) {
        selectCurrentPath(saveRes.resource.id)
      }

      closeGenerateModal()
    } else {
      generateError.value = '生成失败，请重试'
    }
  } catch (e) {
    generateError.value = (e as Error).message || '生成失败，请重试'
  } finally {
    generating.value = false
  }
}

const activeStageIndex = ref(0)

watch(() => currentPathId.value, () => {
  activeStageIndex.value = Math.max(0, getCurrentStageIndex() - 1)
})

onMounted(() => {
  loadPathList()
})
</script>

<template>
  <div class="learning-path-page">
    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">学习路线图</h1>
        <p class="page-subtitle">规划科学、动态的个性化学习路径，明确学习步骤和顺序</p>
      </div>
      <div class="header-actions">
        <div class="view-toggle">
          <button
            class="toggle-btn"
            :class="{ active: viewMode === 'progress' }"
            @click="viewMode = 'progress'"
          >
            学习进度
          </button>
          <button
            class="toggle-btn"
            :class="{ active: viewMode === 'text' }"
            @click="viewMode = 'text'"
          >
            原文
          </button>
        </div>
        <button class="new-path-btn" @click="openGenerateModal">
          <span class="btn-icon">+</span>
          生成新路线
        </button>
      </div>
    </header>

    <!-- 当前学习路径选择器 -->
    <div v-if="pathList.length > 0" class="path-selector-bar">
      <div class="selector-label">当前学习路线</div>
      <div class="selector-current" @click="showPathSelector = !showPathSelector">
        <span class="current-icon">↗</span>
        <span class="current-name">{{ currentPath?.name || '请选择' }}</span>
        <span class="current-arrow">{{ showPathSelector ? '▲' : '▼' }}</span>
      </div>
      <div v-if="showPathSelector" class="selector-dropdown">
        <div
          v-for="p in pathList"
          :key="p.id"
          class="dropdown-item"
          :class="{ active: p.id === currentPathId }"
          @click="selectCurrentPath(p.id)"
        >
          <span class="dd-name">{{ p.name }}</span>
          <span class="dd-meta">{{ p.course_folder }} · {{ formatDate(p.created_at) }}</span>
        </div>
      </div>
      <div v-if="currentPath" class="selector-meta">
        <span class="meta-tag">{{ currentPath.course_folder }}</span>
        <span class="meta-tag">{{ totalStages }} 个阶段</span>
      </div>
    </div>

    <div class="page-content">
      <div v-if="loading" class="page-loading">加载中...</div>

      <div v-else-if="pathList.length === 0" class="empty-page">
        <div class="empty-icon">↗</div>
        <h2 class="empty-title">还没有学习路线</h2>
        <p class="empty-desc">AI 智能分析你的学习目标，生成个性化学习路径</p>
        <button class="primary-btn" @click="openGenerateModal">生成学习路线</button>
      </div>

      <div v-else-if="contentLoading && !pathContent" class="page-loading">加载路径内容中...</div>

      <template v-else-if="currentPath && parsedPath">
        <!-- 学习进度视图 -->
        <template v-if="viewMode === 'progress'">
          <div class="progress-overview">
            <div class="progress-header">
              <div>
                <h2 class="progress-title">{{ parsedPath.title }}</h2>
                <p class="progress-goal">{{ parsedPath.totalGoal }}</p>
              </div>
              <div class="progress-badge">
                <span class="progress-percent">{{ progressPercent }}%</span>
                <span class="progress-label">完成度</span>
              </div>
            </div>

            <div class="progress-bar-wrapper">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
              </div>
              <div class="progress-info">
                <span>已完成 {{ completedCount }} / {{ totalStages }} 个阶段</span>
                <span>预计总时长：{{ totalDuration }}</span>
              </div>
            </div>
          </div>

          <div class="stages-progress-section">
            <div class="section-header">
              <h3 class="section-title">学习阶段进度</h3>
              <button class="reset-btn" @click="resetProgress">重置进度</button>
            </div>
            <div class="stages-progress-list">
              <div
                v-for="(stage, index) in parsedPath.stages"
                :key="stage.index"
                class="stage-progress-card"
                :class="{
                  completed: isStageCompleted(stage.index),
                  current: getCurrentStageIndex() === stage.index && !isStageCompleted(stage.index),
                  expanded: activeStageIndex === index,
                }"
                @click="toggleStageExpand(index, stage.index)"
              >
                <div class="sp-left">
                  <div
                    class="sp-check"
                    @click.stop="toggleStageComplete(stage.index)"
                  >
                    <span v-if="isStageCompleted(stage.index)">✓</span>
                    <span v-else>{{ stage.index }}</span>
                  </div>
                  <div v-if="index < parsedPath.stages.length - 1" class="sp-line"></div>
                </div>
                <div class="sp-main">
                  <div class="sp-header">
                    <div class="sp-title-wrap">
                      <h4 class="sp-title">{{ stage.title }}</h4>
                      <span v-if="getCurrentStageIndex() === stage.index && !isStageCompleted(stage.index)" class="current-badge">进行中</span>
                      <span v-if="isStageCompleted(stage.index)" class="done-badge">已完成</span>
                    </div>
                    <div class="sp-header-right">
                      <span class="sp-duration">{{ stage.duration }}</span>
                      <span class="sp-expand-icon">{{ activeStageIndex === index ? '▲' : '▼' }}</span>
                    </div>
                  </div>
                  <p v-if="stage.goal" class="sp-goal">{{ stage.goal }}</p>

                  <div v-if="stage.knowledge.length" class="sp-tags">
                    <span v-for="k in stage.knowledge.slice(0, 5)" :key="k" class="sp-tag">{{ k }}</span>
                    <span v-if="stage.knowledge.length > 5" class="sp-tag-more">+{{ stage.knowledge.length - 5 }}</span>
                  </div>

                  <div v-if="activeStageIndex === index" class="sp-detail-expanded">
                    <div class="detail-row">
                      <div class="detail-block">
                        <div class="detail-label">学习目标</div>
                        <div class="detail-value">{{ stage.goal || '按照计划完成本阶段学习内容' }}</div>
                      </div>
                    </div>
                    <div v-if="stage.knowledge.length" class="detail-block">
                      <div class="detail-label">核心知识点</div>
                      <div class="knowledge-tags">
                        <span v-for="k in stage.knowledge" :key="k" class="k-tag">{{ k }}</span>
                      </div>
                    </div>
                    <div v-if="stage.resources.length" class="detail-block">
                      <div class="detail-label">推荐学习资源</div>
                      <div class="resource-list">
                        <div v-for="(r, i) in stage.resources" :key="i" class="r-item">
                          <span class="r-icon">▣</span>
                          <span class="r-text">{{ r }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="detail-row">
                      <div class="detail-block">
                        <div class="detail-label">预计时长</div>
                        <div class="detail-value">{{ stage.duration }}</div>
                      </div>
                      <div class="detail-block">
                        <div class="detail-label">前置依赖</div>
                        <div class="detail-value">{{ stage.dependency || '无' }}</div>
                      </div>
                    </div>
                    <div class="detail-block">
                      <div class="detail-label">检验标准</div>
                      <div class="detail-value checkpoint">{{ stage.checkpoint || '能够独立完成相关练习' }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- 文本视图 -->
        <template v-else>
          <div class="text-view-header">
            <h2 class="path-title">{{ currentPath.name }}</h2>
            <div class="path-submeta">
              <span>{{ currentPath.course_folder }}</span>
              <span>·</span>
              <span>{{ formatDate(currentPath.created_at) }}</span>
            </div>
          </div>
          <div class="markdown-card">
            <MarkdownRenderer :content="pathContent" />
          </div>
        </template>
      </template>
    </div>

    <!-- 生成弹窗 -->
    <div v-if="showGenerateModal" class="modal-overlay" @click.self="closeGenerateModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">生成学习路线</h3>
          <button class="modal-close" @click="closeGenerateModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>目标课程</label>
            <select v-model="genCourse">
              <option v-for="c in courseOptions" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div class="form-item">
            <label>学习目标</label>
            <select v-model="genGoal">
              <option v-for="g in goalOptions" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>
          <div class="form-item">
            <label>章节 / 知识点 <span class="required">*</span></label>
            <input
              v-model="genChapter"
              type="text"
              placeholder="例如：关系数据库标准语言 SQL"
            />
          </div>
          <div class="form-item">
            <label>薄弱点（选填）</label>
            <input
              v-model="genWeakness"
              type="text"
              placeholder="例如：嵌套查询、视图、索引"
            />
          </div>
          <p v-if="generateError" class="error-text">{{ generateError }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeGenerateModal">取消</button>
          <button
            class="btn-primary"
            :disabled="generating || !genChapter.trim()"
            @click="generateNewPath"
          >
            {{ generating ? '生成中...' : '开始生成' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.learning-path-page {
  padding: 20px 28px;
  height: calc(100vh - 56px);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  background: #f5f6f8;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
  flex-shrink: 0;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 3px 0;
}

.page-subtitle {
  font-size: 13px;
  color: #888;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-toggle {
  display: flex;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 3px;
}

.toggle-btn {
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn.active {
  background: #1a1a1a;
  color: #fff;
}

.new-path-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  height: 34px;
  padding: 0 14px;
  border: none;
  border-radius: 8px;
  background: #1a1a1a;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.new-path-btn:hover {
  background: #333;
}

.btn-icon {
  font-size: 14px;
  font-weight: 400;
}

/* 路径选择器 */
.path-selector-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  background: #fff;
  border: 1px solid #eaecef;
  border-radius: 10px;
  margin-bottom: 14px;
  flex-shrink: 0;
  position: relative;
}

.selector-label {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  flex-shrink: 0;
}

.selector-current {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 7px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 200px;
}

.selector-current:hover {
  border-color: #ccc;
  background: #f0f0f0;
}

.current-icon {
  font-size: 14px;
  color: #666;
}

.current-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: #1a1a1a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.current-arrow {
  font-size: 10px;
  color: #999;
}

.selector-dropdown {
  position: absolute;
  top: 100%;
  left: 100px;
  margin-top: 4px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  z-index: 100;
  min-width: 280px;
  max-height: 300px;
  overflow-y: auto;
}

.dropdown-item {
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid #f5f5f5;
  display: flex;
  flex-direction: column;
  gap: 3px;
  transition: background 0.15s;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background: #f9f9f9;
}

.dropdown-item.active {
  background: #f0f0f0;
}

.dd-name {
  font-size: 13px;
  font-weight: 500;
  color: #1a1a1a;
}

.dd-meta {
  font-size: 11px;
  color: #999;
}

.selector-meta {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.meta-tag {
  padding: 3px 10px;
  background: #f5f5f5;
  border-radius: 5px;
  font-size: 11px;
  color: #666;
}

.page-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.page-loading {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #999;
}

.empty-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-icon {
  font-size: 56px;
  color: #e5e7eb;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 6px 0;
}

.empty-desc {
  font-size: 13px;
  color: #999;
  margin: 0 0 20px 0;
}

.primary-btn {
  padding: 9px 24px;
  border: none;
  border-radius: 8px;
  background: #1a1a1a;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.primary-btn:hover {
  background: #333;
}

/* 学习进度视图 */
.progress-overview {
  background: #fff;
  border: 1px solid #eaecef;
  border-radius: 12px;
  padding: 24px 28px;
  margin-bottom: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.progress-title {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 6px 0;
}

.progress-goal {
  font-size: 13px;
  color: #666;
  margin: 0;
  max-width: 500px;
  line-height: 1.6;
}

.progress-badge {
  text-align: center;
  padding: 12px 20px;
  background: linear-gradient(135deg, #f5f5f5 0%, #eee 100%);
  border-radius: 10px;
  min-width: 90px;
}

.progress-percent {
  font-size: 26px;
  font-weight: 800;
  color: #1a1a1a;
  display: block;
  line-height: 1;
  margin-bottom: 4px;
}

.progress-label {
  font-size: 11px;
  color: #888;
  font-weight: 500;
}

.progress-bar-wrapper {
  margin-top: 8px;
}

.progress-bar {
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #333 0%, #1a1a1a 100%);
  border-radius: 4px;
  transition: width 0.4s ease;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #888;
}

.progress-tips {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.pt-label {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  color: #888;
  padding-top: 2px;
}

.pt-scroll {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  flex: 1;
}

.pt-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  font-size: 12px;
  color: #555;
}

.pt-num {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #1a1a1a;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pt-text {
  line-height: 1.4;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 14px 0;
}

/* 阶段进度卡片列表 */
.stages-progress-section {
  background: #fff;
  border: 1px solid #eaecef;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.reset-btn {
  padding: 5px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fff;
  font-size: 12px;
  color: #888;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-btn:hover {
  border-color: #d9d9d9;
  color: #666;
}

.stages-progress-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.stage-progress-card {
  display: flex;
  gap: 14px;
  padding: 18px 0;
  border-bottom: 1px solid #f0f0f0;
  position: relative;
}

.stage-progress-card:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.stage-progress-card.completed .sp-title {
  text-decoration: line-through;
  color: #aaa;
}

.stage-progress-card.current .sp-main {
  background: #fafafa;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid #e8e8e8;
}

.sp-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 32px;
  flex-shrink: 0;
}

.sp-check {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 2px solid #d9d9d9;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #999;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.sp-check:hover {
  border-color: #1a1a1a;
}

.stage-progress-card.completed .sp-check {
  background: #1a1a1a;
  border-color: #1a1a1a;
  color: #fff;
  font-size: 14px;
}

.sp-line {
  width: 2px;
  flex: 1;
  min-height: 20px;
  background: #e8e8e8;
  margin-top: 6px;
}

.stage-progress-card.completed .sp-line {
  background: #1a1a1a;
}

.sp-main {
  flex: 1;
  min-width: 0;
  transition: all 0.2s;
}

.sp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.sp-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.sp-duration {
  padding: 3px 10px;
  background: #f0f0f0;
  border-radius: 5px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
  flex-shrink: 0;
}

.stage-progress-card.completed .sp-duration {
  background: #f5f5f5;
  color: #aaa;
}

.sp-goal {
  font-size: 13px;
  color: #555;
  line-height: 1.6;
  margin: 0 0 10px 0;
}

.stage-progress-card.completed .sp-goal {
  color: #aaa;
}

.sp-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 12px;
}

.sp-tag {
  padding: 4px 9px;
  background: #f5f5f5;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  font-size: 11px;
  color: #666;
}

.sp-tag-more {
  padding: 4px 8px;
  background: transparent;
  font-size: 11px;
  color: #999;
}

.sp-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.current-badge {
  padding: 2px 8px;
  background: #1a1a1a;
  color: #fff;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.done-badge {
  padding: 2px 8px;
  background: #f0f0f0;
  color: #999;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.sp-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.sp-expand-icon {
  font-size: 10px;
  color: #999;
  width: 20px;
  text-align: center;
}

.sp-detail-expanded {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed #e8e8e8;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.detail-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-label {
  font-size: 11px;
  font-weight: 600;
  color: #888;
}

.detail-value {
  font-size: 13px;
  color: #333;
  line-height: 1.6;
}

.detail-value.checkpoint {
  padding: 10px 12px;
  background: #fafafa;
  border-left: 3px solid #1a1a1a;
  border-radius: 0 5px 5px 0;
  font-size: 12px;
}

.knowledge-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.k-tag {
  padding: 4px 10px;
  background: #f5f5f5;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  font-size: 12px;
  color: #555;
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.r-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  font-size: 12px;
  color: #444;
}

.r-icon {
  font-size: 12px;
  color: #888;
}

/* 学习建议（已弃用） */

/* 路线详情视图 */
.path-header-section {
  margin-bottom: 16px;
}

.path-title-row {
  margin-bottom: 12px;
}

.path-title {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 6px 0;
}

.path-tags {
  display: flex;
  gap: 8px;
}

.path-tag {
  padding: 3px 10px;
  background: #f3f4f6;
  border-radius: 5px;
  font-size: 12px;
  color: #666;
}

.path-goal-card {
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 16px 20px;
}

.goal-label {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.goal-text {
  font-size: 14px;
  color: #1a1a1a;
  line-height: 1.6;
}

.path-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 10px;
}

.stat-icon {
  font-size: 22px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 17px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 12px;
  color: #888;
}

.stages-vertical {
  background: #fff;
  border: 1px solid #eaecef;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 16px;
}

.vertical-timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.vt-item {
  display: flex;
  gap: 14px;
  cursor: pointer;
}

.vt-item.completed .vt-title {
  color: #aaa;
}

.vt-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 32px;
  flex-shrink: 0;
}

.vt-dot {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #f0f0f0;
  border: 2px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #999;
  transition: all 0.2s;
  flex-shrink: 0;
}

.vt-item.active .vt-dot {
  background: #1a1a1a;
  border-color: #1a1a1a;
  color: #fff;
}

.vt-dot.done {
  background: #1a1a1a;
  border-color: #1a1a1a;
  color: #fff;
  font-size: 14px;
}

.vt-line {
  width: 2px;
  flex: 1;
  min-height: 20px;
  background: #e8e8e8;
  margin: 6px 0;
}

.vt-item.active .vt-line {
  background: #1a1a1a;
}

.vt-content {
  flex: 1;
  padding-bottom: 22px;
}

.vt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.vt-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.vt-duration {
  padding: 3px 9px;
  background: #f0f0f0;
  border-radius: 5px;
  font-size: 11px;
  color: #666;
  font-weight: 500;
}

.vt-goal {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
  margin: 0 0 6px 0;
}

.vt-detail {
  margin-top: 10px;
  padding: 14px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-label {
  font-size: 11px;
  font-weight: 600;
  color: #888;
}

.detail-value {
  font-size: 12px;
  color: #444;
  line-height: 1.5;
}

.detail-value.checkpoint {
  padding: 8px 12px;
  background: #fff;
  border-left: 3px solid #1a1a1a;
  border-radius: 0 5px 5px 0;
  font-size: 12px;
}

.detail-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.knowledge-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.k-tag {
  padding: 4px 9px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 11px;
  color: #555;
}

.resource-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.r-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 9px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 11px;
  color: #555;
}

.r-icon {
  font-size: 10px;
  color: #999;
}

.vt-detail-actions {
  padding-top: 4px;
}

.detail-btn {
  padding: 6px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: #fff;
  font-size: 12px;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
}

.detail-btn.primary {
  background: #1a1a1a;
  border-color: #1a1a1a;
  color: #fff;
}

.detail-btn.primary:hover {
  background: #333;
  border-color: #333;
}

.vt-expand-hint {
  font-size: 11px;
  color: #aaa;
}

/* 文本视图 */
.text-view-header {
  margin-bottom: 16px;
}

.path-submeta {
  font-size: 12px;
  color: #999;
  display: flex;
  gap: 6px;
}

.markdown-card {
  background: #fff;
  border: 1px solid #eaecef;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 16px;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 12px;
  width: 440px;
  max-width: 90vw;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.modal-close {
  width: 26px;
  height: 26px;
  border: none;
  background: transparent;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 5px;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #f5f5f5;
  color: #333;
}

.modal-body {
  padding: 18px 20px;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-item label {
  font-size: 12px;
  font-weight: 500;
  color: #333;
}

.form-item input,
.form-item select {
  height: 36px;
  padding: 0 10px;
  border: 1px solid #d9d9d9;
  border-radius: 7px;
  font-size: 13px;
  color: #1a1a1a;
  background: #fff;
  outline: none;
  transition: border-color 0.2s;
}

.form-item input:focus,
.form-item select:focus {
  border-color: #404040;
}

.required {
  color: #e53935;
}

.error-text {
  color: #e53935;
  font-size: 12px;
  margin: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #f0f0f0;
}

.btn-cancel {
  padding: 7px 18px;
  border: 1px solid #d9d9d9;
  border-radius: 7px;
  background: #fff;
  color: #333;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  border-color: #bbb;
}

.btn-primary {
  padding: 7px 20px;
  border: none;
  border-radius: 7px;
  background: #1a1a1a;
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #333;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
