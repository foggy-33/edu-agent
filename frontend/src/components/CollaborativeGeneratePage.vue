<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { generateCollaborativeLearning, listResources } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import { loadUserProfile } from '../api/userProfile'
import type { CollaborativeExerciseItem, CollaborativeLearningRequest, CollaborativeLearningResponse, CollaborativeResourceType, UploadedResource } from '../types'
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
  { key: 'lecture', resultKey: 'lectureDoc', label: '课程讲解', description: '生成概念、原理和示例讲解', icon: '▤' },
  { key: 'mindmap', resultKey: 'mindmap', label: '思维导图', description: '生成结构化知识导图', icon: '◇' },
  { key: 'exercise', resultKey: 'exercises', label: '练习题', description: '生成分层题目和答案解析', icon: '✓' },
  { key: 'reading', resultKey: 'reading', label: '拓展阅读', description: '生成延伸知识和学习路径', icon: '◉' },
]

const prompt = ref('')
const userProfile = ref(loadUserProfile())
const resources = ref<UploadedResource[]>([])
const selectedTypes = ref<CollaborativeResourceType[]>([])
const selectedFileIds = ref<string[]>([])
const submittedTypes = ref<CollaborativeResourceType[]>([])
const menuOpen = ref(false)
const loading = ref(false)
const error = ref('')
const result = ref<CollaborativeLearningResponse | null>(null)
const activeTab = ref<ResultKey>('lectureDoc')
const exerciseAnswers = ref<Record<string, string>>({})
const exerciseSubmitted = ref<Record<string, boolean>>({})

const availableTabs = computed(() => [
  ...(!submittedTypes.value.length ? [{ key: 'lectureDoc' as ResultKey, label: '对话回答' }] : []),
  ...resourceOptions
    .filter(item => submittedTypes.value.includes(item.key))
    .map(item => ({ key: item.resultKey, label: item.label })),
  ...(submittedTypes.value.length ? [{ key: 'review' as ResultKey, label: '审核结果' }] : []),
])

const selectedOptions = computed(() => resourceOptions.filter(item => selectedTypes.value.includes(item.key)))
const selectedFiles = computed(() => resources.value.filter(item => selectedFileIds.value.includes(item.id)))
const activeContent = computed(() => result.value?.[activeTab.value] || '')
const exerciseItems = computed(() => result.value?.exerciseItems || [])

function toggleResource(key: CollaborativeResourceType) {
  selectedTypes.value = selectedTypes.value.includes(key)
    ? selectedTypes.value.filter(item => item !== key)
    : [...selectedTypes.value, key]
}

function removeResource(key: CollaborativeResourceType) {
  selectedTypes.value = selectedTypes.value.filter(item => item !== key)
}

