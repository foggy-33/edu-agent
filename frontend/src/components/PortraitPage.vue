<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { chatDynamicProfile, getDynamicProfile, getNextProfileQuestion, listDynamicProfiles } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import { loadUserProfile } from '../api/userProfile'
import type { DynamicProfile, SubjectProfileSummary } from '../types/profile'

const defaultCourses = ['数据库系统', '数据结构', '算法设计', '操作系统', '计算机网络', '软件工程']
const userProfile = ref(loadUserProfile())
const portrait = ref<DynamicProfile | null>(null)
const subjectProfiles = ref<SubjectProfileSummary[]>([])
const course = ref('数据库系统')
const userMessage = ref('')
const loading = ref(false)
const error = ref('')
const replies = ref<{ role: 'assistant' | 'user'; content: string }[]>([])

const courses = computed(() => Array.from(new Set([...defaultCourses, ...subjectProfiles.value.map(item => item.course)])))
const dimensions = computed(() => portrait.value?.dimension_catalog || [])
const radarEntries = computed(() => Object.entries(portrait.value?.radar_metrics || {}))
const radarGrid = computed(() => [20, 40, 60, 80, 100].map(level => radarPolygon(level)))
const radarShape = computed(() => radarPolygon(100, radarEntries.value.map(([, value]) => value)))
const hasProfile = computed(() => Boolean(portrait.value?.version))

function point(index: number, value: number, count: number) {
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / count
  const radius = 88 * value / 100
  return `${110 + Math.cos(angle) * radius},${110 + Math.sin(angle) * radius}`
}

function radarPolygon(level: number, values?: number[]) {
  const count = Math.max(radarEntries.value.length, 6)
  return Array.from({ length: count }, (_, index) => point(index, values?.[index] ?? level, count)).join(' ')
}

function axisLabel(index: number, name: string) {
  const count = Math.max(radarEntries.value.length, 6)
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / count
  return {
    name,
    value: radarEntries.value[index]?.[1] ?? 0,
    x: 110 + Math.cos(angle) * 106,
    y: 110 + Math.sin(angle) * 106,
  }
}

function displayValue(value: string | string[] | undefined) {
  if (!value) return '等待对话补充'
  return Array.isArray(value) ? value.join('、') : value
}

function formatTime(value: string | null) {
  if (!value) return '尚未更新'
  return new Date(value).toLocaleString('zh-CN')
}

async function refreshSubjects() {
  const result = await listDynamicProfiles(userProfile.value.userId)
  subjectProfiles.value = result.profiles
}

async function loadPortrait(selectedCourse = course.value) {
  loading.value = true
  error.value = ''
  try {
    course.value = selectedCourse
    const result = await getDynamicProfile(userProfile.value.userId, selectedCourse)
    portrait.value = result.profile
    replies.value = []
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载学科画像失败'
  } finally {
    loading.value = false
  }
}

async function startInterview() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  replies.value = []
  try {
    const result = await getNextProfileQuestion({
      ...loadSiliconFlowConfig(),
      user_id: userProfile.value.userId,
      course: course.value,
    })
    portrait.value = result.profile
    replies.value.push({ role: 'assistant', content: result.question })
    if (result.warning) error.value = `提示：${result.warning}`
  } catch (err) {
    error.value = err instanceof Error ? err.message : '生成访谈问题失败'
  } finally {
    loading.value = false
  }
}

async function sendMessage() {
  const content = userMessage.value.trim()
  if (!content || loading.value) return
  replies.value.push({ role: 'user', content })
  userMessage.value = ''
  loading.value = true
  error.value = ''
  try {
    const result = await chatDynamicProfile({
      ...loadSiliconFlowConfig(),
      user_id: userProfile.value.userId,
      course: course.value,
      message: content,
    })
    portrait.value = result.profile
    replies.value.push({ role: 'assistant', content: result.reply })
    await refreshSubjects()
    if (result.warning) error.value = `提示：${result.warning}`
  } catch (err) {
    error.value = err instanceof Error ? err.message : '画像更新失败'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    await refreshSubjects()
    if (subjectProfiles.value[0]) course.value = subjectProfiles.value[0].course
    await loadPortrait(course.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载画像失败'
  }
})
</script>

