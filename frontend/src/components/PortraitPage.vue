<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { loadUserProfile } from '../api/userProfile'
import { chatDynamicProfile, getDynamicProfile, getNextProfileQuestion } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import type { DynamicProfile } from '../types/profile'

const userProfile = ref(loadUserProfile())
const portrait = ref<DynamicProfile | null>(null)
const replies = ref<{
  role: 'assistant' | 'user'
  content: string
}[]>([])
const portraitLoading = ref(false)
const portraitError = ref('')
const course = ref('数据库系统')
const courses = ['数据库系统', '数据结构', '算法设计', '操作系统', '计算机网络', '软件工程']
const isPortraitBuilt = ref(false)
const showPortrait = ref(false)

const userMessage = ref('')

const dimensions = computed(() => portrait.value?.dimension_catalog || [
  '专业与年级', '学习目标', '知识基础', '认知风格',
  '学习偏好', '时间安排', '学习动机', '能力水平'
])

const dimensionIcons: Record<string, string> = {
  '专业与年级': '🎓',
  '学习目标': '🎯',
  '知识基础': '📚',
  '认知风格': '🧠',
  '学习偏好': '⚡',
  '时间安排': '⏰',
  '学习动机': '🔥',
  '能力水平': '💪'
}

function displayDimensionValue(value: string | string[] | undefined) {
  if (!value) return '等待对话补充'
  return Array.isArray(value) ? value.join('、') : value
}

function getConfidenceColor(confidence: number) {
  if (confidence >= 0.8) return 'text-green-500'
  if (confidence >= 0.5) return 'text-yellow-500'
  return 'text-gray-400'
}

function getConfidenceBarColor(confidence: number) {
  if (confidence >= 0.8) return 'bg-green-500'
  if (confidence >= 0.5) return 'bg-yellow-500'
  return 'bg-gray-300'
}

async function loadPortrait() {
  try {
    const result = await getDynamicProfile(userProfile.value.userId)
    portrait.value = result.profile
    isPortraitBuilt.value = portrait.value && portrait.value.completion > 0
  } catch (err) {
    console.error('加载画像失败', err)
    portrait.value = null
    isPortraitBuilt.value = false
  }
}

async function startPortraitBuild(reset = false) {
  if (portraitLoading.value) return
  portraitLoading.value = true
  portraitError.value = ''
  if (reset) replies.value = []
  
  try {
    const result = await getNextProfileQuestion({
      ...loadSiliconFlowConfig(),
      user_id: userProfile.value.userId,
      course: course.value
    })
    portrait.value = result.profile
    replies.value.push({ role: 'assistant', content: result.question })
    if (result.warning) portraitError.value = `提示：${result.warning}`
  } catch (err) {
    portraitError.value = err instanceof Error ? err.message : '生成访谈问题失败'
  } finally {
    portraitLoading.value = false
  }
}

async function changeCourse() {
  await startPortraitBuild(true)
}

async function sendPortraitMessage() {
  if (!userMessage.value.trim() || portraitLoading.value) return
  const content = userMessage.value.trim()
  replies.value.push({ role: 'user', content })
  userMessage.value = ''
  portraitLoading.value = true
  portraitError.value = ''
  
  try {
    const result = await chatDynamicProfile({
      ...loadSiliconFlowConfig(),
      user_id: userProfile.value.userId,
      course: course.value,
      message: content
    })
    portrait.value = result.profile
    replies.value.push({ role: 'assistant', content: result.reply })
    if (result.warning) portraitError.value = `提示：${result.warning}`
    await askNextQuestion()
  } catch (err) {
    portraitError.value = err instanceof Error ? err.message : '画像更新失败'
  } finally {
    portraitLoading.value = false
  }
}

async function askNextQuestion() {
  try {
    const result = await getNextProfileQuestion({
      ...loadSiliconFlowConfig(),
      user_id: userProfile.value.userId,
      course: course.value
    })
    portrait.value = result.profile
    replies.value.push({ role: 'assistant', content: result.question })
  } catch (err) {
    console.error('获取下一问题失败', err)
  }
}

onMounted(async () => {
  await loadPortrait()
})
</script>

