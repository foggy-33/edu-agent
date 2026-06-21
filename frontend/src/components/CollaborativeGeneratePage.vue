<script setup lang="ts">
import { computed, ref } from 'vue'
import { generateCollaborativeLearning } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import type { CollaborativeLearningRequest, CollaborativeLearningResponse, CollaborativeResourceType } from '../types'
import MarkdownRenderer from './MarkdownRenderer.vue'
import MermaidRenderer from './MermaidRenderer.vue'

type ResultKey = 'lectureDoc' | 'mindmap' | 'exercises' | 'reading' | 'review'

const resourceOptions: {
  key: CollaborativeResourceType
  resultKey: ResultKey
  label: string
  description: string
  icon: string
}[] = [
  { key: 'lecture', resultKey: 'lectureDoc', label: '课程讲解', description: '概念、原理与例子', icon: '📄' },
  { key: 'mindmap', resultKey: 'mindmap', label: '思维导图', description: '梳理知识结构', icon: '🧠' },
  { key: 'exercise', resultKey: 'exercises', label: '练习题', description: '分层题目与解析', icon: '✍️' },
  { key: 'reading', resultKey: 'reading', label: '拓展阅读', description: '延伸知识与路径', icon: '📚' },
]

const apiConfig = ref(loadSiliconFlowConfig())
const form = ref<CollaborativeLearningRequest>({
  major: '计算机科学与技术',
  course: '操作系统',
  chapter: '进程调度',
  weakness: '不会区分 FCFS、SJF 和时间片轮转',
  goal: '期末复习',
  resourceTypes: ['lecture', 'mindmap', 'exercise'],
  ...apiConfig.value,
})
const submittedTypes = ref<CollaborativeResourceType[]>([])
const loading = ref(false)
const error = ref('')
const result = ref<CollaborativeLearningResponse | null>(null)
const activeTab = ref<ResultKey>('lectureDoc')

const availableTabs = computed(() => {
  const selected = submittedTypes.value.length ? submittedTypes.value : form.value.resourceTypes
  return [
    ...resourceOptions
      .filter(item => selected.includes(item.key))
      .map(item => ({ key: item.resultKey, label: item.label })),
    { key: 'review' as ResultKey, label: '审核结果' },
  ]
})

const expectedAgents = computed(() => {
  const selected = submittedTypes.value.length ? submittedTypes.value : form.value.resourceTypes
  const resourceAgents: Record<CollaborativeResourceType, string> = {
    lecture: '课程讲解',
    mindmap: '思维导图',
    exercise: '练习题',
    reading: '拓展阅读',
  }
  return ['学情分析', '任务规划', ...selected.map(item => resourceAgents[item]), '质量审核', '资源整合']
})

const activeContent = computed(() => result.value?.[activeTab.value] || '')
const selectedSummary = computed(() => resourceOptions
  .filter(item => form.value.resourceTypes.includes(item.key))
  .map(item => item.label)
  .join('、'))

function toggleResource(key: CollaborativeResourceType) {
  form.value.resourceTypes = form.value.resourceTypes.includes(key)
    ? form.value.resourceTypes.filter(item => item !== key)
    : [...form.value.resourceTypes, key]
}

