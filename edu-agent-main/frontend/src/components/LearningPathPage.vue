<script setup lang="ts">
import { computed, ref } from 'vue'
import { generateLearningResources } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import { loadUserProfile } from '../api/userProfile'
import MarkdownRenderer from './MarkdownRenderer.vue'

const emit = defineEmits<{
  navigate: [page: 'home' | 'analyze' | 'collaborative' | 'evaluate' | 'courses' | 'account' | 'portrait' | 'resources']
}>()

const userProfile = ref(loadUserProfile())
const modelConfig = ref(loadSiliconFlowConfig())

const course = ref('数据库系统')
const chapter = ref('')
const weakness = ref('')
const goal = ref('考试复习')

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

const generating = ref(false)
const error = ref('')
const learningPath = ref('')
const generated = ref(false)

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

const parsedStages = computed<PathStage[]>(() => {
  if (!learningPath.value) return []
  const stages: PathStage[] = []
  const stageRegex = /###\s*阶段[一二三四五六七八九十\d]+[：:]\s*(.+?)\n/g
  let match
  let index = 0
  const text = learningPath.value

  const stageBlocks = text.split(/###\s*阶段[一二三四五六七八九十\d]+[：:]\s*/).slice(1)
  const stageTitles = text.match(/###\s*阶段[一二三四五六七八九十\d]+[：:]\s*(.+)/g)?.map(s => s.replace(/###\s*阶段[一二三四五六七八九十\d]+[：:]\s*/, '')) || []

  stageBlocks.forEach((block, i) => {
    const title = stageTitles[i] || `阶段${i + 1}`
    const lines = block.split('\n')

    let goal = ''
    let knowledge: string[] = []
    let resources: string[] = []
    let duration = ''
    let dependency = ''
    let checkpoint = ''

    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed.startsWith('- **学习目标**') || trimmed.startsWith('- **学习目标**：')) {
        goal = trimmed.replace(/^- \*\*学习目标\*\*[：:]\s*/, '')
      } else if (trimmed.startsWith('- **核心知识点**') || trimmed.startsWith('- **核心知识点**：')) {
        const k = trimmed.replace(/^- \*\*核心知识点\*\*[：:]\s*/, '')
        knowledge = k.split(/[、，,]/).map(s => s.trim()).filter(Boolean)
      } else if (trimmed.startsWith('- **推荐资源**') || trimmed.startsWith('- **推荐资源**：')) {
        const r = trimmed.replace(/^- \*\*推荐资源\*\*[：:]\s*/, '')
        resources = r.split(/[、，,]/).map(s => s.trim()).filter(Boolean)
      } else if (trimmed.startsWith('- **预计时长**') || trimmed.startsWith('- **预计时长**：')) {
        duration = trimmed.replace(/^- \*\*预计时长\*\*[：:]\s*/, '')
      } else if (trimmed.startsWith('- **依赖关系**') || trimmed.startsWith('- **依赖关系**：')) {
        dependency = trimmed.replace(/^- \*\*依赖关系\*\*[：:]\s*/, '')
      } else if (trimmed.startsWith('- **检验标准**') || trimmed.startsWith('- **检验标准**：')) {
        checkpoint = trimmed.replace(/^- \*\*检验标准\*\*[：:]\s*/, '')
      }
    }

    stages.push({
      index: i + 1,
      title,
      goal,
      knowledge,
      resources,
      duration,
      dependency,
      checkpoint,
    })
  })

  return stages
})