<template>
  <div class="portrait-chat-page">
    <div class="portrait-chat-container">
      <div class="chat-header">
        <h2>💬 画像构建对话</h2>
        <div class="chat-actions">
          <button class="btn-outline" @click="showPortrait = !showPortrait">
            {{ showPortrait ? '隐藏画像' : '👁 查看画像' }}
          </button>
        </div>
      </div>

      <div class="chat-course-select">
        <label>选择课程：</label>
        <select v-model="course" @change="changeCourse">
          <option v-for="item in courses" :key="item" :value="item">{{ item }}</option>
        </select>
      </div>

      <div class="chat-messages">
        <div v-if="replies.length === 0" class="chat-empty">
          <div class="empty-icon">🤖</div>
          <p>开始与AI对话，构建您的学习画像</p>
          <button class="btn-primary" @click="startPortraitBuild(true)" :disabled="portraitLoading">
            {{ portraitLoading ? '加载中...' : '🚀 开始对话' }}
          </button>
        </div>
        
        <div 
          v-for="(item, index) in replies" 
          :key="index" 
          :class="['chat-bubble', `chat-${item.role}`]"
        >
          <span class="bubble-avatar">{{ item.role === 'assistant' ? '🤖' : '👤' }}</span>
          <div class="bubble-content">{{ item.content }}</div>
        </div>
        
        <div v-if="portraitLoading && replies.length > 0" class="chat-bubble chat-assistant">
          <span class="bubble-avatar">🤖</span>
          <div class="bubble-content">正在理解并更新画像...</div>
        </div>
      </div>

      <form v-if="replies.length > 0" class="chat-input" @submit.prevent="sendPortraitMessage">
        <textarea 
          v-model="userMessage" 
          rows="3" 
          :placeholder="`回答AI关于《${course}》的问题，画像会持续更新……`"
          :disabled="portraitLoading"
        ></textarea>
        <div class="chat-input-actions">
          <button type="button" class="btn-secondary" :disabled="portraitLoading" @click="askNextQuestion">
            换一个问题
          </button>
          <button type="submit" class="btn-primary" :disabled="portraitLoading">
            {{ portraitLoading ? '发送中...' : '回答并继续' }}
          </button>
        </div>
      </form>

      <p v-if="portraitError" class="chat-warning">{{ portraitError }}</p>
    </div>

    <Transition name="slide">
      <div v-if="showPortrait" class="portrait-panel">
        <div class="portrait-header">
          <h3>🎯 我的学习画像</h3>
          <button class="close-btn" @click="showPortrait = false">✕</button>
        </div>

        <div v-if="!portrait" class="portrait-empty">
          <div class="empty-icon">🎯</div>
          <h3>尚未构建学习画像</h3>
          <p>与AI对话后将自动生成您的学习画像</p>
        </div>

        <div v-else class="portrait-content">
          <div class="portrait-summary">
            <div class="summary-item">
              <div class="summary-value">{{ portrait.completion || 0 }}%</div>
              <div class="summary-label">完成度</div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: (portrait.completion || 0) + '%' }"></div>
              </div>
            </div>
            <div class="summary-item">
              <div class="summary-value">V{{ portrait.version || 1 }}</div>
              <div class="summary-label">版本</div>
            </div>
            <div class="summary-item">
              <div class="summary-value">{{ Object.keys(portrait.dimensions || {}).length }}/{{ dimensions.length }}</div>
              <div class="summary-label">已识别维度</div>
            </div>
          </div>

          <div class="dimension-grid">
            <article v-for="name in dimensions" :key="name" class="dimension-card">
              <div class="dimension-header">
                <span class="dimension-icon">{{ dimensionIcons[name] || '📌' }}</span>
                <span class="dimension-name">{{ name }}</span>
                <span :class="['dimension-confidence', getConfidenceColor(portrait.dimensions[name]?.confidence || 0)]">
                  {{ Math.round((portrait.dimensions[name]?.confidence || 0) * 100) }}%
                </span>
              </div>
              <div class="dimension-confidence-bar">
                <div :class="['confidence-fill', getConfidenceBarColor(portrait.dimensions[name]?.confidence || 0)]"
                     :style="{ width: (portrait.dimensions[name]?.confidence || 0) * 100 + '%' }"></div>
              </div>
              <p class="dimension-value">{{ displayDimensionValue(portrait.dimensions[name]?.value) }}</p>
              <p class="dimension-evidence">{{ portrait.dimensions[name]?.evidence || '继续对话后自动补全' }}</p>
            </article>
          </div>

          <div class="portrait-footer">
            <div class="auto-update">
              <span class="update-icon">🔄</span>
              <span>画像会根据您的学习行为自动更新</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.portrait-chat-page {
  display: flex;
  gap: 16px;
  height: calc(100vh - 120px);
}

.portrait-chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #e5e7eb;
}

.chat-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.chat-course-select {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
}

.chat-course-select select {
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 14px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.chat-empty p {
  color: #6b7280;
  margin-bottom: 20px;
}

.chat-bubble {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.chat-user {
  flex-direction: row-reverse;
}

.bubble-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.chat-assistant .bubble-avatar {
  background: #f3f4f6;
}

.chat-user .bubble-avatar {
  background: #6366f1;
  color: white;
}

.bubble-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.6;
}

.chat-assistant .bubble-content {
  background: #f3f4f6;
  border-radius: 16px 16px 16px 4px;
}

.chat-user .bubble-content {
  background: #6366f1;
  color: white;
  border-radius: 16px 16px 4px 16px;
}

.chat-input {
  padding: 12px 14px;
  border-top: 1px solid #e5e7eb;
}

.chat-input textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  margin-bottom: 10px;
  box-sizing: border-box;
}

.chat-input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.chat-warning {
  padding: 10px 14px;
  background: #fef3c7;
  color: #d97706;
  font-size: 13px;
  margin: 0;
}

.portrait-panel {
  width: 450px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.portrait-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.portrait-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: #9ca3af;
  padding: 4px;
}

.portrait-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
}

.portrait-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.portrait-summary {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.summary-item {
  flex: 1;
  text-align: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: #6366f1;
}

.summary-label {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.progress-bar {
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.dimension-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.dimension-card {
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.dimension-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.dimension-icon {
  font-size: 18px;
}

.dimension-name {
  flex: 1;
  font-weight: 500;
  font-size: 14px;
}

.dimension-confidence {
  font-size: 14px;
  font-weight: 600;
}

.dimension-confidence-bar {
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  margin-bottom: 12px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.dimension-value {
  font-size: 14px;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.dimension-evidence {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}

.portrait-footer {
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.auto-update {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #ecfdf5;
  border-radius: 8px;
  font-size: 13px;
  color: #059669;
}

.update-icon {
  font-size: 14px;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
