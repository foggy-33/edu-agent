<script setup lang="ts">
import { computed, ref } from 'vue'
import { generateCollaborativeLearning } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import type { CollaborativeLearningRequest, CollaborativeLearningResponse, CollaborativeResourceType } from '../types'
import MarkdownRenderer from './MarkdownRenderer.vue'
import MermaidRenderer from './MermaidRenderer.vue'

const resourceOptions: { key: CollaborativeResourceType; label: string; icon: string }[] = [
  { key: 'lecture', label: '课程讲解', icon: '文' },
  { key: 'mindmap', label: '思维导图', icon: '图' },
  { key: 'exercise', label: '练习题', icon: '练' },
  { key: 'reading', label: '拓展阅读', icon: '读' },
  { key: 'code', label: '代码实操', icon: '码' },
  { key: 'video', label: '视频脚本', icon: '视' },
]

const expectedAgents = ['学情分析', '任务规划', '课程讲解', '思维导图', '练习题', '拓展阅读', '代码实操', '视频脚本', '质量审核', '资源整合']
const apiConfig = ref(loadSiliconFlowConfig())
const form = ref<CollaborativeLearningRequest>({
  major: '计算机科学与技术',
  course: '操作系统',
  chapter: '进程调度',
  weakness: '不会区分 FCFS、SJF 和时间片轮转',
  goal: '期末复习',
  resourceTypes: resourceOptions.map(item => item.key),
  ...apiConfig.value,
})
const loading = ref(false)
const error = ref('')
const result = ref<CollaborativeLearningResponse | null>(null)
const activeTab = ref<keyof Omit<CollaborativeLearningResponse, 'agentTrace'>>('lectureDoc')

const tabs: { key: keyof Omit<CollaborativeLearningResponse, 'agentTrace'>; label: string }[] = [
  { key: 'lectureDoc', label: '讲解文档' },
  { key: 'mindmap', label: '思维导图' },
  { key: 'exercises', label: '练习题' },
  { key: 'reading', label: '拓展阅读' },
  { key: 'codeCase', label: '代码案例' },
  { key: 'videoScript', label: '视频脚本' },
  { key: 'review', label: '审核结果' },
]
const activeContent = computed(() => result.value?.[activeTab.value] || '')

function toggleResource(key: CollaborativeResourceType) {
  form.value.resourceTypes = form.value.resourceTypes.includes(key)
    ? form.value.resourceTypes.filter(item => item !== key)
    : [...form.value.resourceTypes, key]
}

async function submit() {
  if (!form.value.resourceTypes.length) {
    error.value = '请至少选择一种资源类型'
    return
  }
  loading.value = true
  apiConfig.value = loadSiliconFlowConfig()
  form.value = { ...form.value, ...apiConfig.value }
  error.value = ''
  result.value = null
  try {
    result.value = await generateCollaborativeLearning(form.value)
    activeTab.value = 'lectureDoc'
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '资源生成失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="collab-page">
    <section class="surface collab-form-card">
      <div class="collab-heading">
        <div><span class="section-kicker">LangGraph 多智能体协作</span><h2>个性化资源生成</h2><p>填写学习上下文，由十个智能体协同生成完整资源包。</p></div>
        <span :class="['collab-mode', apiConfig.api_key ? 'configured' : '']">{{ apiConfig.api_key ? `使用设置中的模型：${apiConfig.model}` : '设置中未填写 API Key，将使用 Mock' }}</span>
      </div>
      <form class="collab-form" @submit.prevent="submit">
        <label><span>专业</span><input v-model.trim="form.major" required /></label>
        <label><span>课程</span><input v-model.trim="form.course" required /></label>
        <label><span>章节</span><input v-model.trim="form.chapter" required /></label>
        <label><span>学习目标</span><input v-model.trim="form.goal" required /></label>
        <label class="collab-wide"><span>知识短板</span><textarea v-model.trim="form.weakness" rows="3" required /></label>
        <fieldset class="collab-wide">
          <legend>资源类型</legend>
          <button v-for="item in resourceOptions" :key="item.key" type="button" :class="{ selected: form.resourceTypes.includes(item.key) }" @click="toggleResource(item.key)">
            <b>{{ item.icon }}</b>{{ item.label }}
          </button>
        </fieldset>
        <div v-if="error" class="auth-error collab-wide">{{ error }}</div>
        <button class="collab-generate collab-wide" :disabled="loading">{{ loading ? '智能体协作生成中...' : '启动多智能体资源生成' }}</button>
      </form>
    </section>

    <section class="surface trace-card">
      <div class="collab-heading"><div><span class="section-kicker">执行流程</span><h2>Agent 协作轨迹</h2></div><strong>{{ result?.agentTrace.length || 0 }}/10</strong></div>
      <div class="trace-grid">
        <article v-for="(agent, index) in expectedAgents" :key="agent" :class="{ done: result?.agentTrace[index], running: loading && index === 0 }">
          <span>{{ result?.agentTrace[index] ? '✓' : index + 1 }}</span>
          <div><b>{{ result?.agentTrace[index]?.agent || `${agent} Agent` }}</b><small>{{ result?.agentTrace[index]?.summary || (loading ? '等待协作结果...' : '等待执行') }}</small></div>
        </article>
      </div>
    </section>

    <section v-if="result" class="surface result-card">
      <div class="result-tabs">
        <button v-for="tab in tabs" :key="tab.key" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">{{ tab.label }}</button>
      </div>
      <div class="result-content">
        <MermaidRenderer v-if="activeTab === 'mindmap'" :chart="activeContent" />
        <MarkdownRenderer v-else :content="activeContent" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.collab-page { display: grid; gap: 20px; }
.collab-form-card, .trace-card, .result-card { padding: 24px; }
.collab-heading { display: flex; align-items: start; justify-content: space-between; gap: 20px; margin-bottom: 20px; }
.collab-heading h2 { margin: 5px 0; color: #172033; font-size: 22px; }
.collab-heading p { margin: 0; color: #7a8495; }
.collab-mode { padding: 7px 10px; border-radius: 999px; color: #5146cf; background: #efedff; font-size: 12px; font-weight: 700; }
.collab-mode.configured { color: #166534; background: #dcfce7; }
.collab-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.collab-form label { display: grid; gap: 7px; color: #4b5563; font-size: 13px; font-weight: 650; }
.collab-form input, .collab-form textarea { width: 100%; padding: 11px 12px; border: 1px solid #dfe3eb; border-radius: 10px; resize: vertical; }
.collab-wide { grid-column: 1 / -1; }
fieldset { display: flex; flex-wrap: wrap; gap: 9px; padding: 14px; border: 1px solid #e7eaf1; border-radius: 12px; }
legend { padding: 0 6px; color: #4b5563; font-size: 13px; font-weight: 650; }
fieldset button { display: flex; align-items: center; gap: 7px; padding: 9px 11px; border: 1px solid #e1e4eb; border-radius: 9px; color: #697386; background: #fff; }
fieldset button b { display: grid; place-items: center; width: 23px; height: 23px; border-radius: 6px; color: #5146cf; background: #efedff; font-size: 11px; }
fieldset button.selected { border-color: #6d5de7; color: #433aa8; background: #f8f7ff; }
.collab-generate { padding: 13px; border: 0; border-radius: 11px; color: #fff; background: linear-gradient(135deg, #5146cf, #6d5de7); font-weight: 750; }
.collab-generate:disabled { cursor: wait; opacity: .65; }
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
@media (max-width: 760px) { .collab-form, .trace-grid { grid-template-columns: 1fr; } .collab-heading { flex-direction: column; } }
</style>
