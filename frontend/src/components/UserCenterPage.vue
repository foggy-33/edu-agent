<script setup lang="ts">
import { computed, ref } from 'vue'
import { testSiliconFlow } from '../api/client'
import { loadSiliconFlowConfig, saveSiliconFlowConfig } from '../api/settings'
import { defaultUserProfile, loadUserProfile, saveUserProfile } from '../api/userProfile'

const emit = defineEmits<{
  logout: []
}>()

const userProfile = ref(loadUserProfile())
const fileInput = ref<HTMLInputElement | null>(null)
const userError = ref('')
const userSuccess = ref('')

const apiConfig = ref(loadSiliconFlowConfig())
const apiShowKey = ref(false)
const apiTesting = ref(false)
const apiMessage = ref('')
const apiError = ref(false)

const initials = computed(() => userProfile.value.name.trim().slice(0, 1).toUpperCase() || 'U')

function chooseAvatar() {
  fileInput.value?.click()
}

function handleAvatar(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    userError.value = '请选择图片文件'
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    userError.value = '头像图片不能超过 2 MB'
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    userProfile.value.avatar = String(reader.result || '')
    userError.value = ''
  }
  reader.readAsDataURL(file)
}

function saveProfile() {
  if (!userProfile.value.name.trim()) {
    userError.value = '名称不能为空'
    return
  }
  userProfile.value.name = userProfile.value.name.trim()
  saveUserProfile(userProfile.value)
  userError.value = ''
  userSuccess.value = '个人资料已保存'
}

function reset() {
  userProfile.value = { ...defaultUserProfile }
  saveUserProfile(userProfile.value)
  userError.value = ''
  userSuccess.value = '已恢复默认资料'
}

function normalizeApiConfig() {
  apiConfig.value = {
    ...apiConfig.value,
    api_key: apiConfig.value.api_key.trim(),
    base_url: apiConfig.value.base_url.trim() || 'https://api.siliconflow.cn/v1',
    model: apiConfig.value.model.trim() || 'deepseek-ai/DeepSeek-V4-Pro',
  }
}

function saveApiSettings() {
  normalizeApiConfig()
  saveSiliconFlowConfig(apiConfig.value)
  apiError.value = false
  apiMessage.value = 'API 设置已保存到当前浏览器'
}

async function testApiSettings() {
  saveApiSettings()
  if (!apiConfig.value.api_key.trim()) {
    apiError.value = true
    apiMessage.value = '请先填写 API Key'
    return
  }
  apiTesting.value = true
  try {
    const result = await testSiliconFlow(apiConfig.value)
    apiError.value = false
    apiMessage.value = `${result.model}：${result.message}`
  } catch (err) {
    apiError.value = true
    apiMessage.value = err instanceof Error ? err.message : '连接测试失败'
  } finally {
    apiTesting.value = false
  }
}
</script>

