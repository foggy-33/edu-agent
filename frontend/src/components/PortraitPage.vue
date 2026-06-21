<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { chatDynamicProfile, getDynamicProfile, getNextProfileQuestion, listDynamicProfiles } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import { loadUserProfile } from '../api/userProfile'
import type { DynamicProfile, SubjectProfileSummary } from '../types/profile'
import SubjectProfileDrawer from './SubjectProfileDrawer.vue'

type ChatMessage = {
  role: 'assistant' | 'user'
  content: string
}

const defaultCourses = ['数据库系统', '数据结构', '算法设计', '操作系统', '计算机网络', '软件工程']
const userProfile = ref(loadUserProfile())
const portrait = ref<DynamicProfile | null>(null)
const subjectProfiles = ref<SubjectProfileSummary[]>([])
const course = ref('数据库系统')
const userMessage = ref('')
const loading = ref(false)
const error = ref('')
const showProfiles = ref(false)
const messageStream = ref<HTMLElement | null>(null)
const replies = ref<ChatMessage[]>([])

const courses = computed(() => Array.from(new Set([...defaultCourses, ...subjectProfiles.value.map(item => item.course)])))
const hasProfile = computed(() => Boolean(portrait.value?.version))

function welcomeMessage(selectedCourse: string): ChatMessage {
  return {
    role: 'assistant',
    content: `你好，我是你的${selectedCourse}画像助手。你可以直接告诉我学习目标、基础情况、薄弱知识点、偏好的学习方式或学习时间，我会在对话中持续完善这门课的画像。`,
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
    error.value = err instanceof Error ? err.message : '加载学科画像失败'
  } finally {
    loading.value = false
  }
}

async function startInterview() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const result = await getNextProfileQuestion({
      ...loadSiliconFlowConfig(),
      user_id: userProfile.value.userId,
      course: course.value,
    })
    portrait.value = result.profile
    replies.value.push({ role: 'assistant', content: result.question })
    await scrollToLatest()
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

