<script setup lang="ts">
import { computed, ref } from 'vue'
import { defaultUserProfile, loadUserProfile, saveUserProfile } from '../api/userProfile'

const emit = defineEmits<{
  logout: []
}>()

const userProfile = ref(loadUserProfile())
const fileInput = ref<HTMLInputElement | null>(null)
const userError = ref('')
const userSuccess = ref('')
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
  userSuccess.value = '个人资料已保存，并同步到侧边栏'
}

function reset() {
  userProfile.value = { ...defaultUserProfile }
  saveUserProfile(userProfile.value)
  userError.value = ''
  userSuccess.value = '已恢复默认资料'
}

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
          <button class="btn-secondary" @click="reset">恢复默认</button>
          <button class="btn-primary" @click="saveProfile">保存资料</button>
          <button class="logout-button" @click="emit('logout')">退出当前账号</button>
        </div>

        <div v-if="userSuccess" class="message success">{{ userSuccess }}</div>
        <div v-if="userError" class="message error">{{ userError }}</div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.user-center-container {
  display: block !important;
  max-width: 760px;
  margin: 0 auto;
}

.profile-section {
  display: flex !important;
  flex-direction: column !important;
}

.profile-card {
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

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.profile-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
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

@media (max-width: 900px) {
  .user-center-container {
    max-width: none;
  }
}
</style>
