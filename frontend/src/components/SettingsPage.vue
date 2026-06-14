<script setup lang="ts">
import { ref } from 'vue'
import { testSiliconFlow } from '../api/client'
import { loadSiliconFlowConfig, saveSiliconFlowConfig } from '../api/settings'

const config = ref(loadSiliconFlowConfig())
const showKey = ref(false)
const testing = ref(false)
const message = ref('')
const isError = ref(false)

function save() {
  saveSiliconFlowConfig(config.value)
  isError.value = false
  message.value = '配置已保存在当前浏览器中'
}

async function testConnection() {
  testing.value = true
  message.value = ''
  try {
    const result = await testSiliconFlow(config.value)
    saveSiliconFlowConfig(config.value)
    isError.value = false
    message.value = `${result.model}：${result.message}`
  } catch (error) {
    isError.value = true
    message.value = error instanceof Error ? error.message : '连接测试失败'
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <div class="settings-layout">
    <section class="surface settings-card">
      <span class="section-kicker">模型服务</span>
      <h2>硅基流动 API 设置</h2>
      <p class="settings-intro">用于画像对话和多智能体资源生成。API Key 仅保存在当前浏览器，请求时临时发送，后端不会持久化密钥。</p>
      <div class="settings-form">
        <label><span>API Key</span><div class="secret-input"><input v-model="config.api_key" :type="showKey ? 'text' : 'password'" placeholder="sk-..." /><button type="button" @click="showKey = !showKey">{{ showKey ? '隐藏' : '显示' }}</button></div></label>
        <label><span>Base URL</span><input v-model="config.base_url" type="url" /></label>
        <label><span>模型标识</span><input v-model="config.model" type="text" /><small>默认采用官方当前可用的 Pro DeepSeek 模型，也可填写你的 DeepSeek-V4-Pro 实际模型标识。</small></label>
      </div>
      <div class="settings-actions"><button class="btn-secondary" @click="save">保存设置</button><button class="btn-primary" :disabled="testing" @click="testConnection">{{ testing ? '正在测试...' : '测试连接' }}</button></div>
      <div v-if="message" :class="['settings-message', isError ? 'settings-message-error' : '']">{{ message }}</div>
    </section>
    <aside class="surface settings-note">
      <span class="section-kicker">使用说明</span><h2>画像随学随新</h2><p>每次画像对话都会提取新证据，并持续更新画像版本、维度置信度与最近交流记录。</p>
      <div class="settings-fact"><b>8</b><span>画像维度</span></div><div class="settings-fact"><b>20</b><span>最近对话证据</span></div><div class="settings-fact"><b>JSON</b><span>持久化画像</span></div>
    </aside>
  </div>
</template>