<template>
  <div class="portrait-page">
    <aside class="subject-sidebar">
      <div class="panel-title">
        <div>
          <span class="eyebrow">SUBJECT PROFILES</span>
          <h2>各科画像</h2>
        </div>
        <span class="count">{{ subjectProfiles.length }}</span>
      </div>
      <p class="sidebar-tip">每个学科独立存储和更新，互不覆盖。</p>
      <div v-if="subjectProfiles.length" class="subject-list">
        <button
          v-for="item in subjectProfiles"
          :key="item.course"
          :class="['subject-card', { active: item.course === course }]"
          @click="loadPortrait(item.course)"
        >
          <div class="subject-card-top">
            <strong>{{ item.course }}</strong>
            <span>{{ item.completion }}%</span>
          </div>
          <div class="mini-progress"><span :style="{ width: item.completion + '%' }"></span></div>
          <small>V{{ item.version }} · {{ formatTime(item.updated_at) }}</small>
        </button>
      </div>
      <div v-else class="subject-empty">还没有已构建的学科画像</div>
    </aside>

    <main class="portrait-workspace">
      <section class="toolbar">
        <div>
          <span class="eyebrow">CURRENT SUBJECT</span>
          <h1>{{ course }}学习画像</h1>
        </div>
        <div class="course-actions">
          <select v-model="course" @change="loadPortrait(course)">
            <option v-for="item in courses" :key="item" :value="item">{{ item }}</option>
          </select>
          <button class="primary-button" :disabled="loading" @click="startInterview">
            {{ hasProfile ? '继续完善画像' : '开始构建画像' }}
          </button>
        </div>
      </section>

      <p v-if="error" class="warning">{{ error }}</p>

      <section class="overview-grid">
        <article class="radar-card">
          <div class="section-heading">
            <div>
              <span class="eyebrow">RADAR</span>
              <h3>学科能力雷达</h3>
            </div>
            <span class="completion">{{ portrait?.completion || 0 }}% 完成</span>
          </div>
          <svg class="radar" viewBox="0 0 220 220" role="img" :aria-label="`${course}画像雷达图`">
            <polygon v-for="grid in radarGrid" :key="grid" :points="grid" class="radar-grid" />
            <line
              v-for="(_, index) in radarEntries"
              :key="`axis-${index}`"
              x1="110" y1="110"
              :x2="point(index, 100, Math.max(radarEntries.length, 6)).split(',')[0]"
              :y2="point(index, 100, Math.max(radarEntries.length, 6)).split(',')[1]"
              class="radar-axis"
            />
            <polygon :points="radarShape" class="radar-value" />
            <g v-for="([name], index) in radarEntries" :key="name">
              <circle
                :cx="point(index, radarEntries[index][1], Math.max(radarEntries.length, 6)).split(',')[0]"
                :cy="point(index, radarEntries[index][1], Math.max(radarEntries.length, 6)).split(',')[1]"
                r="3.5" class="radar-dot"
              />
              <text
                :x="axisLabel(index, name).x"
                :y="axisLabel(index, name).y"
                text-anchor="middle"
                class="radar-label"
              >{{ name }} {{ axisLabel(index, name).value }}</text>
            </g>
          </svg>
        </article>

        <article class="context-card">
          <div class="section-heading">
            <div>
              <span class="eyebrow">LLM CONTEXT</span>
              <h3>大模型可读画像摘要</h3>
            </div>
            <span class="schema">{{ portrait?.llm_context?.schema_version || 'subject-profile-v1' }}</span>
          </div>
          <p class="context-summary">{{ portrait?.llm_context?.summary || `尚未构建${course}画像。开始访谈后，这里会形成可供大模型直接理解的结构化摘要。` }}</p>
          <div class="context-tags">
            <span v-for="item in portrait?.llm_context?.weak_points || []" :key="item" class="tag weak">{{ item }}</span>
            <span v-for="item in portrait?.llm_context?.resource_preferences || []" :key="item" class="tag preference">{{ item }}</span>
          </div>
          <div class="context-meta">
            <span>版本 V{{ portrait?.version || 0 }}</span>
            <span>{{ formatTime(portrait?.updated_at || null) }}</span>
          </div>
        </article>
      </section>

      <section v-if="replies.length" class="interview-card">
        <div class="section-heading">
          <div>
            <span class="eyebrow">INTERVIEW</span>
            <h3>{{ course }}画像访谈</h3>
          </div>
        </div>
        <div class="messages">
          <div v-for="(item, index) in replies" :key="index" :class="['message', item.role]">
            {{ item.content }}
          </div>
          <div v-if="loading" class="message assistant">正在理解并更新该科画像...</div>
        </div>
        <form class="message-form" @submit.prevent="sendMessage">
          <textarea v-model="userMessage" rows="2" :disabled="loading" :placeholder="`回答关于${course}的问题`"></textarea>
          <button class="primary-button" :disabled="loading || !userMessage.trim()">发送并更新</button>
        </form>
      </section>

      <section class="dimensions-card">
        <div class="section-heading">
          <div>
            <span class="eyebrow">EVIDENCE</span>
            <h3>画像维度与证据</h3>
          </div>
          <span class="completion">{{ Object.keys(portrait?.dimensions || {}).length }}/{{ dimensions.length }}</span>
        </div>
        <div class="dimension-grid">
          <article v-for="name in dimensions" :key="name" class="dimension-item">
            <div class="dimension-top">
              <strong>{{ name }}</strong>
              <span>{{ Math.round((portrait?.dimensions[name]?.confidence || 0) * 100) }}%</span>
            </div>
            <div class="confidence-track">
              <span :style="{ width: (portrait?.dimensions[name]?.confidence || 0) * 100 + '%' }"></span>
            </div>
            <p>{{ displayValue(portrait?.dimensions[name]?.value) }}</p>
            <small>{{ portrait?.dimensions[name]?.evidence || '继续访谈后补充证据' }}</small>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.portrait-page { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 18px; min-height: calc(100vh - 130px); color: #172033; }
.subject-sidebar, .toolbar, .radar-card, .context-card, .interview-card, .dimensions-card { background: #fff; border: 1px solid #e8ecf4; border-radius: 18px; box-shadow: 0 10px 30px rgba(37, 52, 89, .05); }
.subject-sidebar { padding: 18px; }
.panel-title, .section-heading, .toolbar, .subject-card-top, .dimension-top, .context-meta, .course-actions { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
h1, h2, h3, p { margin: 0; }
h1 { font-size: 24px; } h2 { font-size: 20px; } h3 { font-size: 17px; }
.eyebrow { display: block; color: #7a88a8; font-size: 10px; font-weight: 800; letter-spacing: .14em; margin-bottom: 5px; }
.count, .completion, .schema { border-radius: 999px; background: #eef2ff; color: #5968d9; font-size: 12px; padding: 5px 9px; }
.sidebar-tip { margin: 14px 0; color: #7a8499; font-size: 12px; line-height: 1.6; }
.subject-list { display: grid; gap: 9px; }
.subject-card { width: 100%; padding: 12px; text-align: left; border: 1px solid #edf0f6; border-radius: 12px; background: #fafbfe; cursor: pointer; color: inherit; }
.subject-card.active { border-color: #6d75e8; background: #f1f2ff; }
.subject-card small, .dimension-item small { color: #8b94a8; font-size: 11px; line-height: 1.5; }
.mini-progress, .confidence-track { height: 4px; background: #e9edf5; border-radius: 99px; overflow: hidden; margin: 8px 0; }
.mini-progress span, .confidence-track span { display: block; height: 100%; background: linear-gradient(90deg, #6875e8, #62c3aa); border-radius: inherit; }
.subject-empty { padding: 26px 10px; text-align: center; color: #939bad; font-size: 13px; border: 1px dashed #dfe4ed; border-radius: 12px; }
.portrait-workspace { display: grid; align-content: start; gap: 18px; min-width: 0; }
.toolbar { padding: 18px 22px; }
select, textarea { border: 1px solid #dfe4ed; border-radius: 10px; background: #fff; color: inherit; font: inherit; }
select { padding: 9px 12px; } textarea { width: 100%; padding: 11px 13px; resize: vertical; box-sizing: border-box; }
.primary-button { border: 0; border-radius: 10px; background: #626ce0; color: #fff; padding: 10px 15px; font-weight: 700; cursor: pointer; }
.primary-button:disabled { opacity: .55; cursor: default; }
.warning { padding: 10px 14px; border-radius: 10px; background: #fff7df; color: #966b16; font-size: 13px; }
.overview-grid { display: grid; grid-template-columns: minmax(360px, .9fr) minmax(360px, 1.1fr); gap: 18px; }
.radar-card, .context-card, .interview-card, .dimensions-card { padding: 20px; }
.radar { display: block; width: min(100%, 390px); margin: 8px auto 0; overflow: visible; }
.radar-grid { fill: rgba(100, 112, 224, .025); stroke: #dfe4ef; stroke-width: .8; }
.radar-axis { stroke: #e4e8f0; stroke-width: .8; }
.radar-value { fill: rgba(99, 108, 224, .22); stroke: #636ce0; stroke-width: 2; }
.radar-dot { fill: #fff; stroke: #636ce0; stroke-width: 2; }
.radar-label { fill: #596278; font-size: 8px; font-weight: 600; }
.context-card { display: flex; flex-direction: column; }
.context-summary { margin: 24px 0; padding: 16px; border-left: 3px solid #6875e8; border-radius: 0 12px 12px 0; background: #f7f8fd; color: #4f5b73; line-height: 1.8; font-size: 14px; }
.context-tags { display: flex; flex-wrap: wrap; gap: 7px; }
.tag { padding: 5px 9px; border-radius: 999px; font-size: 11px; }
.tag.weak { background: #fff0ef; color: #bc5b53; }.tag.preference { background: #eaf8f4; color: #278a72; }
.context-meta { margin-top: auto; padding-top: 20px; color: #929bad; font-size: 11px; }
.messages { display: grid; gap: 9px; margin: 16px 0; max-height: 260px; overflow-y: auto; }
.message { max-width: 76%; padding: 10px 13px; border-radius: 12px; background: #f0f2f7; line-height: 1.6; font-size: 13px; }
.message.user { justify-self: end; background: #646de0; color: #fff; }
.message-form { display: flex; align-items: end; gap: 10px; }
.message-form textarea { flex: 1; }
.dimension-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 16px; }
.dimension-item { padding: 14px; border: 1px solid #edf0f6; border-radius: 13px; background: #fafbfe; }
.dimension-top span { color: #6875e8; font-size: 12px; font-weight: 700; }
.dimension-item p { margin: 10px 0 6px; color: #455069; font-size: 13px; line-height: 1.6; }
@media (max-width: 1100px) { .portrait-page { grid-template-columns: 1fr; }.subject-list { grid-template-columns: repeat(2, 1fr); }.overview-grid { grid-template-columns: 1fr; } }
@media (max-width: 700px) { .toolbar, .course-actions, .message-form { align-items: stretch; flex-direction: column; }.dimension-grid, .subject-list { grid-template-columns: 1fr; } }
</style>
