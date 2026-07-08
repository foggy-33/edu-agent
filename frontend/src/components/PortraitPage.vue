<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { chatDynamicProfile, getDynamicProfile, listDynamicProfiles } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import { loadUserProfile } from '../api/userProfile'
import type { DynamicProfile, SubjectProfileSummary } from '../types/profile'

type ChatMessage = {
  role: 'assistant' | 'user'
  content: string
}

const defaultCourses = ['数据库系统', '数据结构', '算法设计', '操作系统', '计算机网络', '软件工程']
const userProfile = ref(loadUserProfile())
const portrait = ref<DynamicProfile | null>(null)
const subjectProfiles = ref<SubjectProfileSummary[]>([])
const course = ref('操作系统')
const userMessage = ref('')
const newCourseName = ref('')
const creatingProfile = ref(false)
const loading = ref(false)
const error = ref('')
const messageStream = ref<HTMLElement | null>(null)
const replies = ref<ChatMessage[]>([])

const courses = computed(() => Array.from(new Set([
  ...subjectProfiles.value.map(item => item.course),
  ...defaultCourses,
])))
const hasProfile = computed(() => Boolean(portrait.value?.version))
const completionLabel = computed(() => `完成度 ${portrait.value?.completion || 0}%`)
const subtitle = computed(() => `${course.value} · 画像 V${portrait.value?.version || 0} · ${completionLabel.value}`)

function welcomeMessage(selectedCourse: string): ChatMessage {
  return {
    role: 'assistant',
    content: `你好，我会根据你对《${selectedCourse}》的描述更新学习画像。你可以说目标、基础、薄弱点、学习偏好或最近遇到的问题。`,
  }
}

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
    replies.value = [welcomeMessage(selectedCourse)]
    await scrollToLatest()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '画像加载失败'
  } finally {
    loading.value = false
  }
}

async function createProfile() {
  const name = newCourseName.value.trim()
  if (!name) {
    creatingProfile.value = true
    return
  }
  if (!courses.value.includes(name)) {
    subjectProfiles.value = [
      { course: name, completion: 0, version: 0, updated_at: null, summary: '', radar_metrics: {} },
      ...subjectProfiles.value,
    ]
  }
  newCourseName.value = ''
  creatingProfile.value = false
  await loadPortrait(name)
}

async function sendMessage() {
  const content = userMessage.value.trim()
  if (!content || loading.value) return

  replies.value.push({ role: 'user', content })
  userMessage.value = ''
  loading.value = true
  error.value = ''
  await scrollToLatest()

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
    await scrollToLatest()
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
    error.value = err instanceof Error ? err.message : '画像加载失败'
  }
})
</script>

<template>
  <div :class="['profile-chat-page', { idle: replies.length <= 1 && !loading }]">
    <section v-if="replies.length <= 1 && !loading" class="empty-state">
      <h2>准备好了，随时开始画像对话</h2>
      <p>{{ subtitle }}</p>
    </section>

    <main v-if="replies.length > 1 || loading" ref="messageStream" class="message-stream">
      <div class="message-column">
        <article v-for="(item, index) in replies" :key="index" :class="['chat-row', item.role]">
          <div class="message-body">
            <p>{{ item.content }}</p>
          </div>
        </article>

        <article v-if="loading" class="chat-row assistant">
          <div class="message-body">
            <div class="typing"><i></i><i></i><i></i></div>
          </div>
        </article>
      </div>
    </main>

    <section class="composer-section">
      <p v-if="error" class="composer-error">{{ error }}</p>
      <div class="composer">
        <textarea
          v-model="userMessage"
          rows="1"
          :disabled="loading"
          :placeholder="`告诉 AI 你学习《${course}》的情况......`"
          @keydown.enter.exact.prevent="sendMessage"
        ></textarea>

        <div class="selected-tools">
          <button type="button" class="subject-chip" :disabled="loading">
            画像 {{ course }}
          </button>
          <button v-if="!creatingProfile" type="button" :disabled="loading" @click="creatingProfile = true">
            + 新建画像
          </button>
          <label v-else class="new-profile-field">
            <input
              v-model.trim="newCourseName"
              :disabled="loading"
              placeholder="输入学科名称"
              @keydown.enter.prevent="createProfile"
            />
            <button type="button" :disabled="loading" @click="createProfile">创建</button>
          </label>
        </div>

        <div class="composer-actions">
          <select v-model="course" :disabled="loading" aria-label="选择学科" @change="loadPortrait(course)">
            <option v-for="item in courses" :key="item" :value="item">{{ item }}</option>
          </select>
          <span class="selection-label">{{ completionLabel }}</span>
          <button class="send-button" :disabled="loading || !userMessage.trim()" aria-label="发送消息" @click="sendMessage">
            {{ loading ? '...' : '↑' }}
          </button>
        </div>
      </div>
      <p class="composer-hint">AI 只会将对话中有明确证据的信息写入当前学科画像。</p>
    </section>
  </div>