function toggleFile(fileId: string) {
  selectedFileIds.value = selectedFileIds.value.includes(fileId)
    ? selectedFileIds.value.filter(item => item !== fileId)
    : [...selectedFileIds.value, fileId]
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

function submitExercise(item: CollaborativeExerciseItem) {
  const answer = exerciseAnswers.value[item.id]?.trim()
  if (!answer) return
  exerciseSubmitted.value = { ...exerciseSubmitted.value, [item.id]: true }
}

function retryExercise(questionId: string) {
  exerciseSubmitted.value = { ...exerciseSubmitted.value, [questionId]: false }
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

async function submit() {
  const question = prompt.value.trim()
  if (!question) {
    error.value = '请输入你想学习的内容'
    return
  }
  const config = loadSiliconFlowConfig()
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
  exerciseAnswers.value = {}
  exerciseSubmitted.value = {}
  menuOpen.value = false
  submittedTypes.value = [...selectedTypes.value]
  activeTab.value = resourceOptions.find(item => submittedTypes.value.includes(item.key))?.resultKey || 'lectureDoc'

  try {
    result.value = await generateCollaborativeLearning(payload)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '资源生成失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadUploadedResources)
</script>

<template>
  <div :class="['generate-page', { 'has-result': result || loading }]">
    <section v-if="!result && !loading" class="empty-state">
      <h2>今天想学点什么？</h2>
    </section>

    <section v-if="loading" class="generating-state">
      <span class="generating-mark">✦</span>
      <div>
        <strong>正在生成学习资源</strong>
        <p>正在理解问题并组织所选内容……</p>
      </div>
    </section>

    <section v-if="result" class="result-card">
      <div v-if="result.sources.length" class="result-sources">
        <span>参考资料</span>
        <b v-for="source in result.sources" :key="source.id">{{ source.name }}</b>
      </div>
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
        <div v-else-if="activeTab === 'exercises' && exerciseItems.length" class="practice-list">
          <article
            v-for="(item, index) in exerciseItems"
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
        <MarkdownRenderer v-else :content="activeContent" />
      </div>
    </section>

    <section class="composer-section">
      <div v-if="error" class="composer-error">{{ error }}</div>

      <div class="composer">
        <textarea
          v-model="prompt"
          rows="1"
          :disabled="loading"
          placeholder="有问题，尽管问"
          @keydown.enter.exact.prevent="submit"
        ></textarea>

        <div v-if="selectedOptions.length || selectedFiles.length" class="selected-tools">
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
          <button
            v-for="item in selectedOptions"
            :key="item.key"
            type="button"
            :disabled="loading"
            @click="removeResource(item.key)"
          >
            <span>{{ item.icon }}</span>{{ item.label }}<i>×</i>
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
              +
            </button>

            <div v-if="menuOpen" class="tool-menu">
              <div class="menu-title">引用资源库文件</div>
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
              <div v-else class="no-files">资源库暂无 PDF，请先上传文件</div>
              <div class="menu-divider"></div>
              <div class="menu-title">选择生成内容</div>
              <button
                v-for="item in resourceOptions"
                :key="item.key"
                type="button"
                :class="{ selected: selectedTypes.includes(item.key) }"
                @click="toggleResource(item.key)"
              >
                <span class="tool-icon">{{ item.icon }}</span>
                <span><b>{{ item.label }}</b><small>{{ item.description }}</small></span>
                <i>{{ selectedTypes.includes(item.key) ? '✓' : '' }}</i>
              </button>
            </div>
          </div>

          <span class="selection-label">
            {{ selectedFileIds.length ? `已引用 ${selectedFileIds.length} 份 PDF` : selectedTypes.length ? `已选 ${selectedTypes.length} 项` : '直接对话' }}
          </span>

          <button class="send-button" :disabled="loading || !prompt.trim()" aria-label="发送" @click="submit">
            {{ loading ? '…' : '↑' }}
          </button>
        </div>
      </div>

      <p class="composer-hint">Enter 发送 · Shift + Enter 换行</p>
    </section>
  </div>
</template>

<style scoped>
.generate-page { display: grid; grid-template-rows: 1fr auto; width: min(980px, 100%); min-height: calc(100vh - 210px); margin: 0 auto; color: #202123; }
.generate-page.has-result { gap: 24px; }
.empty-state { display: grid; place-items: end center; padding-bottom: 42px; }
.empty-state h2 { margin: 0; font-size: clamp(28px, 4vw, 38px); font-weight: 500; letter-spacing: -.035em; }
.generating-state { display: flex; align-items: center; justify-content: center; gap: 14px; min-height: 320px; }
.generating-mark { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 50%; color: #fff; background: #202123; animation: pulse 1.2s infinite; }
.generating-state strong { font-size: 16px; }
.generating-state p { margin: 5px 0 0; color: #8a8a8a; font-size: 13px; }
.result-card { min-height: 320px; overflow: hidden; border: 1px solid #e5e5e5; border-radius: 18px; background: #fff; }
.result-sources { display: flex; align-items: center; flex-wrap: wrap; gap: 7px; padding: 12px 16px 0; color: #858585; font-size: 10px; }
.result-sources b { padding: 5px 8px; border-radius: 999px; color: #7d3434; background: #fff0f0; font-weight: 650; }
.result-tabs { display: flex; gap: 4px; padding: 12px 16px 0; overflow-x: auto; border-bottom: 1px solid #ececec; }
.result-tabs button { padding: 11px 14px; border: 0; border-radius: 9px 9px 0 0; color: #6d6d6d; background: transparent; white-space: nowrap; font-weight: 600; }
.result-tabs button.active { color: #202123; background: #f2f2f2; }
.result-content { padding: 26px; }
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
.composer-section { position: sticky; bottom: 0; z-index: 5; padding: 12px 0 4px; background: linear-gradient(180deg, rgba(247, 248, 251, 0), #f7f8fb 24%); }
.composer { padding: 13px 14px 11px; border: 1px solid #d9d9d9; border-radius: 26px; background: #fff; box-shadow: 0 8px 30px rgba(0, 0, 0, .08); }
.composer:focus-within { border-color: #b8b8b8; box-shadow: 0 8px 32px rgba(0, 0, 0, .11); }
.composer textarea { width: 100%; min-height: 34px; max-height: 170px; padding: 5px 5px 10px; overflow-y: auto; border: 0; outline: 0; resize: none; color: #202123; background: transparent; font: inherit; font-size: 16px; line-height: 1.55; }
.composer textarea::placeholder { color: #929292; }
.selected-tools { display: flex; flex-wrap: wrap; gap: 7px; padding: 0 4px 9px; }
.selected-tools button { display: flex; align-items: center; gap: 6px; padding: 6px 9px; border: 1px solid #dedede; border-radius: 999px; color: #555; background: #fafafa; font-size: 12px; }
.selected-tools button i { color: #929292; font-style: normal; font-size: 14px; }
.selected-tools button.selected-file { max-width: 260px; border-color: #f1caca; color: #8d3434; background: #fff5f5; }
.selected-tools button.selected-file span { font-size: 9px; font-weight: 850; }
.composer-actions { display: flex; align-items: center; gap: 9px; }
.tool-picker { position: relative; }
.add-button { display: grid; place-items: center; width: 36px; height: 36px; border: 0; border-radius: 50%; color: #303030; background: #f0f0f0; font-size: 25px; font-weight: 300; }
.add-button:hover { background: #e6e6e6; }
.tool-menu { position: absolute; left: 0; bottom: 46px; width: 310px; padding: 8px; border: 1px solid #dadada; border-radius: 16px; background: #fff; box-shadow: 0 14px 38px rgba(0, 0, 0, .16); }
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
.selection-label { flex: 1; color: #8b8b8b; font-size: 12px; }
.send-button { display: grid; place-items: center; width: 38px; height: 38px; border: 0; border-radius: 50%; color: #fff; background: #202123; font-size: 21px; }
.send-button:disabled { background: #d0d0d0; cursor: default; }
.composer-hint { margin: 8px 0 0; color: #9a9a9a; text-align: center; font-size: 10px; }
.composer-error { margin: 0 auto 9px; padding: 9px 12px; border-radius: 10px; color: #a13838; background: #fff0f0; font-size: 12px; }
button { cursor: pointer; }
button:disabled { cursor: default; opacity: .65; }
@keyframes pulse { 50% { transform: scale(.94); opacity: .65; } }
@media (max-width: 620px) {
  .generate-page { min-height: calc(100vh - 170px); }
  .tool-menu { width: min(310px, calc(100vw - 60px)); }
  .result-content { padding: 18px; }
}
</style>