const totalDuration = computed(() => {
  let totalDays = 0
  for (const stage of parsedStages.value) {
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
  return totalDays ? `约 ${Math.round(totalDays)} 天` : '待生成'
})

async function generatePath() {
  if (!chapter.value.trim()) {
    error.value = '请输入章节或知识点'
    return
  }
  error.value = ''
  generating.value = true
  learningPath.value = ''
  generated.value = false

  try {
    const result = await generateLearningResources({
      user_id: userProfile.value.userId,
      major: '未指定',
      course: course.value,
      chapter: chapter.value,
      weakness: weakness.value || chapter.value,
      goal: goal.value,
      resourceTypes: ['path'],
      fileIds: [],
      api_key: modelConfig.value.api_key,
      base_url: modelConfig.value.base_url,
      model: modelConfig.value.model,
    })
    learningPath.value = result.learningPath || ''
    generated.value = true
  } catch (e) {
    error.value = (e as Error).message || '生成失败，请重试'
  } finally {
    generating.value = false
  }
}

const activeStageIndex = ref(0)

function selectStage(index: number) {
  activeStageIndex.value = index
}
</script>

<template>
  <div class="learning-path-page">
    <header class="page-header">
      <h1 class="page-title">学习路线图</h1>
      <p class="page-subtitle">规划科学、动态的个性化学习路径，明确学习步骤和顺序</p>
    </header>

    <section class="path-generator">
      <div class="generator-card">
        <div class="generator-title">生成学习路径</div>
        <div class="generator-form">
          <div class="form-row">
            <div class="form-item">
              <label>课程</label>
              <select v-model="course">
                <option v-for="c in courseOptions" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div class="form-item">
              <label>学习目标</label>
              <select v-model="goal">
                <option v-for="g in goalOptions" :key="g" :value="g">{{ g }}</option>
              </select>
            </div>
          </div>
          <div class="form-item">
            <label>章节 / 知识点</label>
            <input
              v-model="chapter"
              type="text"
              placeholder="例如：关系数据库标准语言 SQL"
            />
          </div>
          <div class="form-item">
            <label>薄弱点（选填）</label>
            <input
              v-model="weakness"
              type="text"
              placeholder="例如：嵌套查询、视图、索引"
            />
          </div>
          <button
            class="generate-btn"
            :disabled="generating || !chapter.trim()"
            @click="generatePath"
          >
            <span v-if="generating">生成中...</span>
            <span v-else>生成学习路线</span>
          </button>
          <p v-if="error" class="error-text">{{ error }}</p>
        </div>
      </div>
    </section>

    <section v-if="generated && parsedStages.length" class="path-visualization">
      <div class="path-overview">
        <div class="overview-card">
          <div class="overview-value">{{ parsedStages.length }}</div>
          <div class="overview-label">学习阶段</div>
        </div>
        <div class="overview-card">
          <div class="overview-value">{{ totalDuration }}</div>
          <div class="overview-label">预计总时长</div>
        </div>
        <div class="overview-card">
          <div class="overview-value">{{ course }}</div>
          <div class="overview-label">目标课程</div>
        </div>
      </div>

      <div class="timeline-section">
        <h3 class="section-title">学习阶段时间线</h3>
        <div class="timeline">
          <div
            v-for="(stage, index) in parsedStages"
            :key="stage.index"
            class="timeline-item"
            :class="{ active: activeStageIndex === index, completed: activeStageIndex > index }"
            @click="selectStage(index)"
          >
            <div class="timeline-dot">
              <span class="dot-number">{{ stage.index }}</span>
            </div>
            <div v-if="index < parsedStages.length - 1" class="timeline-line"></div>
            <div class="timeline-content">
              <div class="stage-title">{{ stage.title }}</div>
              <div class="stage-duration">{{ stage.duration }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="stage-detail-section">
        <div class="stage-detail-card">
          <div class="stage-header">
            <div class="stage-badge">阶段 {{ parsedStages[activeStageIndex]?.index }}</div>
            <h3 class="stage-name">{{ parsedStages[activeStageIndex]?.title }}</h3>
          </div>

          <div class="stage-body">
            <div class="detail-item">
              <div class="detail-label">学习目标</div>
              <div class="detail-value">{{ parsedStages[activeStageIndex]?.goal }}</div>
            </div>

            <div class="detail-item">
              <div class="detail-label">核心知识点</div>
              <div class="detail-tag-list">
                <span
                  v-for="k in parsedStages[activeStageIndex]?.knowledge"
                  :key="k"
                  class="knowledge-tag"
                >{{ k }}</span>
              </div>
            </div>

            <div class="detail-item">
              <div class="detail-label">推荐学习资源</div>
              <div class="resource-list">
                <div
                  v-for="(r, i) in parsedStages[activeStageIndex]?.resources"
                  :key="i"
                  class="resource-item"
                >
                  <span class="resource-icon">▣</span>
                  <span class="resource-name">{{ r }}</span>
                </div>
              </div>
            </div>

            <div class="detail-row">
              <div class="detail-item">
                <div class="detail-label">预计时长</div>
                <div class="detail-value highlight">{{ parsedStages[activeStageIndex]?.duration }}</div>
              </div>
              <div class="detail-item">
                <div class="detail-label">前置依赖</div>
                <div class="detail-value">{{ parsedStages[activeStageIndex]?.dependency }}</div>
              </div>
            </div>

            <div class="detail-item">
              <div class="detail-label">检验标准</div>
              <div class="detail-value checkpoint">{{ parsedStages[activeStageIndex]?.checkpoint }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="full-markdown-section">
        <h3 class="section-title">完整学习路径</h3>
        <div class="markdown-card">
          <MarkdownRenderer :content="learningPath" />
        </div>
      </div>
    </section>

    <section v-else-if="!generating" class="empty-state">
      <div class="empty-icon">↗</div>
      <h3 class="empty-title">还没有学习路线</h3>
      <p class="empty-desc">输入章节和目标，生成你的个性化学习路径</p>
    </section>
  </div>
</template>

<style scoped>
.learning-path-page {
  padding: 32px 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.path-generator {
  margin-bottom: 40px;
}

.generator-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 28px;
}

.generator-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 20px;
}

.generator-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item label {
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.form-item input,
.form-item select {
  height: 40px;
  padding: 0 12px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  font-size: 14px;
  color: #1a1a1a;
  background: #fff;
  outline: none;
  transition: border-color 0.2s;
}

.form-item input:focus,
.form-item select:focus {
  border-color: #404040;
}

.generate-btn {
  height: 44px;
  border: none;
  border-radius: 8px;
  background: #1a1a1a;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.generate-btn:hover:not(:disabled) {
  background: #333;
}

.generate-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error-text {
  color: #e53935;
  font-size: 13px;
  margin: 0;
}

.path-overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.overview-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}

.overview-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.overview-label {
  font-size: 13px;
  color: #666;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 20px 0;
}

.timeline-section {
  margin-bottom: 32px;
}

.timeline {
  display: flex;
  align-items: flex-start;
  gap: 0;
  padding: 20px 0;
  overflow-x: auto;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-width: 120px;
  position: relative;
  cursor: pointer;
}

.timeline-dot {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #f0f0f0;
  border: 2px solid #d9d9d9;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  transition: all 0.2s;
  z-index: 2;
}

.timeline-item.active .timeline-dot {
  background: #1a1a1a;
  border-color: #1a1a1a;
}

.timeline-item.completed .timeline-dot {
  background: #4caf50;
  border-color: #4caf50;
}

.dot-number {
  font-size: 16px;
  font-weight: 700;
  color: #666;
}

.timeline-item.active .dot-number,
.timeline-item.completed .dot-number {
  color: #fff;
}

.timeline-line {
  position: absolute;
  top: 23px;
  left: 50%;
  width: 100%;
  height: 3px;
  background: #e0e0e0;
  z-index: 1;
}

.timeline-item.completed .timeline-line {
  background: #4caf50;
}

.timeline-content {
  text-align: center;
  padding: 0 8px;
}

.stage-title {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.stage-duration {
  font-size: 12px;
  color: #999;
}

.stage-detail-section {
  margin-bottom: 32px;
}

.stage-detail-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  overflow: hidden;
}

.stage-header {
  padding: 24px 28px;
  border-bottom: 1px solid #f0f0f0;
}

.stage-badge {
  display: inline-block;
  padding: 4px 10px;
  background: #f0f0f0;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
}

.stage-name {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0;
}

.stage-body {
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-label {
  font-size: 13px;
  font-weight: 600;
  color: #666;
}

.detail-value {
  font-size: 15px;
  color: #1a1a1a;
  line-height: 1.6;
}

.detail-value.highlight {
  font-weight: 600;
  color: #1a1a1a;
}

.detail-value.checkpoint {
  padding: 12px 16px;
  background: #f9f9f9;
  border-left: 3px solid #1a1a1a;
  border-radius: 0 6px 6px 0;
}

.detail-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.detail-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.knowledge-tag {
  padding: 6px 12px;
  background: #f5f5f5;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  font-size: 13px;
  color: #333;
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.resource-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
}

.resource-icon {
  font-size: 14px;
  color: #666;
}

.resource-name {
  font-size: 14px;
  color: #1a1a1a;
}

.full-markdown-section {
  margin-bottom: 40px;
}

.markdown-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 28px;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 48px;
  color: #ccc;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.empty-desc {
  font-size: 14px;
  color: #999;
  margin: 0;
}
</style>