async function submit() {
  if (!form.value.weakness.trim()) {
    error.value = '请描述你想学习或解决的问题'
    return
  }
  if (!form.value.resourceTypes.length) {
    error.value = '请至少选择一种资源类型'
    return
  }

  loading.value = true
  apiConfig.value = loadSiliconFlowConfig()
  form.value = { ...form.value, ...apiConfig.value }
  submittedTypes.value = [...form.value.resourceTypes]
  error.value = ''
  result.value = null
  activeTab.value = resourceOptions.find(item => submittedTypes.value.includes(item.key))?.resultKey || 'review'

  try {
    result.value = await generateCollaborativeLearning(form.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '资源生成失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="resource-page">
    <section class="resource-hero">
      <span class="hero-badge">AI 学习资源生成器</span>
      <h2>今天想学点什么？</h2>
      <p>描述你的学习问题，并选择需要生成的资源。AI 会结合课程、目标和知识短板组织内容。</p>
    </section>

    <section class="composer-card">
      <div class="context-grid">
        <label><span>专业</span><input v-model.trim="form.major" /></label>
        <label><span>课程</span><input v-model.trim="form.course" /></label>
        <label><span>章节</span><input v-model.trim="form.chapter" /></label>
        <label><span>学习目标</span><input v-model.trim="form.goal" /></label>
      </div>

      <div class="prompt-box">
        <textarea
          v-model.trim="form.weakness"
          rows="5"
          placeholder="例如：我总是分不清 FCFS、SJF 和时间片轮转，希望用对比案例讲清楚，并生成一份思维导图和练习题。"
          @keydown.ctrl.enter="submit"
        />

        <div class="prompt-footer">
          <div class="resource-chips">
            <button
              v-for="item in resourceOptions"
              :key="item.key"
              type="button"
              :class="{ selected: form.resourceTypes.includes(item.key) }"
              :title="item.description"
              @click="toggleResource(item.key)"
            >
              <span>{{ item.icon }}</span>{{ item.label }}
              <i v-if="form.resourceTypes.includes(item.key)">✓</i>
            </button>
          </div>
          <button class="send-button" :disabled="loading" title="生成资源（Ctrl + Enter）" @click="submit">
            {{ loading ? '…' : '↑' }}
          </button>
        </div>
      </div>

      <div class="composer-meta">
        <span>{{ selectedSummary || '尚未选择资源类型' }}</span>
        <span :class="{ configured: apiConfig.api_key }">
          {{ apiConfig.api_key ? `模型：${apiConfig.model}` : '未配置 API Key，将使用 Mock' }}
        </span>
      </div>
      <div v-if="error" class="composer-error">{{ error }}</div>
    </section>

    <section v-if="loading || result" class="surface trace-card">
      <div class="section-heading">
        <div><span class="section-kicker">执行流程</span><h2>多智能体协作轨迹</h2></div>
        <strong>{{ result?.agentTrace.length || 0 }}/{{ expectedAgents.length }}</strong>
      </div>
      <div class="trace-grid">
        <article
          v-for="(agent, index) in expectedAgents"
          :key="agent"
          :class="{ done: result?.agentTrace[index], running: loading && index === 0 }"
        >
          <span>{{ result?.agentTrace[index] ? '✓' : index + 1 }}</span>
          <div>
            <b>{{ result?.agentTrace[index]?.agent || `${agent} Agent` }}</b>
            <small>{{ result?.agentTrace[index]?.summary || (loading ? '正在组织生成任务...' : '等待执行') }}</small>
          </div>
        </article>
      </div>
    </section>

    <section v-if="result" class="surface result-card">
      <div class="result-tabs">
        <button
          v-for="tab in availableTabs"
          :key="tab.key"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="result-content">
        <MermaidRenderer v-if="activeTab === 'mindmap'" :chart="activeContent" />
        <MarkdownRenderer v-else :content="activeContent" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.resource-page { display: grid; gap: 22px; max-width: 1080px; margin: 0 auto; }
.resource-hero { padding: 18px 12px 2px; text-align: center; }
.hero-badge { display: inline-flex; padding: 6px 11px; border-radius: 999px; color: #5146cf; background: #efedff; font-size: 12px; font-weight: 750; }
.resource-hero h2 { margin: 14px 0 8px; color: #172033; font-size: clamp(28px, 4vw, 42px); letter-spacing: -.04em; }
.resource-hero p { max-width: 680px; margin: 0 auto; color: #7a8495; line-height: 1.7; }
.composer-card { padding: 18px; border: 1px solid #e2e5ec; border-radius: 24px; background: #fff; box-shadow: 0 18px 55px rgba(31, 42, 68, .1); }
.context-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 12px; }
.context-grid label { display: grid; gap: 5px; }
.context-grid span { color: #7c8495; font-size: 11px; font-weight: 700; }
.context-grid input { min-width: 0; padding: 9px 10px; border: 1px solid #e6e8ee; border-radius: 10px; color: #30384a; background: #fafbfc; }
.prompt-box { overflow: hidden; border: 1px solid #dfe3ea; border-radius: 18px; background: #fff; transition: border-color .2s, box-shadow .2s; }
.prompt-box:focus-within { border-color: #7769e8; box-shadow: 0 0 0 4px rgba(109, 93, 231, .1); }
.prompt-box textarea { width: 100%; padding: 18px 18px 10px; border: 0; outline: 0; resize: none; color: #202939; background: transparent; font-size: 15px; line-height: 1.65; }
.prompt-footer { display: flex; align-items: end; justify-content: space-between; gap: 14px; padding: 10px 12px 12px; }
.resource-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.resource-chips button { display: flex; align-items: center; gap: 6px; padding: 8px 11px; border: 1px solid #e2e5eb; border-radius: 999px; color: #60697a; background: #fff; font-size: 12px; font-weight: 650; }
.resource-chips button:hover { background: #f7f7fb; }
.resource-chips button.selected { border-color: #c9c3ff; color: #473daf; background: #f1efff; }
.resource-chips i { display: grid; place-items: center; width: 16px; height: 16px; border-radius: 50%; color: #fff; background: #6254d8; font-size: 10px; font-style: normal; }
.send-button { width: 42px; height: 42px; flex: 0 0 auto; border: 0; border-radius: 50%; color: #fff; background: #202123; font-size: 24px; line-height: 1; }
.send-button:hover { background: #5146cf; }
.send-button:disabled { cursor: wait; opacity: .5; }
.composer-meta { display: flex; justify-content: space-between; gap: 12px; padding: 11px 3px 0; color: #8b93a3; font-size: 11px; }
.composer-meta .configured { color: #15803d; }
.composer-error { margin-top: 12px; padding: 11px 13px; border-radius: 10px; color: #a33333; background: #fff1f1; font-size: 13px; }
.trace-card { padding: 24px; }
.section-heading { display: flex; align-items: start; justify-content: space-between; gap: 20px; margin-bottom: 18px; }
.section-heading h2 { margin: 5px 0 0; color: #172033; font-size: 21px; }
.section-heading strong { color: #5146cf; }
.trace-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.trace-grid article { display: flex; gap: 10px; padding: 12px; border: 1px solid #e7eaf1; border-radius: 11px; background: #fafbfc; }
.trace-grid article > span { width: 27px; height: 27px; flex: 0 0 auto; display: grid; place-items: center; border-radius: 50%; color: #8b93a3; background: #eef0f4; font-size: 12px; font-weight: 800; }
.trace-grid article div { display: grid; gap: 3px; }
.trace-grid article b { color: #444d5f; font-size: 13px; }
.trace-grid article small { color: #969ead; }
.trace-grid article.done { border-color: #d8d4ff; background: #f8f7ff; }
.trace-grid article.done > span { color: #fff; background: #5146cf; }
.trace-grid article.running { animation: pulse 1.2s infinite; }
.result-card { padding: 0; overflow: hidden; }
.result-tabs { display: flex; gap: 4px; padding: 12px 12px 0; overflow-x: auto; border-bottom: 1px solid #e7eaf1; }
.result-tabs button { padding: 11px 14px; border: 0; border-radius: 9px 9px 0 0; color: #697386; background: transparent; white-space: nowrap; font-weight: 650; }
.result-tabs button.active { color: #5146cf; background: #efedff; }
.result-content { padding: 24px; }
@keyframes pulse { 50% { opacity: .55; } }
@media (max-width: 800px) {
  .context-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .trace-grid { grid-template-columns: 1fr; }
}
@media (max-width: 520px) {
  .context-grid { grid-template-columns: 1fr; }
  .prompt-footer, .composer-meta { align-items: stretch; flex-direction: column; }
  .send-button { align-self: flex-end; }
}
</style>
