<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { chatDynamicProfile, getDynamicProfile, getNextProfileQuestion } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import type { DynamicProfile } from '../types/profile'

const userId = ref('demo_user_001')
const course = ref('数据库系统')
const courses = ['数据库系统', '数据结构', '算法设计', '操作系统', '计算机网络', '软件工程']
const message = ref('')
const loading = ref(false)
const error = ref('')
const profile = ref<DynamicProfile | null>(null)
const replies = ref<{ role: 'assistant' | 'user'; content: string }[]>([])
const dimensions = computed(() => profile.value?.dimension_catalog || [])

async function loadProfile() {
  const result = await getDynamicProfile(userId.value)
  profile.value = result.profile
}

async function askNextQuestion(reset = false) {
  if (loading.value) return
  loading.value = true
  error.value = ''
  if (reset) replies.value = []
  try {
    const result = await getNextProfileQuestion({ ...loadSiliconFlowConfig(), user_id: userId.value, course: course.value })
    profile.value = result.profile
    replies.value.push({ role: 'assistant', content: result.question })
    if (result.warning) error.value = `主动访谈使用规则回退：${result.warning}`
  } catch (err) {
    error.value = err instanceof Error ? err.message : '生成访谈问题失败'
  } finally {
    loading.value = false
  }
}

async function changeCourse() {
  await askNextQuestion(true)
}

async function sendMessage() {
  if (!message.value.trim() || loading.value) return
  const content = message.value.trim()
  replies.value.push({ role: 'user', content })
  message.value = ''
  loading.value = true
  error.value = ''
  try {
    const result = await chatDynamicProfile({ ...loadSiliconFlowConfig(), user_id: userId.value, course: course.value, message: content })
    profile.value = result.profile
    replies.value.push({ role: 'assistant', content: result.reply })
    if (result.warning) error.value = `已使用规则回退：${result.warning}`
    await askNextQuestion()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '画像更新失败'
  } finally {
    loading.value = false
  }
}

function displayValue(value: string | string[] | undefined) {
  if (!value) return '等待对话补充'
  return Array.isArray(value) ? value.join('、') : value
}

onMounted(async () => {
  await loadProfile()
  await askNextQuestion(true)
})
</script>

<template>
  <div class="profile-builder">
    <section class="surface profile-chat">
      <div class="profile-chat-head">
        <div><span class="section-kicker">AI 主动画像访谈</span><h2>和学习助手聊聊你的情况</h2></div>
        <div class="profile-user-fields">
          <select v-model="course" @change="changeCourse"><option v-for="item in courses" :key="item" :value="item">{{ item }}</option></select>
        </div>
      </div>
      <div class="chat-stream"><div v-for="(item, index) in replies" :key="index" :class="['chat-bubble', `chat-${item.role}`]">{{ item.content }}</div><div v-if="loading" class="chat-bubble chat-assistant">正在理解并更新画像...</div></div>
      <form class="chat-composer" @submit.prevent="sendMessage"><textarea v-model="message" rows="3" :placeholder="`回答 AI 关于《${course}》的问题，画像会持续更新……`"></textarea><div class="chat-composer-actions"><button type="button" class="btn-secondary" :disabled="loading" @click="askNextQuestion()">换一个问题</button><button class="btn-primary" :disabled="loading">回答并继续访谈</button></div></form>
      <p v-if="error" class="profile-warning">{{ error }}</p>
    </section>
    <section class="profile-board">
      <div class="profile-summary"><div><span>画像完成度</span><strong>{{ profile?.completion || 0 }}%</strong></div><div><span>画像版本</span><strong>V{{ profile?.version || 0 }}</strong></div><div><span>已识别维度</span><strong>{{ Object.keys(profile?.dimensions || {}).length }}/{{ dimensions.length || 8 }}</strong></div></div>
      <div class="profile-dimension-grid"><article v-for="name in dimensions" :key="name" class="surface dimension-card"><div class="dimension-head"><span>{{ name }}</span><b>{{ Math.round((profile?.dimensions[name]?.confidence || 0) * 100) }}%</b></div><p>{{ displayValue(profile?.dimensions[name]?.value) }}</p><small>{{ profile?.dimensions[name]?.evidence || '继续对话后自动补全' }}</small></article></div>
    </section>
  </div>
</template>
