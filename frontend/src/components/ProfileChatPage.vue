<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { chatDynamicProfile, getDynamicProfile } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import type { DynamicProfile } from '../types/profile'

const userId = ref('demo_user_001')
const course = ref('数据库系统')
const message = ref('')
const loading = ref(false)
const error = ref('')
const profile = ref<DynamicProfile | null>(null)
const replies = ref<{ role: 'assistant' | 'user'; content: string }[]>([
  { role: 'assistant', content: '你好，我会通过轻量对话持续了解你的学习情况。先介绍一下你的专业、当前目标，以及最困扰你的知识点吧。' }
])
const dimensions = computed(() => profile.value?.dimension_catalog || [])

async function loadProfile() {
  const result = await getDynamicProfile(userId.value)
  profile.value = result.profile
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

onMounted(loadProfile)
</script>

<template>
  <div class="profile-builder">
    <section class="surface profile-chat">
      <div class="profile-chat-head"><div><span class="section-kicker">自然语言画像共建</span><h2>和学习助手聊聊你的情况</h2></div><div class="profile-user-fields"><input v-model="userId" @change="loadProfile" /><input v-model="course" /></div></div>
      <div class="chat-stream"><div v-for="(item, index) in replies" :key="index" :class="['chat-bubble', `chat-${item.role}`]">{{ item.content }}</div><div v-if="loading" class="chat-bubble chat-assistant">正在理解并更新画像...</div></div>
      <form class="chat-composer" @submit.prevent="sendMessage"><textarea v-model="message" rows="3" placeholder="例如：我是软件工程大三学生，准备考研。数据库范式总是判断错，晚上更适合通过例题学习……"></textarea><button class="btn-primary" :disabled="loading">发送并更新画像</button></form>
      <p v-if="error" class="profile-warning">{{ error }}</p>
    </section>
    <section class="profile-board">
      <div class="profile-summary"><div><span>画像完成度</span><strong>{{ profile?.completion || 0 }}%</strong></div><div><span>画像版本</span><strong>V{{ profile?.version || 0 }}</strong></div><div><span>已识别维度</span><strong>{{ Object.keys(profile?.dimensions || {}).length }}/{{ dimensions.length || 8 }}</strong></div></div>
      <div class="profile-dimension-grid"><article v-for="name in dimensions" :key="name" class="surface dimension-card"><div class="dimension-head"><span>{{ name }}</span><b>{{ Math.round((profile?.dimensions[name]?.confidence || 0) * 100) }}%</b></div><p>{{ displayValue(profile?.dimensions[name]?.value) }}</p><small>{{ profile?.dimensions[name]?.evidence || '继续对话后自动补全' }}</small></article></div>
    </section>
  </div>
</template>
