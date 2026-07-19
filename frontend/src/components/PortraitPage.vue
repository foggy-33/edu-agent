<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { chatDynamicProfile, getDynamicProfile, getNextProfileQuestion, listDynamicProfiles } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import { loadUserProfile } from '../api/userProfile'
import type { DynamicProfile, SubjectProfileSummary } from '../types/profile'

type ChatMessage = {
  role: 'assistant' | 'user'
  content: string
}

const INTERVIEW_TURNS = 6

const defaultCourses = ['数据库系统', '数据结构', '算法设计', '操作系统', '计算机网络', '软件工程']
const NEW_PROFILE_VALUE = '__new_profile__'
const userProfile = ref(loadUserProfile())
const portrait = ref<DynamicProfile | null>(null)
const subjectProfiles = ref<SubjectProfileSummary[]>([])
const course = ref('操作系统')
const loading = ref(false)
const questionStreaming = ref(false)
const error = ref('')
const messageStream = ref<HTMLElement | null>(null)
const replies = ref<ChatMessage[]>([])
const conversationStarted = ref(false)
const guidedStep = ref(0)
const answerDraft = ref('')
const interviewComplete = ref(false)

const courses = computed(() => Array.from(new Set([
  ...subjectProfiles.value.map(item => item.course),
  ...defaultCourses,
])))
const subtitle = computed(() => `${course.value} · 六维学习画像 · V${portrait.value?.version || 0}`)
const emit = defineEmits<{
  navigate: [page: 'account']
}>()

async function scrollToLatest() {
  await nextTick()
  if (messageStream.value) {
    messageStream.value.scrollTop = messageStream.value.scrollHeight
  }
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
    conversationStarted.value = false
    await scrollToLatest()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '画像加载失败'
  } finally {
    loading.value = false
  }
}

async function handleProfileSelect(event: Event) {
  const selected = (event.target as HTMLSelectElement).value
  if (selected === NEW_PROFILE_VALUE) {
    const name = window.prompt('请输入新画像名称')
    const nextCourse = name?.trim()
    if (!nextCourse) return
    if (!courses.value.includes(nextCourse)) {
      subjectProfiles.value = [
        { course: nextCourse, completion: 0, version: 0, updated_at: null, summary: '', radar_metrics: {} },
        ...subjectProfiles.value,
      ]
    }
    await loadPortrait(nextCourse)
    return
  }
  await loadPortrait(selected)
}

async function startConversation() {
  if (loading.value || !course.value) return
  conversationStarted.value = true
  error.value = ''
  replies.value = []
  guidedStep.value = 0
  answerDraft.value = ''
  interviewComplete.value = false
  await scrollToLatest()
  await askNextQuestion()
}

async function askNextQuestion() {
  questionStreaming.value = true
  try {
    const result = await getNextProfileQuestion({
      ...loadSiliconFlowConfig(),
      user_id: userProfile.value.userId,
      course: course.value,
    })
    questionStreaming.value = false
    await streamAssistant(result.question || `聊聊你目前学习《${course.value}》时最想解决的问题。`)
    if (result.warning) error.value = `提示：${result.warning}`
  } catch (err) {
    questionStreaming.value = false
    error.value = err instanceof Error ? err.message : '暂时无法生成下一个问题'
    await streamAssistant(`聊聊你目前学习《${course.value}》时最想解决的问题。`)
  }
}

async function streamAssistant(content: string) {
  questionStreaming.value = true
  replies.value.push({ role: 'assistant', content: '' })
  const target = replies.value.length - 1
  const message = replies.value[target]
  if (!message) {
    questionStreaming.value = false
    return
  }
  for (let index = 0; index < content.length; index += 2) {
    message.content = content.slice(0, index + 2)
    await scrollToLatest()
    await new Promise(resolve => window.setTimeout(resolve, 14))
  }
  message.content = content
  questionStreaming.value = false
  await scrollToLatest()
}

async function sendAnswer() {
  const answer = answerDraft.value.trim()
  if (!answer || loading.value || questionStreaming.value || interviewComplete.value) return
  answerDraft.value = ''
  replies.value.push({ role: 'user', content: answer })
  await scrollToLatest()
  loading.value = true
  error.value = ''

  try {
    const result = await chatDynamicProfile({
      ...loadSiliconFlowConfig(),
      user_id: userProfile.value.userId,
      course: course.value,
      message: answer,
    })
    portrait.value = result.profile
    await refreshSubjects()
    loading.value = false
    if (result.warning) error.value = `提示：${result.warning}`

    if (guidedStep.value >= INTERVIEW_TURNS - 1) {
      interviewComplete.value = true
      await streamAssistant(`谢谢你的回答。我已经根据这次对话更新了《${course.value}》学习画像，你可以前往个人中心查看六维分析、薄弱点和学习建议。`)
      return
    }

    guidedStep.value += 1
    await askNextQuestion()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '画像更新失败'
    loading.value = false
  }
}

function handleComposerKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.shiftKey) return
  event.preventDefault()
  void sendAnswer()
}

function finishConversation() {
  emit('navigate', 'account')
}

onMounted(async () => {
  try {
    await refreshSubjects()
    if (subjectProfiles.value[0]) course.value = subjectProfiles.value[0].course
    await loadPortrait(course.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : '画像加载失败'
  }
})
</script>

<template>
  <div :class="['profile-chat-page', { idle: !conversationStarted && !loading }]">
    <section v-if="!conversationStarted && !loading" class="empty-state">
      <h2>准备好了，随时开始画像对话</h2>
      <p>{{ subtitle }}</p>
    </section>

    <main v-if="conversationStarted || loading" ref="messageStream" class="message-stream">
      <div class="message-column">
        <article v-for="(item, index) in replies" :key="index" :class="['chat-row', item.role]">
          <div class="message-body">
            <p>{{ item.content }}</p>
          </div>
        </article>

        <article v-if="loading || questionStreaming" class="chat-row assistant">
          <div class="message-body">
            <div class="typing"><i></i><i></i><i></i></div>
          </div>
        </article>
      </div>
    </main>

    <section v-if="!conversationStarted" class="composer-section">
      <p v-if="error" class="composer-error">{{ error }}</p>
      <div class="composer starter-composer">
        <select :value="course" :disabled="loading" aria-label="选择画像" @change="handleProfileSelect">
          <option v-for="item in courses" :key="item" :value="item">{{ item }}</option>
          <option disabled value="">────────</option>
          <option :value="NEW_PROFILE_VALUE">+ 新建画像</option>
        </select>
        <button class="start-button" type="button" :disabled="loading || !course" @click="startConversation">
          开始对话
        </button>
      </div>
      <p class="composer-hint">选择画像后，AI 会先提出一个问题。</p>
    </section>

    <section v-else class="composer-section">
      <p v-if="error" class="composer-error">{{ error }}</p>
      <div v-if="!interviewComplete" class="guided-composer">
        <div class="guided-head">
          <span>{{ course }} · 自然语言画像对话</span>
          <b>{{ Math.min(guidedStep + 1, INTERVIEW_TURNS) }}/{{ INTERVIEW_TURNS }}</b>
        </div>
        <div class="guided-progress"><i :style="{ width: `${((guidedStep + 1) / INTERVIEW_TURNS) * 100}%` }"></i></div>
        <div class="answer-composer">
          <textarea
            v-model="answerDraft"
            :disabled="loading || questionStreaming"
            rows="2"
            placeholder="用自己的话回答，越具体越有助于形成准确画像"
            aria-label="回答画像问题"
            @keydown="handleComposerKeydown"
          ></textarea>
          <button
            class="send-button"
            type="button"
            aria-label="发送回答"
            :disabled="!answerDraft.trim() || loading || questionStreaming"
            @click="sendAnswer"
          >↑</button>
        </div>
        <p v-if="loading" class="generating-hint">正在理解你的回答并更新画像...</p>
      </div>
      <div v-else class="completion-composer">
        <div>
          <strong>画像已生成</strong>
          <span>六维分析和学习建议已保存</span>
        </div>
        <button class="finish-button" type="button" @click="finishConversation">前往个人中心查看</button>
      </div>
      <p class="composer-hint">Enter 发送，Shift + Enter 换行；AI 会根据你的回答继续追问。</p>
    </section>
  </div>
</template>

<style scoped>
.profile-chat-page { display: grid; grid-template-rows: 1fr auto; width: min(980px, 100%); min-height: calc(100vh - 80px); margin: 0 auto; color: #202123; }
.profile-chat-page.idle { grid-template-rows: auto auto; width: min(580px, 100%); align-content: center; gap: 22px; padding-bottom: 8vh; }
.empty-state { display: grid; place-items: center; padding: 0; text-align: center; }
.empty-state h2 { margin: 0; font-size: clamp(30px, 4.2vw, 42px); font-weight: 500; letter-spacing: 0; }
.empty-state p { margin: 12px 0 0; color: #9a9a9a; font-size: 13px; }
.message-stream { min-height: 320px; overflow-y: auto; scroll-behavior: smooth; }
.message-column { width: min(820px, calc(100% - 36px)); margin: 0 auto; padding: 30px 0 132px; }
.chat-row { display: flex; margin-bottom: 24px; }
.chat-row.user { justify-content: flex-end; }
.message-body { max-width: min(700px, 86%); }
.message-body p { margin: 0; color: #202123; font-size: 15px; line-height: 1.8; white-space: pre-wrap; }
.chat-row.user .message-body { padding: 12px 15px; border-radius: 18px; background: #f3f3f3; }
.typing { display: flex; gap: 5px; padding: 10px 0; }
.typing i { width: 6px; height: 6px; border-radius: 50%; background: #8f96a3; animation: typing 1.1s infinite ease-in-out; }
.typing i:nth-child(2) { animation-delay: .16s; }
.typing i:nth-child(3) { animation-delay: .32s; }
.composer-section { position: sticky; bottom: 18px; z-index: 5; width: min(760px, calc(100% - 32px)); margin: 0 auto; padding: 0; background: transparent; box-shadow: none; }
.profile-chat-page.idle .composer-section { position: static; padding: 0; background: transparent; }
.composer { padding: 12px 14px 11px; border: 1px solid #d9d9d9; border-radius: 26px; background: rgba(255, 255, 255, .98); box-shadow: 0 14px 44px rgba(15, 23, 42, .16); outline: none; backdrop-filter: blur(10px); }
.starter-composer { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 7px; align-items: center; max-width: 560px; margin: 0 auto; padding: 7px; border-radius: 999px; }
.composer:focus-within { border-color: #d9d9d9; box-shadow: 0 16px 48px rgba(15, 23, 42, .2); }
.composer textarea { width: 100%; min-height: 34px; max-height: 170px; padding: 5px 5px 9px; overflow-y: auto; border: 0; outline: 0; resize: none; color: #202123; background: transparent; font: inherit; font-size: 16px; line-height: 1.55; }
.composer textarea::placeholder { color: #929292; }
.composer select { width: 100%; min-width: 0; min-height: 38px; padding: 8px 13px; border: 0; border-radius: 999px; color: #565656; background: #f0f0f0; outline: 0; font-size: 14px; }
.composer-actions { display: flex; align-items: center; gap: 9px; }
.selection-label { flex: 1; color: #8b8b8b; font-size: 12px; }
.start-button { min-height: 38px; padding: 0 15px; border-radius: 999px; color: #fff; background: #202123; font-size: 13px; font-weight: 700; white-space: nowrap; }
.finish-button { min-height: 34px; padding: 0 12px; border: 1px solid #d6d6d6; border-radius: 999px; color: #333; background: #fff; font-size: 12px; font-weight: 600; white-space: nowrap; }
.finish-button:hover { background: #f3f3f3; }
.guided-composer, .completion-composer { padding: 14px; border: 1px solid #dedede; border-radius: 22px; background: rgba(255, 255, 255, .98); box-shadow: 0 14px 44px rgba(15, 23, 42, .14); }
.guided-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; color: #6f6f6f; font-size: 12px; }
.guided-head b { color: #202123; font-size: 12px; }
.guided-progress { height: 3px; margin: 10px 0 13px; overflow: hidden; border-radius: 999px; background: #ececec; }
.guided-progress i { display: block; height: 100%; border-radius: inherit; background: #202123; transition: width .25s ease; }
.answer-composer { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: end; gap: 10px; padding: 9px 10px 9px 14px; border: 1px solid #dedede; border-radius: 18px; background: #fafafa; transition: border-color .16s ease, box-shadow .16s ease; }
.answer-composer:focus-within { border-color: #8b7cf6; box-shadow: 0 0 0 3px rgba(124, 108, 240, .1); }
.answer-composer textarea { width: 100%; min-height: 44px; max-height: 140px; padding: 4px 0; overflow-y: auto; border: 0; outline: 0; resize: none; color: #202123; background: transparent; font: inherit; font-size: 14px; line-height: 1.55; }
.answer-composer textarea::placeholder { color: #999; }
.generating-hint { margin: 11px 0 0; color: #858585; text-align: center; font-size: 11px; }
.completion-composer { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.completion-composer div { display: grid; gap: 3px; }
.completion-composer strong { font-size: 14px; }
.completion-composer span { color: #858585; font-size: 11px; }
.send-button { display: grid; place-items: center; width: 38px; height: 38px; border: 0; border-radius: 50%; color: #fff; background: #202123; font-size: 19px; }
.send-button:disabled, .start-button:disabled { background: #d0d0d0; cursor: default; }
.composer-hint { margin: 7px 0 0; color: rgba(80, 80, 80, .62); text-align: center; font-size: 10px; text-shadow: 0 1px 8px rgba(255, 255, 255, .9); }
.composer-error { margin: 0 auto 9px; padding: 9px 12px; border-radius: 10px; color: #a13838; background: #fff0f0; font-size: 12px; }
.composer-section:focus-within, .composer:focus, .composer textarea:focus, .composer select:focus, .composer button:focus { outline: none; }
button { cursor: pointer; border: 0; }
button:disabled { cursor: default; opacity: .55; }
@keyframes typing { 0%, 60%, 100% { transform: translateY(0); opacity: .45; } 30% { transform: translateY(-4px); opacity: 1; } }
@media (max-width: 760px) {
  .profile-chat-page { min-height: calc(100vh - 64px); }
  .message-column { width: calc(100% - 24px); padding-top: 24px; }
  .message-body { max-width: 88%; }
  .starter-composer { grid-template-columns: 1fr; }
  .starter-composer { border-radius: 22px; }
  .answer-composer { border-radius: 16px; }
  .completion-composer { align-items: stretch; flex-direction: column; }
  .finish-button { padding: 0 10px; font-size: 11px; }
}
</style>
