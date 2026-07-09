<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getDynamicProfile, listDynamicProfiles, testSiliconFlow } from '../api/client'
import { loadSiliconFlowConfig, saveSiliconFlowConfig } from '../api/settings'
import { defaultUserProfile, loadUserProfile, saveUserProfile } from '../api/userProfile'
import type { DynamicProfile, SubjectProfileSummary } from '../types/profile'
import HomePage from './HomePage.vue'

const emit = defineEmits<{
  logout: []
  navigate: [page: 'home' | 'analyze' | 'collaborative' | 'evaluate' | 'courses' | 'account' | 'portrait' | 'resources']
}>()

const userProfile = ref(loadUserProfile())
const fileInput = ref<HTMLInputElement | null>(null)
const userError = ref('')
const userSuccess = ref('')
const profileLoading = ref(false)
const profileError = ref('')
const subjectProfiles = ref<SubjectProfileSummary[]>([])
const selectedCourse = ref('数据库系统')
const portrait = ref<DynamicProfile | null>(null)

const apiConfig = ref(loadSiliconFlowConfig())
const apiShowKey = ref(false)
const apiTesting = ref(false)
const apiMessage = ref('')
const apiError = ref(false)

const initials = computed(() => userProfile.value.name.trim().slice(0, 1).toUpperCase() || 'U')
const activeSubject = computed(() => subjectProfiles.value.find(item => item.course === selectedCourse.value))
const radarMetrics = computed<[string, number][]>(() => {
  const source = portrait.value?.radar_metrics || activeSubject.value?.radar_metrics || {}
  const entries = Object.entries(source)
  if (entries.length) return entries
  return [
    ['概念理解', 52],
    ['应用迁移', 44],
    ['练习表现', 58],
    ['学习稳定性', 48],
    ['资源偏好', 62],
  ]
})
const radarPoints = computed(() => radarMetrics.value.map(([, value], index) => {
  const total = radarMetrics.value.length
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / total
  const radius = 84 * Math.max(0, Math.min(100, Number(value))) / 100
  return `${110 + Math.cos(angle) * radius},${110 + Math.sin(angle) * radius}`
}).join(' '))
const radarAxes = computed(() => radarMetrics.value.map(([name, value], index) => {
  const total = radarMetrics.value.length
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / total
  return {
    name,
    value,
    x: 110 + Math.cos(angle) * 98,
    y: 110 + Math.sin(angle) * 98,
    lineX: 110 + Math.cos(angle) * 88,
    lineY: 110 + Math.sin(angle) * 88,
    anchor: Math.cos(angle) > 0.25 ? 'start' : Math.cos(angle) < -0.25 ? 'end' : 'middle',
  }
}))
const radarRings = computed(() => [20, 40, 60, 80].map(radius => {
  const count = Math.max(radarMetrics.value.length, 3)
  return Array.from({ length: count }, (_, index) => {
    const angle = -Math.PI / 2 + (Math.PI * 2 * index) / count
    return `${110 + Math.cos(angle) * radius},${110 + Math.sin(angle) * radius}`
  }).join(' ')
}))

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
  apiMessage.value = 'API 设置已保存到当前浏览器，首页对话、资源生成和画像对话会共用这份配置。'
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

async function loadPortrait(course = selectedCourse.value) {
  profileLoading.value = true
  profileError.value = ''
  try {
    selectedCourse.value = course
    const result = await getDynamicProfile(userProfile.value.userId, course)
    portrait.value = result.profile
  } catch (err) {
    portrait.value = null
    profileError.value = err instanceof Error ? err.message : '画像加载失败'
  } finally {
    profileLoading.value = false
  }
}

async function loadProfileOverview() {
  profileLoading.value = true
  profileError.value = ''
  try {
    const result = await listDynamicProfiles(userProfile.value.userId)
    subjectProfiles.value = result.profiles
    if (result.profiles[0]) {
      await loadPortrait(result.profiles[0].course)
    } else {
      await loadPortrait(selectedCourse.value)
    }
  } catch (err) {
    profileError.value = err instanceof Error ? err.message : '画像加载失败'
  } finally {
    profileLoading.value = false
  }
}