<template>
  <div class="settings-container">
    <section class="settings-hero">
      <div>
        <span>SETTINGS</span>
        <h1>账户设置</h1>
        <p>管理账号资料和系统设置</p>
      </div>
      <div class="hero-avatar">
        <img v-if="userProfile.avatar" :src="userProfile.avatar" alt="用户头像" />
        <span v-else>{{ initials }}</span>
      </div>
    </section>

    <div class="settings-grid">
      <section class="profile-section">
        <header>
          <span>ACCOUNT</span>
          <h2>个人资料</h2>
        </header>

        <div class="profile-preview">
          <div class="preview-avatar">
            <img v-if="userProfile.avatar" :src="userProfile.avatar" alt="用户头像" />
            <span v-else>{{ initials }}</span>
          </div>
          <div class="preview-info">
            <div class="preview-name">{{ userProfile.name }}</div>
            <div class="preview-id">ID: {{ userProfile.userId }}</div>
          </div>
          <button class="btn-secondary" type="button" @click="chooseAvatar">更换头像</button>
          <input ref="fileInput" type="file" accept="image/*" hidden @change="handleAvatar" />
          <small class="avatar-hint">支持 JPG、PNG、WebP，文件不超过 2 MB</small>
        </div>

        <div class="profile-info-grid">
          <div class="info-card">
            <div class="info-icon">📱</div>
            <div class="info-content">
              <span class="info-label">手机号码</span>
              <span class="info-value">{{ userProfile.phone || '未填写' }}</span>
            </div>
          </div>
          <div class="info-card">
            <div class="info-icon">📧</div>
            <div class="info-content">
              <span class="info-label">邮箱地址</span>
              <span class="info-value">{{ userProfile.email || '未填写' }}</span>
            </div>
          </div>
          <div class="info-card">
            <div class="info-icon">🏛️</div>
            <div class="info-content">
              <span class="info-label">所在院校</span>
              <span class="info-value">{{ userProfile.school || '未填写' }}</span>
            </div>
          </div>
          <div class="info-card">
            <div class="info-icon">📚</div>
            <div class="info-content">
              <span class="info-label">专业班级</span>
              <span class="info-value">{{ userProfile.major || '未填写' }}</span>
            </div>
          </div>
        </div>

        <div class="profile-form">
          <div class="form-group">
            <label>显示名称</label>
            <input v-model="userProfile.name" maxlength="30" placeholder="请输入显示名称" />
          </div>
          <div class="form-group">
            <label>手机号码</label>
            <input v-model="userProfile.phone" placeholder="请输入手机号码" />
          </div>
          <div class="form-group">
            <label>邮箱地址</label>
            <input v-model="userProfile.email" type="email" placeholder="请输入邮箱地址" />
          </div>
          <div class="form-group">
            <label>所在院校</label>
            <input v-model="userProfile.school" placeholder="请输入院校名称" />
          </div>
          <div class="form-group">
            <label>专业班级</label>
            <input v-model="userProfile.major" placeholder="请输入专业班级" />
          </div>
        </div>

        <div class="profile-actions">
          <button class="btn-secondary" type="button" @click="reset">恢复默认</button>
          <button class="btn-primary" type="button" @click="saveProfile">保存资料</button>
        </div>

        <div v-if="userSuccess" class="message success">{{ userSuccess }}</div>
        <div v-if="userError" class="message error">{{ userError }}</div>
      </section>

      <section class="api-section">
        <header>
          <div>
            <span>API SETTINGS</span>
            <h2>API 设置</h2>
          </div>
          <span class="model-tag">{{ apiConfig.model }}</span>
        </header>

        <p class="api-note">
          当前项目使用硅基流动兼容 OpenAI 的接口。这里保存的是当前浏览器配置，会被首页对话、个性化资源生成、课程练习和画像对话共用。
        </p>

        <div class="api-form">
          <div class="form-group">
            <label>API Key</label>
            <div class="secret-input">
              <input v-model="apiConfig.api_key" :type="apiShowKey ? 'text' : 'password'" placeholder="sk-..." />
              <button type="button" @click="apiShowKey = !apiShowKey">{{ apiShowKey ? '隐藏' : '显示' }}</button>
            </div>
          </div>
          <div class="form-group">
            <label>Base URL</label>
            <input v-model="apiConfig.base_url" type="url" placeholder="https://api.siliconflow.cn/v1" />
          </div>
          <div class="form-group">
            <label>模型</label>
            <input v-model="apiConfig.model" placeholder="deepseek-ai/DeepSeek-V4-Pro" />
          </div>
        </div>

        <div class="api-actions">
          <button class="btn-secondary" type="button" @click="saveApiSettings">保存设置</button>
          <button class="btn-primary" type="button" :disabled="apiTesting" @click="testApiSettings">
            {{ apiTesting ? '正在测试...' : '测试连接' }}
          </button>
        </div>

        <p v-if="apiMessage" :class="['message', apiError ? 'error' : 'success']">{{ apiMessage }}</p>
      </section>
    </div>

    <section class="security-section">
      <header>
        <span>SECURITY</span>
        <h2>安全设置</h2>
      </header>
      <div class="security-actions">
        <button class="logout-button" type="button" @click="emit('logout')">退出当前账号</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.settings-container {
  display: grid;
  gap: 22px;
  max-width: 1220px;
  margin: 0 auto;
  color: #241d35;
}

.settings-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  padding: 30px;
  border: 1px solid #eee9ff;
  border-radius: 24px;
  background:
    radial-gradient(circle at 92% 18%, rgba(139, 92, 246, .18), transparent 18rem),
    #fff;
  box-shadow: 0 18px 45px rgba(93, 73, 170, .08);
}

.settings-hero span {
  color: #8b75d7;
  font-size: 10px;
  font-weight: 850;
  letter-spacing: .14em;
}

.settings-hero h1 {
  margin: 7px 0 8px;
  color: #25144f;
  font-size: clamp(26px, 4vw, 38px);
  font-weight: 780;
}

