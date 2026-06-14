<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { defaultUserProfile, loadUserProfile, saveUserProfile } from '../api/userProfile'
import { getDynamicProfile } from '../api/client'
import type { DynamicProfile } from '../types/profile'

const emit = defineEmits<{
  navigate: [page: 'portrait']
  logout: []
}>()

const userProfile = ref(loadUserProfile())
const fileInput = ref<HTMLInputElement | null>(null)
const userError = ref('')
const userSuccess = ref('')
const initials = computed(() => userProfile.value.name.trim().slice(0, 1).toUpperCase() || 'U')

const portrait = ref<DynamicProfile | null>(null)
const portraitLoading = ref(false)

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
  userSuccess.value = '个人资料已保存，并同步到侧边栏'
}

function reset() {
  userProfile.value = { ...defaultUserProfile }
  saveUserProfile(userProfile.value)
  userError.value = ''
  userSuccess.value = '已恢复默认资料'
}

async function loadPortrait() {
  portraitLoading.value = true
  try {
    const result = await getDynamicProfile(userProfile.value.userId)
    portrait.value = result.profile
  } catch (err) {
    console.error('加载画像失败', err)
    portrait.value = null
  } finally {
    portraitLoading.value = false
  }
}

function goToPortraitPage() {
  emit('navigate', 'portrait')
}

onMounted(async () => {
  await loadPortrait()
})
</script>

<template>
  <div class="user-center-container">
    <div class="profile-section">
      <div class="profile-card">
        <div class="profile-header">
          <h2>👤 个人资料</h2>
        </div>
        
        <div class="profile-avatar-section">
          <div class="profile-avatar-large">
            <img v-if="userProfile.avatar" :src="userProfile.avatar" alt="用户头像" />
            <span v-else>{{ initials }}</span>
          </div>
          <button class="btn-secondary" @click="chooseAvatar">更换头像</button>
          <input ref="fileInput" type="file" accept="image/*" hidden @change="handleAvatar" />
          <small>支持 JPG、PNG、WebP，文件不超过 2 MB</small>
        </div>

        <div class="profile-form">
          <div class="form-group">
            <label>显示名称</label>
            <input v-model="userProfile.name" maxlength="30" placeholder="请输入显示名称" />
          </div>
          
          <div class="form-group">
            <label>用户 ID</label>
            <input :value="userProfile.userId" disabled />
            <small>用户 ID 用于关联动态学习画像，当前不可修改。</small>
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
          <button class="btn-secondary" @click="reset">恢复默认</button>
          <button class="btn-primary" @click="saveProfile">保存资料</button>
          <button class="logout-button" @click="emit('logout')">退出当前账号</button>
        </div>

        <div v-if="userSuccess" class="message success">{{ userSuccess }}</div>
        <div v-if="userError" class="message error">{{ userError }}</div>
      </div>
    </div>

    <div class="portrait-section">
      <div class="portrait-card">
        <div class="portrait-header">
          <h2>🎯 我的学习画像</h2>
          <div class="portrait-actions">
            <button class="btn-secondary" @click="loadPortrait" :disabled="portraitLoading">
              {{ portraitLoading ? '刷新中...' : '🔄 自动重构' }}
            </button>
            <button class="btn-primary" @click="goToPortraitPage">
              ✏️ 自我重构
            </button>
          </div>
        </div>

        <div v-if="portraitLoading" class="loading-state">
          <div class="loading-icon">⏳</div>
          <p>正在加载画像...</p>
        </div>

        <div v-else-if="!portrait" class="empty-state">
          <div class="empty-icon">🎯</div>
          <h3>尚未构建学习画像</h3>
          <p>点击「自我重构」按钮，与AI对话构建您的学习画像</p>
          <button class="btn-primary" @click="goToPortraitPage">🚀 开始构建画像</button>
        </div>

        <div v-else class="portrait-content">
          <div class="portrait-summary">
            <div class="summary-card">
              <div class="summary-icon">📊</div>
              <div class="summary-value">{{ portrait.completion || 0 }}%</div>
              <div class="summary-label">完成度</div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: (portrait.completion || 0) + '%' }"></div>
              </div>
            </div>
            <div class="summary-card">
              <div class="summary-icon">📋</div>
              <div class="summary-value">V{{ portrait.version || 1 }}</div>
              <div class="summary-label">版本</div>
            </div>
            <div class="summary-card">
              <div class="summary-icon">🎯</div>
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
    </div>
  </div>
</template>

<style scoped>
.user-center-container {
  display: grid !important;
  grid-template-columns: 1fr 1fr !important;
  gap: 24px !important;
}

.profile-section,
.portrait-section {
  display: flex !important;
  flex-direction: column !important;
}

.profile-card,
.portrait-card {
  background: #fff !important;
  border-radius: 16px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  overflow: hidden !important;
  display: block !important;
  width: auto !important;
  align-items: flex-start !important;
  gap: 0 !important;
  padding: 0 !important;
  margin-bottom: 0 !important;
  border: none !important;
  text-align: left !important;
}

.profile-header,
.portrait-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.profile-header h2,
.portrait-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.portrait-actions {
  display: flex;
  gap: 10px;
}

.profile-avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 20px;
}

.profile-avatar-large {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: white;
  margin-bottom: 16px;
  overflow: hidden;
}

.profile-avatar-large img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-form {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.form-group input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #6366f1;
}

.form-group input:disabled {
  background: #f9fafb;
  color: #9ca3af;
}

.form-group small {
  display: block;
  color: #9ca3af;
  font-size: 12px;
  margin-top: 6px;
}

.profile-actions {
  display: flex;
  gap: 10px;
  padding: 0 20px 20px;
}

.message {
  padding: 12px 16px;
  border-radius: 8px;
  margin: 0 20px 20px;
  font-size: 13px;
}

.message.success {
  background: #ecfdf5;
  color: #059669;
}

.message.error {
  background: #fef2f2;
  color: #dc2626;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.loading-icon,
.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.loading-state p,
.empty-state p {
  color: #6b7280;
  margin-bottom: 20px;
}

.portrait-content {
  padding: 20px;
}

.portrait-summary {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.summary-card {
  flex: 1;
  text-align: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.summary-icon {
  font-size: 24px;
  margin-bottom: 8px;
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
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.dimension-card {
  padding: 14px;
  background: #f8fafc;
  border-radius: 10px;
}

.dimension-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.dimension-icon {
  font-size: 16px;
}

.dimension-name {
  flex: 1;
  font-weight: 500;
  font-size: 13px;
}

.dimension-confidence {
  font-size: 13px;
  font-weight: 600;
}

.dimension-confidence-bar {
  height: 3px;
  background: #e5e7eb;
  border-radius: 2px;
  margin-bottom: 10px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.dimension-value {
  font-size: 13px;
  color: #1f2937;
  margin: 0;
}

.portrait-footer {
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
  margin-top: 20px;
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

@media (max-width: 900px) {
  .user-center-container {
    grid-template-columns: 1fr;
  }
  
  .dimension-grid {
    grid-template-columns: 1fr;
  }
}
</style>