onMounted(loadProfileOverview)
</script>

<template>
  <div class="user-center-container">
    <section class="profile-hero">
      <div>
        <span>PERSONAL CENTER</span>
        <h1>{{ userProfile.name }}的学习空间</h1>
        <p>管理账号资料、查看学科画像，并快速回到最近的学习任务。</p>
      </div>
    </section>

    <div class="user-center-grid">
      <div class="profile-card">
        <div class="profile-header">
          <div>
            <span>ACCOUNT</span>
            <h2>个人资料</h2>
          </div>
        </div>

        <div class="profile-avatar-section">
          <div class="profile-avatar-large">
            <img v-if="userProfile.avatar" :src="userProfile.avatar" alt="用户头像" />
            <span v-else>{{ initials }}</span>
          </div>
          <button class="btn-secondary" type="button" @click="chooseAvatar">更换头像</button>
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
            <small>用户 ID 是当前账号的唯一标识，当前不可修改。</small>
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
          <button class="logout-button" type="button" @click="emit('logout')">退出当前账号</button>
        </div>

        <div v-if="userSuccess" class="message success">{{ userSuccess }}</div>
        <div v-if="userError" class="message error">{{ userError }}</div>
      </div>

      <section class="portrait-card">
        <header>
          <div>
            <span>LEARNING PORTRAIT</span>
            <h2>学科画像雷达图</h2>
          </div>
          <b>{{ portrait?.completion || activeSubject?.completion || 0 }}%</b>
        </header>

        <div class="subject-switcher">
          <button
            v-for="item in subjectProfiles"
            :key="item.course"
            type="button"
            :class="{ active: item.course === selectedCourse }"
            :disabled="profileLoading"
            @click="loadPortrait(item.course)"
          >
            {{ item.course }}
          </button>
          <button v-if="!subjectProfiles.length" type="button" class="active">{{ selectedCourse }}</button>
        </div>

        <div class="portrait-radar-wrap">
          <svg class="portrait-radar" viewBox="0 0 220 220" role="img" aria-label="学科画像雷达图">
            <polygon
              v-for="ring in radarRings"
              :key="ring"
              :points="ring"
              class="radar-ring"
            />
            <line
              v-for="axis in radarAxes"
              :key="axis.name"
              x1="110"
              y1="110"
              :x2="axis.lineX"
              :y2="axis.lineY"
              class="radar-axis"
            />
            <polygon :points="radarPoints" class="radar-area" />
            <polyline :points="radarPoints" class="radar-line" />
            <circle
              v-for="point in radarPoints.split(' ')"
              :key="point"
              :cx="point.split(',')[0]"
              :cy="point.split(',')[1]"
              r="3.2"
              class="radar-point"
            />
            <text
              v-for="axis in radarAxes"
              :key="`${axis.name}-label`"
              :x="axis.x"
              :y="axis.y"
              :text-anchor="axis.anchor"
              class="radar-label"
            >
              {{ axis.name }}
            </text>
          </svg>
        </div>

        <p class="portrait-summary">
          {{ portrait?.llm_context?.summary || activeSubject?.summary || '还没有形成完整画像。完成学习评估或多轮学习问答后，会在这里生成雷达图。' }}
        </p>

        <div class="metric-list">
          <article v-for="[name, value] in radarMetrics" :key="name">
            <span>{{ name }}</span>
            <b>{{ value }}</b>
            <i><em :style="{ width: `${value}%` }"></em></i>
          </article>
        </div>

        <p v-if="profileError" class="message error">{{ profileError }}</p>
      </section>
    </div>

    <section class="api-settings-card">
      <header>
        <div>
          <span>API SETTINGS</span>
          <h2>API 设置</h2>
        </div>
        <b>{{ apiConfig.model }}</b>
      </header>
      <p class="api-note">
        当前项目使用硅基流动兼容 OpenAI 的接口。这里保存的是当前浏览器配置，会被首页对话、个性化资源生成、课程练习和画像对话共用。
      </p>
      <div class="api-form">
        <label>
          <span>API Key</span>
          <div class="secret-input">
            <input v-model="apiConfig.api_key" :type="apiShowKey ? 'text' : 'password'" placeholder="sk-..." />
            <button type="button" @click="apiShowKey = !apiShowKey">{{ apiShowKey ? '隐藏' : '显示' }}</button>
          </div>
        </label>
        <label>
          <span>Base URL</span>
          <input v-model="apiConfig.base_url" type="url" placeholder="https://api.siliconflow.cn/v1" />
        </label>
        <label class="api-model-field">
          <span>模型</span>
          <input v-model="apiConfig.model" placeholder="deepseek-ai/DeepSeek-V4-Pro" />
        </label>
      </div>
      <div class="api-actions">
        <button class="btn-secondary" type="button" @click="saveApiSettings">保存 API 设置</button>
        <button class="btn-primary" type="button" :disabled="apiTesting" @click="testApiSettings">
          {{ apiTesting ? '正在测试...' : '测试连接' }}
        </button>
      </div>
      <p v-if="apiMessage" :class="['message', apiError ? 'error' : 'success']">{{ apiMessage }}</p>
    </section>

    <section class="account-dashboard-section">
      <div class="section-title">
        <span>OVERVIEW</span>
        <h2>学习概览</h2>
      </div>
      <HomePage @navigate="page => emit('navigate', page)" />
    </section>
  </div>