</template>

<style scoped>
.profile-chat-page { display: grid; grid-template-rows: 1fr auto; width: min(980px, 100%); min-height: calc(100vh - 80px); margin: 0 auto; color: #202123; }
.profile-chat-page.idle { grid-template-rows: auto auto; width: min(680px, 100%); align-content: center; gap: 28px; padding-bottom: 8vh; }
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
.composer:focus-within { border-color: #d9d9d9; box-shadow: 0 16px 48px rgba(15, 23, 42, .2); }
.composer textarea { width: 100%; min-height: 34px; max-height: 170px; padding: 5px 5px 9px; overflow-y: auto; border: 0; outline: 0; resize: none; color: #202123; background: transparent; font: inherit; font-size: 16px; line-height: 1.55; }
.composer textarea::placeholder { color: #929292; }
.selected-tools { display: flex; flex-wrap: wrap; gap: 7px; padding: 0 4px 9px; }
.selected-tools button, .new-profile-field { display: inline-flex; align-items: center; gap: 6px; min-height: 30px; padding: 5px 9px; border: 1px solid #dedede; border-radius: 999px; color: #555; background: #fafafa; font-size: 12px; }
.selected-tools button.subject-chip { color: #444; border-color: #dedede; background: #f6f6f6; }
.new-profile-field { padding: 3px 4px 3px 10px; }
.new-profile-field input { width: 118px; border: 0; outline: 0; color: #202123; background: transparent; font: inherit; font-size: 12px; }
.new-profile-field button { min-height: 24px; padding: 3px 8px; border: 0; color: #fff; background: #202123; }
.composer-actions { display: flex; align-items: center; gap: 9px; }
.composer-actions select { min-width: 116px; max-width: 160px; padding: 8px 28px 8px 10px; border: 0; border-radius: 999px; color: #565656; background: #f0f0f0; outline: 0; font-size: 12px; }
.selection-label { flex: 1; color: #8b8b8b; font-size: 12px; }
.send-button { display: grid; place-items: center; width: 38px; height: 38px; border: 0; border-radius: 50%; color: #fff; background: #202123; font-size: 19px; }
.send-button:disabled { background: #d0d0d0; cursor: default; }
.composer-hint { margin: 7px 0 0; color: rgba(80, 80, 80, .62); text-align: center; font-size: 10px; text-shadow: 0 1px 8px rgba(255, 255, 255, .9); }
.composer-error { margin: 0 auto 9px; padding: 9px 12px; border-radius: 10px; color: #a13838; background: #fff0f0; font-size: 12px; }
.composer-section:focus-within, .composer:focus, .composer textarea:focus, .composer-actions select:focus, .composer-actions button:focus { outline: none; }
button { cursor: pointer; border: 0; }
button:disabled { cursor: default; opacity: .55; }
@keyframes typing { 0%, 60%, 100% { transform: translateY(0); opacity: .45; } 30% { transform: translateY(-4px); opacity: 1; } }
@media (max-width: 760px) {
  .profile-chat-page { min-height: calc(100vh - 64px); }
  .message-column { width: calc(100% - 24px); padding-top: 24px; }
  .message-body { max-width: 88%; }
  .composer-actions select { max-width: 120px; }
}
</style>