async function selectProfile(selectedCourse: string) {
  await loadPortrait(selectedCourse)
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
  <div class="profile-chat-page">
    <header class="chat-header">
      <div class="assistant-identity">
        <div class="assistant-avatar">AI</div>
        <div>
          <h2>{{ course }}画像助手</h2>
          <p>
            <span class="status-dot"></span>
            {{ hasProfile ? `画像 V${portrait?.version} · 完成度 ${portrait?.completion}%` : '等待开始构建画像' }}
          </p>
        </div>
      </div>

      <div class="header-actions">
        <select v-model="course" :disabled="loading" aria-label="选择学科" @change="loadPortrait(course)">
          <option v-for="item in courses" :key="item" :value="item">{{ item }}</option>
        </select>
        <button class="profile-overview-button" type="button" @click="showProfiles = true">
          <span>◫</span>查看各科画像
        </button>
      </div>
    </header>

    <main ref="messageStream" class="message-stream">
      <div class="message-column">
        <article v-for="(item, index) in replies" :key="index" :class="['chat-row', item.role]">
          <div v-if="item.role === 'assistant'" class="message-avatar">AI</div>
          <div class="message-body">
            <span class="message-author">{{ item.role === 'assistant' ? '画像助手' : '你' }}</span>
            <p>{{ item.content }}</p>
          </div>
          <div v-if="item.role === 'user'" class="message-avatar user-avatar">
            {{ userProfile.name.trim().slice(0, 1).toUpperCase() || 'U' }}
          </div>
        </article>

        <article v-if="loading" class="chat-row assistant">
          <div class="message-avatar">AI</div>
          <div class="message-body">
            <span class="message-author">画像助手</span>
            <div class="typing"><i></i><i></i><i></i></div>
          </div>
        </article>
      </div>
    </main>

    <div class="composer-area">
      <p v-if="error" class="chat-warning">{{ error }}</p>
      <div class="quick-actions">
        <button type="button" :disabled="loading" @click="startInterview">
          <span>✦</span>{{ hasProfile ? '让 AI 继续提问' : '开始画像访谈' }}
        </button>
        <span>Enter 发送 · Shift + Enter 换行</span>
      </div>
      <form class="chat-composer" @submit.prevent="sendMessage">
        <textarea
          v-model="userMessage"
          rows="1"
          :disabled="loading"
          :placeholder="`告诉 AI 你学习《${course}》的情况……`"
          @keydown.enter.exact.prevent="sendMessage"
        ></textarea>
        <button class="send-button" :disabled="loading || !userMessage.trim()" aria-label="发送消息">↑</button>
      </form>
      <p class="composer-hint">AI 只会将对话中有明确证据的信息写入当前学科画像。</p>
    </div>

    <SubjectProfileDrawer
      v-if="showProfiles"
      :profiles="subjectProfiles"
      :profile="portrait"
      :current-course="course"
      :loading="loading"
      @close="showProfiles = false"
      @select="selectProfile"
    />
  </div>
</template>

<style scoped>
.profile-chat-page { position: relative; display: grid; grid-template-rows: auto minmax(420px, 1fr) auto; height: calc(100vh - 154px); min-height: 650px; overflow: hidden; border: 1px solid #e3e6ec; border-radius: 22px; color: #202938; background: #fff; box-shadow: 0 16px 45px rgba(31, 42, 68, .07); }
.chat-header { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 15px 20px; border-bottom: 1px solid #e8eaef; background: rgba(255, 255, 255, .96); }
.assistant-identity, .header-actions { display: flex; align-items: center; gap: 12px; }
.assistant-avatar, .message-avatar { display: grid; place-items: center; width: 38px; height: 38px; flex: 0 0 auto; border-radius: 12px; color: #fff; background: linear-gradient(135deg, #5146cf, #7b6dea); font-size: 12px; font-weight: 800; }
.assistant-identity h2 { margin: 0 0 3px; font-size: 16px; }
.assistant-identity p { display: flex; align-items: center; gap: 6px; margin: 0; color: #858d9b; font-size: 11px; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 3px #dcfce7; }
.header-actions select { padding: 9px 30px 9px 11px; border: 1px solid #dfe3ea; border-radius: 10px; color: #424b5d; background: #fff; }
.profile-overview-button { display: flex; align-items: center; gap: 7px; padding: 9px 13px; border: 1px solid #d8d4ff; border-radius: 10px; color: #4e43bc; background: #f4f2ff; font-weight: 700; }
.message-stream { overflow-y: auto; scroll-behavior: smooth; background: linear-gradient(180deg, #fff 0%, #fbfbfd 100%); }
.message-column { width: min(820px, calc(100% - 36px)); margin: 0 auto; padding: 34px 0 24px; }
.chat-row { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 28px; }
.chat-row.user { justify-content: flex-end; }
.chat-row.user .message-body { align-items: flex-end; }
.message-avatar { width: 32px; height: 32px; border-radius: 10px; font-size: 10px; }
.user-avatar { color: #4f5668; background: #e9ebf0; }
.message-body { display: flex; flex-direction: column; align-items: flex-start; max-width: min(680px, 78%); }
.message-author { margin-bottom: 6px; color: #8c94a3; font-size: 11px; font-weight: 700; }
.message-body p { margin: 0; padding: 12px 15px; border-radius: 5px 17px 17px 17px; color: #323b4d; background: #f0f1f4; font-size: 14px; line-height: 1.75; white-space: pre-wrap; }
.chat-row.user .message-body p { border-radius: 17px 5px 17px 17px; color: #fff; background: #5d52cf; }
.typing { display: flex; gap: 5px; padding: 15px 17px; border-radius: 5px 17px 17px 17px; background: #f0f1f4; }
.typing i { width: 6px; height: 6px; border-radius: 50%; background: #8f96a3; animation: typing 1.1s infinite ease-in-out; }
.typing i:nth-child(2) { animation-delay: .16s; }.typing i:nth-child(3) { animation-delay: .32s; }
.composer-area { padding: 10px 18px 14px; border-top: 1px solid #eceef2; background: #fff; }
.quick-actions, .chat-composer, .composer-hint, .chat-warning { width: min(820px, 100%); margin-left: auto; margin-right: auto; }
.quick-actions { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.quick-actions button { display: flex; align-items: center; gap: 6px; padding: 7px 10px; border: 0; border-radius: 999px; color: #5146cf; background: #f1efff; font-size: 12px; font-weight: 700; }
.quick-actions > span { color: #a0a6b0; font-size: 10px; }
.chat-composer { display: flex; align-items: flex-end; gap: 10px; padding: 10px 11px 10px 16px; border: 1px solid #d9dde5; border-radius: 19px; box-shadow: 0 5px 20px rgba(31, 42, 68, .07); }
.chat-composer:focus-within { border-color: #7569df; box-shadow: 0 0 0 4px rgba(109, 93, 231, .09); }
.chat-composer textarea { width: 100%; min-height: 28px; max-height: 130px; padding: 5px 0; overflow-y: auto; border: 0; outline: 0; resize: none; color: #242c3b; background: transparent; font: inherit; line-height: 1.55; }
.send-button { display: grid; place-items: center; width: 38px; height: 38px; flex: 0 0 auto; border: 0; border-radius: 50%; color: #fff; background: #24262b; font-size: 21px; }
.send-button:disabled { cursor: default; opacity: .3; }
.composer-hint { margin-top: 7px; margin-bottom: 0; color: #a0a6b0; text-align: center; font-size: 10px; }
.chat-warning { margin-top: 0; margin-bottom: 8px; padding: 8px 11px; border-radius: 9px; color: #936816; background: #fff7df; font-size: 12px; }
button { cursor: pointer; }
button:disabled { cursor: default; opacity: .55; }
@keyframes typing { 0%, 60%, 100% { transform: translateY(0); opacity: .45; } 30% { transform: translateY(-4px); opacity: 1; } }
@media (max-width: 760px) {
  .profile-chat-page { height: calc(100vh - 125px); min-height: 570px; border-radius: 15px; }
  .chat-header { align-items: stretch; flex-direction: column; }
  .header-actions { justify-content: space-between; }
  .message-column { width: calc(100% - 24px); padding-top: 24px; }
  .message-body { max-width: 82%; }
  .quick-actions > span { display: none; }
}
</style>