</template>

<style scoped>
.user-center-container {
  display: grid;
  gap: 22px;
  max-width: 1220px;
  margin: 0 auto;
  color: #241d35;
}

.profile-hero {
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

.profile-hero span,
.profile-header span,
.portrait-card header span,
.api-settings-card header span,
.section-title span {
  color: #8b75d7;
  font-size: 10px;
  font-weight: 850;
  letter-spacing: .14em;
}

.profile-hero h1 {
  margin: 7px 0 8px;
  color: #25144f;
  font-size: clamp(26px, 4vw, 38px);
  font-weight: 780;
}

.profile-hero p {
  margin: 0;
  color: #80758f;
  font-size: 14px;
}

.account-dashboard-section {
  width: 100%;
}

.user-center-grid {
  display: grid;
  grid-template-columns: minmax(320px, 430px) minmax(0, 1fr);
  gap: 22px;
  align-items: start;
}

.profile-card,
.portrait-card,
.api-settings-card {
  border: 1px solid #eee9ff;
  border-radius: 22px;
  background: #fff;
  box-shadow: 0 14px 38px rgba(93, 73, 170, .08);
}

.profile-card {
  overflow: hidden;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 22px 24px 10px;
}

.profile-header h2,
.portrait-card h2,
.api-settings-card h2,
.section-title h2 {
  margin: 5px 0 0;
  color: #25144f;
  font-size: 22px;
  font-weight: 760;
}

.profile-avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 24px 26px;
}

.profile-avatar-large {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 108px;
  height: 108px;
  margin-bottom: 16px;
  overflow: hidden;
  border-radius: 50%;
  color: #fff;
  background: linear-gradient(135deg, #6d5df2, #a855f7);
  font-size: 40px;
}

.profile-avatar-large img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-avatar-section small {
  margin-top: 9px;
  color: #756a84;
  font-size: 12px;
}

.profile-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  padding: 0 24px 22px;
}

.form-group:nth-child(1),
.form-group:nth-child(2) {
  grid-column: 1 / -1;
}

.form-group label,
.api-form label {
  display: block;
  margin-bottom: 8px;
  color: #5f526f;
  font-size: 13px;
  font-weight: 700;
}

.form-group input,
.api-form input {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  border: 1px solid #e7ddff;
  border-radius: 12px;
  color: #241d35;
  background: #fff;
  font-size: 14px;
}

.form-group input:focus,
.api-form input:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, .1);
}

.form-group input:disabled {
  background: #f9fafb;
  color: #9ca3af;
}

.form-group small {
  display: block;
  margin-top: 6px;
  color: #9ca3af;
  font-size: 12px;
}

