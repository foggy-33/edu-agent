<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getDynamicProfile, listDynamicProfiles, testSiliconFlow, testSpark } from '../api/client'
import { loadSiliconFlowConfig, saveSiliconFlowConfig } from '../api/settings'
import { defaultUserProfile, loadUserProfile, saveUserProfile } from '../api/userProfile'
import { updateUserProfile } from '../api/auth'
import type { DynamicProfile, SubjectProfileSummary } from '../types/profile'

const emit = defineEmits<{
  logout: []
}>()

const userProfile = ref(loadUserProfile())
const fileInput = ref<HTMLInputElement | null>(null)
const userError = ref('')
const userSuccess = ref('')

const apiConfig = ref(loadSiliconFlowConfig())
const apiShowKey = ref(false)
const sparkShowPassword = ref(false)
const apiTesting = ref(false)
const apiMessage = ref('')
const apiError = ref(false)

const userSaving = ref(false)
const subjectProfiles = ref<SubjectProfileSummary[]>([])
const selectedPortraitCourse = ref('')
const portraitDetails = ref<DynamicProfile | null>(null)
const portraitLoading = ref(false)

const initials = computed(() => userProfile.value.name.trim().slice(0, 1).toUpperCase() || 'U')
const activeModelName = computed(() => apiConfig.value.active_provider === 'spark'
  ? `讯飞星火 · ${apiConfig.value.spark_model}`
  : `硅基流动 · ${apiConfig.value.model}`)

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
  if (file.size > 10 * 1024 * 1024) {
    userError.value = '头像图片不能超过 10 MB'
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    userProfile.value.avatar = String(reader.result || '')
    userError.value = ''
  }
  reader.readAsDataURL(file)
}

async function saveProfile() {
  if (!userProfile.value.name.trim()) {
    userError.value = '名称不能为空'
    return
  }
  userProfile.value.name = userProfile.value.name.trim()
  userSaving.value = true
  userError.value = ''
  userSuccess.value = ''
  try {
    const result = await updateUserProfile({
      display_name: userProfile.value.name,
      avatar: userProfile.value.avatar,
      phone: userProfile.value.phone,
      email: userProfile.value.email,
      school: userProfile.value.school,
      major: userProfile.value.major,
      grade_level: userProfile.value.gradeLevel,
      learning_goal: userProfile.value.learningGoal,
    })
    userProfile.value.userId = result.username
    userProfile.value.name = result.display_name
    userProfile.value.avatar = result.avatar
    userProfile.value.phone = result.phone
    userProfile.value.email = result.email
    userProfile.value.school = result.school
    userProfile.value.major = result.major
    userProfile.value.gradeLevel = result.grade_level
    if (result.learning_goal !== undefined && result.learning_goal !== null) {
      userProfile.value.learningGoal = result.learning_goal
    }
    saveUserProfile(userProfile.value)
    userSuccess.value = '个人资料已保存'
  } catch (err: any) {
    userError.value = err.message || '保存失败，请稍后重试'
  } finally {
    userSaving.value = false
  }
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
    spark_api_password: apiConfig.value.spark_api_password.trim(),
    spark_base_url: apiConfig.value.spark_base_url.trim() || 'https://spark-api-open.xf-yun.com/x2',
    spark_model: apiConfig.value.spark_model.trim() || 'spark-x',
  }
}

function saveApiSettings() {
  normalizeApiConfig()
  saveSiliconFlowConfig(apiConfig.value)
  apiError.value = false
  apiMessage.value = '设置已保存'
}

async function testApiSettings() {
  saveApiSettings()
  const isSpark = apiConfig.value.active_provider === 'spark'
  if (isSpark ? !apiConfig.value.spark_api_password.trim() : !apiConfig.value.api_key.trim()) {
    apiError.value = true
    apiMessage.value = isSpark ? '请先填写讯飞星火 API Password' : '请先填写硅基流动 API Key'
    return
  }
  apiTesting.value = true
  try {
    const result = isSpark ? await testSpark(apiConfig.value) : await testSiliconFlow(apiConfig.value)
    apiError.value = false
    apiMessage.value = `${result.model}：${result.message}`
  } catch (err) {
    apiError.value = true
    apiMessage.value = err instanceof Error ? err.message : '连接测试失败'
  } finally {
    apiTesting.value = false
  }
}

async function loadPortraitDetails(course?: string) {
  const targetCourse = course || selectedPortraitCourse.value
  if (!targetCourse) return
  portraitLoading.value = true
  try {
    selectedPortraitCourse.value = targetCourse
    const result = await getDynamicProfile(userProfile.value.userId, targetCourse)
    portraitDetails.value = result.profile
  } catch {
    portraitDetails.value = null
  } finally {
    portraitLoading.value = false
  }
}