.settings-hero p {
  margin: 0;
  color: #80758f;
  font-size: 14px;
}

.hero-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 108px;
  height: 108px;
  border-radius: 50%;
  color: #fff;
  background: linear-gradient(135deg, #6d5df2, #a855f7);
  font-size: 40px;
  overflow: hidden;
}

.hero-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.settings-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 500px);
  gap: 22px;
  align-items: start;
}

.profile-section,
.api-section,
.security-section {
  border: 1px solid #eee9ff;
  border-radius: 22px;
  background: #fff;
  box-shadow: 0 14px 38px rgba(93, 73, 170, .08);
  padding: 24px;
}

.profile-section header,
.api-section header,
.security-section header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.profile-section header span,
.api-section header span,
.security-section header span {
  color: #8b75d7;
  font-size: 10px;
  font-weight: 850;
  letter-spacing: .14em;
}

.profile-section h2,
.api-section h2,
.security-section h2 {
  margin: 5px 0 0;
  color: #25144f;
  font-size: 22px;
  font-weight: 760;
}

.model-tag {
  padding: 6px 10px;
  border-radius: 999px;
  color: #5b35c8;
  background: #f0ebff;
  font-size: 12px;
  font-weight: 600;
}

.profile-preview {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  padding: 20px;
  margin-top: 20px;
  border-radius: 16px;
  background: linear-gradient(135deg, #f0ebff, #fff);
}

.preview-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  color: #fff;
  background: linear-gradient(135deg, #6d5df2, #a855f7);
  font-size: 32px;
  overflow: hidden;
}

.preview-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-info {
  flex: 1;
}

.preview-name {
  font-size: 18px;
  font-weight: 760;
  color: #25144f;
}

.preview-id {
  font-size: 13px;
  color: #80758f;
  margin-top: 4px;
}

.profile-preview .btn-secondary {
  padding: 8px 14px;
  border-radius: 10px;
  font-weight: 720;
}

.avatar-hint {
  flex: 1;
  width: 100%;
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.profile-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 20px;
}

.info-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 12px;
  background: #f9fafb;
}

.info-icon {
  font-size: 20px;
}

.info-content {
  display: flex;
  flex-direction: column;
}

.info-label {
  font-size: 12px;
  color: #6b7280;
}

.info-value {
  font-size: 14px;
  color: #241d35;
  font-weight: 500;
  margin-top: 2px;
}

.profile-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 6px;
  color: #5f526f;
  font-size: 13px;
  font-weight: 700;
}

.form-group input {
  padding: 10px 12px;
  border: 1px solid #e7ddff;
  border-radius: 10px;
  color: #241d35;
  background: #fff;
  font-size: 14px;
}

.form-group input:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, .1);
}

.profile-actions,
.api-actions,
.security-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}

.profile-actions button,
.api-actions button {
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 720;
}

.btn-primary {
  border: 0;
  color: #fff;
  background: linear-gradient(135deg, #6d5df2, #9d6cff);
  box-shadow: 0 12px 24px rgba(109, 93, 242, .22);
}

.btn-secondary {
  border: 0;
  color: #5b35c8;
  background: #f0ebff;
}

.logout-button {
  padding: 12px 24px;
  border: 1px solid #f5c2c7;
  border-radius: 10px;
  color: #c82828;
  background: #fff;
  font-weight: 720;
}

.message {
  padding: 12px 16px;
  border-radius: 10px;
  margin-top: 16px;
  font-size: 13px;
}

.message.success {
  background: #f0ebff;
  color: #5b35c8;
}

.message.error {
  background: #fef2f2;
  color: #dc2626;
}

.api-note {
  margin: 14px 0 18px;
  color: #80758f;
  font-size: 13px;
  line-height: 1.7;
}

.api-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.secret-input {
  display: flex;
  gap: 8px;
}

.secret-input input {
  flex: 1;
  min-width: 0;
}

.secret-input button {
  flex: 0 0 auto;
  padding: 0 14px;
  border: 0;
  border-radius: 10px;
  color: #5b35c8;
  background: #f0ebff;
  font-weight: 750;
}

.security-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
}

.security-actions {
  margin: 0;
}

@media (max-width: 900px) {
  .settings-container {
    max-width: none;
  }

  .settings-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .settings-grid {
    grid-template-columns: 1fr;
  }

  .profile-info-grid {
    grid-template-columns: 1fr;
  }

  .profile-form {
    grid-template-columns: 1fr;
  }

  .security-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
  }
}
</style>