.profile-actions,
.api-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.profile-actions {
  padding: 0 24px 24px;
}

.profile-actions button,
.api-actions button,
.profile-avatar-section button {
  padding: 10px 13px;
  border-radius: 11px;
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
  border: 1px solid #f5c2c7;
  color: #c82828;
  background: #fff;
}

.message {
  padding: 12px 16px;
  border-radius: 8px;
  margin: 0 20px 20px;
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

.portrait-card,
.api-settings-card {
  padding: 24px;
}

.portrait-card header,
.api-settings-card header,
.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.portrait-card header b,
.api-settings-card header b {
  max-width: min(420px, 52vw);
  padding: 8px 11px;
  overflow: hidden;
  border-radius: 999px;
  color: #5b35c8;
  background: #f0ebff;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.subject-switcher {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 20px 0 12px;
}

.subject-switcher button {
  padding: 7px 10px;
  border: 1px solid #e7ddff;
  border-radius: 999px;
  color: #6a5a7d;
  background: #fff;
  font-size: 12px;
}

.subject-switcher button.active {
  color: #fff;
  border-color: #7c5cff;
  background: #7c5cff;
}

.portrait-radar-wrap {
  display: grid;
  place-items: center;
  min-height: 280px;
  margin: 8px 0 14px;
  border-radius: 20px;
  background: linear-gradient(180deg, #fbfaff, #fff);
}

.portrait-radar {
  width: min(360px, 100%);
  height: auto;
  overflow: visible;
}

.radar-ring {
  fill: none;
  stroke: #e8defd;
  stroke-width: 1;
}

.radar-axis {
  stroke: #efe8ff;
  stroke-width: 1;
}

.radar-area {
  fill: rgba(124, 92, 255, .24);
  stroke: none;
}

.radar-line {
  fill: none;
  stroke: #7c5cff;
  stroke-width: 3;
  stroke-linejoin: round;
}

.radar-point {
  fill: #fff;
  stroke: #7c5cff;
  stroke-width: 2.4;
}

.radar-label {
  fill: #6d617e;
  font-size: 9px;
  font-weight: 700;
}

.portrait-summary {
  margin: 0;
  padding: 14px;
  border-left: 3px solid #8b5cf6;
  border-radius: 0 14px 14px 0;
  color: #63566f;
  background: #fbf9ff;
  font-size: 13px;
  line-height: 1.75;
}

.metric-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.metric-list article {
  padding: 12px;
  border: 1px solid #eee9ff;
  border-radius: 14px;
  background: #fff;
}

.metric-list span {
  color: #6a5a7d;
  font-size: 12px;
}

.metric-list b {
  float: right;
  color: #6d5df2;
  font-size: 13px;
}

.metric-list i {
  display: block;
  height: 5px;
  margin-top: 10px;
  overflow: hidden;
  border-radius: 99px;
  background: #eee9ff;
}

.metric-list em {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #6d5df2, #a855f7);
}

.api-note {
  margin: 14px 0 18px;
  color: #80758f;
  font-size: 13px;
  line-height: 1.7;
}

.api-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.api-model-field {
  grid-column: 1 / -1;
}

.secret-input {
  display: flex;
  gap: 8px;
}

.secret-input input {
  min-width: 0;
}

.secret-input button {
  flex: 0 0 auto;
  padding: 0 12px;
  border: 0;
  border-radius: 11px;
  color: #5b35c8;
  background: #f0ebff;
  font-weight: 750;
}

.api-actions {
  justify-content: flex-end;
  margin-top: 16px;
}

.api-actions .message,
.api-settings-card .message {
  margin: 14px 0 0;
}

.section-title {
  margin: 4px 0 14px;
}

@media (max-width: 900px) {
  .user-center-container {
    max-width: none;
  }

  .profile-hero,
  .user-center-grid,
  .api-form {
    grid-template-columns: 1fr;
  }

  .profile-hero,
  .api-settings-card header {
    align-items: flex-start;
    flex-direction: column;
  }

  .profile-form,
  .metric-list {
    grid-template-columns: 1fr;
  }
}
</style>