onMounted(async () => {
  try {
    const result = await listDynamicProfiles(userProfile.value.userId)
    subjectProfiles.value = result.profiles
    const firstCourse = result.profiles[0]?.course
    if (firstCourse) await loadPortraitDetails(firstCourse)
  } catch {
    subjectProfiles.value = []
  }
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>个人中心</h1>
      <p>管理你的个人信息和系统设置</p>
    </div>

    <div class="content-grid">
      <section class="panel">
        <div class="panel-header">
          <h2>个人资料</h2>
        </div>

        <div class="profile-basic">
          <div class="avatar-wrap">
            <div class="avatar">
              <img v-if="userProfile.avatar" :src="userProfile.avatar" alt="用户头像" />
              <span v-else>{{ initials }}</span>
            </div>
            <button class="avatar-btn" type="button" @click="chooseAvatar">更换头像</button>
            <input ref="fileInput" type="file" accept="image/*" hidden @change="handleAvatar" />
            <div class="avatar-hint">支持 JPG、PNG、WebP，不超过 10 MB</div>
          </div>
          <div class="profile-info">
            <div class="info-name">{{ userProfile.name }}</div>
            <div class="info-id">账号：{{ userProfile.userId }}</div>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-item">
            <label>显示名称</label>
            <input v-model="userProfile.name" maxlength="30" placeholder="请输入显示名称" />
          </div>
          <div class="form-item">
            <label>手机号码</label>
            <input v-model="userProfile.phone" placeholder="请输入手机号码" />
          </div>
          <div class="form-item">
            <label>邮箱地址</label>
            <input v-model="userProfile.email" type="email" placeholder="请输入邮箱地址" />
          </div>
          <div class="form-item">
            <label>所在院校</label>
            <input v-model="userProfile.school" placeholder="请输入院校名称" />
          </div>
          <div class="form-item">
            <label>专业班级</label>
            <input v-model="userProfile.major" placeholder="请输入专业班级" />
          </div>
          <div class="form-item">
            <label>学习阶段</label>
            <select v-model="userProfile.gradeLevel">
              <option value="">请选择</option>
              <option value="大一">大一</option>
              <option value="大二">大二</option>
              <option value="大三">大三</option>
              <option value="大四">大四</option>
              <option value="研一">研一</option>
              <option value="研二">研二</option>
              <option value="研三">研三</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <div class="form-item">
            <label>学习目标</label>
            <select v-model="userProfile.learningGoal">
              <option value="">请选择</option>
              <option value="课程学习">跟上课程进度</option>
              <option value="考试复习">应对期末考试</option>
              <option value="考研准备">考研复习</option>
              <option value="竞赛准备">竞赛/项目</option>
              <option value="求职面试">求职面试</option>
              <option value="兴趣学习">兴趣驱动</option>
            </select>
          </div>
        </div>

        <div v-if="userProfile.learningStyle.length || userProfile.weakSubjects.length || userProfile.improvementAreas.length" class="tag-section">
          <div v-if="userProfile.learningStyle.length" class="tag-group">
            <div class="tag-label">偏好的学习方式</div>
            <div class="tag-list">
              <span v-for="style in userProfile.learningStyle" :key="style" class="tag">{{ style }}</span>
            </div>
          </div>
          <div v-if="userProfile.weakSubjects.length" class="tag-group">
            <div class="tag-label">有困难的科目</div>
            <div class="tag-list">
              <span v-for="subject in userProfile.weakSubjects" :key="subject" class="tag tag-warn">{{ subject }}</span>
            </div>
          </div>
          <div v-if="userProfile.improvementAreas.length" class="tag-group">
            <div class="tag-label">希望提升的方面</div>
            <div class="tag-list">
              <span v-for="area in userProfile.improvementAreas" :key="area" class="tag tag-info">{{ area }}</span>
            </div>
          </div>
        </div>

        <div class="panel-actions">
          <button class="btn-ghost" type="button" @click="reset" :disabled="userSaving">恢复默认</button>
          <button class="btn-primary" type="button" @click="saveProfile" :disabled="userSaving">
            <span v-if="userSaving">保存中...</span>
            <span v-else>保存资料</span>
          </button>
        </div>

        <div v-if="userSuccess" class="tip tip-success">{{ userSuccess }}</div>
        <div v-if="userError" class="tip tip-error">{{ userError }}</div>
      </section>

      <section class="panel">
        <div class="panel-header">
          <h2>模型设置</h2>
          <span class="model-badge">{{ activeModelName }}</span>
        </div>

        <p class="panel-desc">
          同时保存硅基流动和讯飞星火配置，可选择当前学习功能实际调用的模型。设置保存在当前浏览器中。
        </p>

        <div class="provider-switch" role="tablist" aria-label="模型服务商">
          <button
            type="button"
            :class="{ active: apiConfig.active_provider === 'siliconflow' }"
            @click="apiConfig.active_provider = 'siliconflow'; apiMessage = ''"
          >硅基流动</button>
          <button
            type="button"
            :class="{ active: apiConfig.active_provider === 'spark' }"
            @click="apiConfig.active_provider = 'spark'; apiMessage = ''"
          >讯飞星火</button>
        </div>

        <div v-if="apiConfig.active_provider === 'siliconflow'" class="form-stack">
          <div class="form-item">
            <label>API Key</label>
            <div class="input-with-btn">
              <input v-model="apiConfig.api_key" :type="apiShowKey ? 'text' : 'password'" placeholder="sk-..." />
              <button type="button" @click="apiShowKey = !apiShowKey">{{ apiShowKey ? '隐藏' : '显示' }}</button>
            </div>
          </div>
          <div class="form-item">
            <label>Base URL</label>
            <input v-model="apiConfig.base_url" type="url" placeholder="https://api.siliconflow.cn/v1" />
          </div>
          <div class="form-item">
            <label>模型名称</label>
            <input v-model="apiConfig.model" placeholder="deepseek-ai/DeepSeek-V4-Pro" />
          </div>
        </div>

        <div v-else class="form-stack">
          <div class="form-item">
            <label>API Password</label>
            <div class="input-with-btn">
              <input
                v-model="apiConfig.spark_api_password"
                :type="sparkShowPassword ? 'text' : 'password'"
                placeholder="控制台 HTTP 服务接口认证信息"
                autocomplete="off"
              />
              <button type="button" @click="sparkShowPassword = !sparkShowPassword">{{ sparkShowPassword ? '隐藏' : '显示' }}</button>
            </div>
          </div>
          <div class="form-item">
            <label>Base URL</label>
            <input v-model="apiConfig.spark_base_url" type="url" placeholder="https://spark-api-open.xf-yun.com/x2" />
          </div>
          <div class="form-item">
            <label>模型名称</label>
            <input v-model="apiConfig.spark_model" placeholder="spark-x" />
            <small class="field-hint">X2 使用 /x2，X1.5 使用 /v2；两者模型名均为 spark-x。</small>
          </div>
        </div>

        <div class="panel-actions">
          <button class="btn-ghost" type="button" @click="saveApiSettings">保存设置</button>
          <button class="btn-primary" type="button" :disabled="apiTesting" @click="testApiSettings">
            {{ apiTesting ? '测试中...' : '测试连接' }}
          </button>
        </div>

        <p v-if="apiMessage" :class="['tip', apiError ? 'tip-error' : 'tip-success']">{{ apiMessage }}</p>
      </section>
    </div>

    <section id="portrait-details" class="panel portrait-panel">
      <div class="panel-header portrait-panel-header">
        <div>
          <h2>学习画像</h2>
          <p>查看画像对话形成的六维分析与学习建议</p>
        </div>
        <select
          v-if="subjectProfiles.length"
          v-model="selectedPortraitCourse"
          :disabled="portraitLoading"
          @change="loadPortraitDetails()"
        >
          <option v-for="item in subjectProfiles" :key="item.course" :value="item.course">{{ item.course }}</option>
        </select>
      </div>

      <div v-if="portraitLoading" class="portrait-empty">正在加载画像...</div>
      <div v-else-if="portraitDetails" class="portrait-content">
        <p class="portrait-overview">{{ portraitDetails.llm_context.summary || '继续完成画像对话后，这里会生成学科画像总结。' }}</p>
        <div class="portrait-metrics">
          <article v-for="(value, name) in portraitDetails.radar_metrics" :key="name">
            <div><strong>{{ name }}</strong><span>{{ value }}</span></div>
            <i><em :style="{ width: `${value}%` }"></em></i>
            <p>{{ portraitDetails.radar_summaries[name] || '继续对话后补充该维度总结。' }}</p>
          </article>
        </div>
      </div>
      <div v-else class="portrait-empty">还没有画像记录，请先到“画像对话”完成一轮访谈。</div>
    </section>

    <section class="panel panel-security">
      <div class="panel-header">
        <h2>账号安全</h2>
      </div>
      <div class="security-content">
        <p>退出当前登录的账号</p>
        <button class="btn-danger" type="button" @click="emit('logout')">退出登录</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page-container {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  color: #1f2937;
}

.page-header h1 {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.model-badge {
  padding: 4px 10px;
  border-radius: 6px;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 12px;
  font-weight: 500;
}

.panel-desc {
  margin: 0 0 16px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
}

.profile-basic {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px;
  margin-bottom: 20px;
  background: #f9fafb;
  border-radius: 10px;
}

.avatar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #d1d5db;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 600;
  overflow: hidden;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-btn {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #374151;
  font-size: 12px;
  cursor: pointer;
}

.avatar-btn:hover {
  background: #f9fafb;
}

.avatar-hint {
  font-size: 11px;
  color: #9ca3af;
}

.profile-info {
  min-width: 0;
}

.info-name {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.info-id {
  margin-top: 4px;
  font-size: 13px;
  color: #6b7280;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.form-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.provider-switch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  margin-bottom: 16px;
  padding: 4px;
  border-radius: 10px;
  background: #f3f4f6;
}

.provider-switch button {
  min-height: 36px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.provider-switch button.active {
  background: #111827;
  color: #ffffff;
}

.field-hint {
  color: #9ca3af;
  font-size: 11px;
  line-height: 1.5;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.form-item input,
.form-item select {
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  color: #1f2937;
  background: #fff;
  outline: none;
  transition: border-color 0.15s;
}

.form-item input:focus,
.form-item select:focus {
  border-color: #6b7280;
  box-shadow: 0 0 0 3px rgba(107, 114, 128, 0.1);
}

.input-with-btn {
  display: flex;
  gap: 8px;
}

.input-with-btn input {
  flex: 1;
  min-width: 0;
}

.input-with-btn button {
  flex: none;
  padding: 0 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #f9fafb;
  color: #374151;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.input-with-btn button:hover {
  background: #f3f4f6;
}

.tag-section {
  margin-top: 20px;
  padding: 14px;
  background: #f9fafb;
  border-radius: 8px;
}

.tag-group {
  margin-bottom: 12px;
}

.tag-group:last-child {
  margin-bottom: 0;
}

.tag-label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 8px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  padding: 4px 10px;
  border-radius: 6px;
  background: #e5e7eb;
  color: #374151;
  font-size: 12px;
  font-weight: 500;
}

.tag.tag-warn {
  background: #fef3c7;
  color: #92400e;
}

.tag.tag-info {
  background: #dbeafe;
  color: #1e40af;
}

.panel-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn-primary,
.btn-ghost,
.btn-danger {
  padding: 9px 18px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.btn-primary {
  background: #111827;
  color: #fff;
  border-color: #111827;
}

.btn-primary:hover:not(:disabled) {
  background: #1f2937;
  border-color: #1f2937;
}

.btn-ghost {
  background: #fff;
  color: #374151;
  border-color: #d1d5db;
}

.btn-ghost:hover {
  background: #f9fafb;
}

.portrait-panel-header { align-items: flex-start; }
.portrait-panel-header p { margin: 5px 0 0; color: #8a8f98; font-size: 12px; }
.portrait-panel-header select { min-width: 150px; padding: 8px 11px; border: 1px solid #d1d5db; border-radius: 8px; color: #202123; background: #ffffff; outline: none; }
.portrait-overview { margin: 0 0 16px; padding: 14px 16px; border-radius: 10px; color: #4b5563; background: #f7f7f8; font-size: 13px; line-height: 1.7; }
.portrait-metrics { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.portrait-metrics article { padding: 14px; border: 1px solid #e5e7eb; border-radius: 12px; }
.portrait-metrics article > div { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.portrait-metrics strong { font-size: 13px; }
.portrait-metrics span { color: #6b7280; font-size: 12px; }
.portrait-metrics i { display: block; height: 4px; margin: 8px 0; overflow: hidden; border-radius: 999px; background: #e5e7eb; }
.portrait-metrics em { display: block; height: 100%; border-radius: inherit; background: #202123; }
.portrait-metrics p { margin: 0; color: #6b7280; font-size: 11px; line-height: 1.55; }
.portrait-empty { padding: 28px 12px; color: #8a8f98; text-align: center; font-size: 13px; }

.btn-danger {
  background: #fff;
  color: #dc2626;
  border-color: #fecaca;
}

.btn-danger:hover {
  background: #fef2f2;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tip {
  padding: 10px 14px;
  border-radius: 8px;
  margin-top: 14px;
  font-size: 13px;
}

.tip-success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.tip-error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.panel-security .security-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-security p {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .profile-basic {
    flex-direction: column;
    text-align: center;
  }

  .portrait-panel-header {
    flex-direction: column;
    gap: 12px;
  }

  .portrait-panel-header select {
    width: 100%;
  }

  .portrait-metrics {
    grid-template-columns: 1fr;
  }

  .panel-security .security-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
