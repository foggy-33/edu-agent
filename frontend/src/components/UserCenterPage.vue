<script setup lang="ts">
import { computed, ref } from 'vue'
import { defaultUserProfile, loadUserProfile, saveUserProfile } from '../api/userProfile'

const profile = ref(loadUserProfile())
const message = ref('')
const error = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const initials = computed(() => profile.value.name.trim().slice(0, 1).toUpperCase() || 'U')

function chooseAvatar() {
  fileInput.value?.click()
}

function handleAvatar(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    error.value = '请选择图片文件'
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    error.value = '头像图片不能超过 2 MB'
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    profile.value.avatar = String(reader.result || '')
    error.value = ''
  }
  reader.readAsDataURL(file)
}

function save() {
  if (!profile.value.name.trim()) {
    error.value = '名称不能为空'
    return
  }
  profile.value.name = profile.value.name.trim()
  saveUserProfile(profile.value)
  error.value = ''
  message.value = '个人资料已保存，并同步到侧边栏'
}

function reset() {
  profile.value = { ...defaultUserProfile }
  saveUserProfile(profile.value)
  error.value = ''
  message.value = '已恢复默认资料'
}
</script>

<template>
  <div class="user-center-layout">
    <section class="surface user-profile-hero">
      <div class="user-avatar-large">
        <img v-if="profile.avatar" :src="profile.avatar" alt="用户头像" />
        <span v-else>{{ initials }}</span>
      </div>
      <h2>{{ profile.name }}</h2>
      <p>{{ profile.userId }}</p>
      <button class="btn-secondary" @click="chooseAvatar">更换头像</button>
      <input ref="fileInput" type="file" accept="image/*" hidden @change="handleAvatar" />
      <small>支持 JPG、PNG、WebP，文件不超过 2 MB</small>
    </section>

    <section class="surface user-profile-form">
      <span class="section-kicker">个人中心</span>
      <h2>编辑个人资料</h2>
      <p>修改后的名称和头像会立即显示在左侧个人资料入口。</p>
      <label><span>显示名称</span><input v-model="profile.name" maxlength="30" placeholder="请输入显示名称" /></label>
      <label><span>用户 ID</span><input :value="profile.userId" disabled /><small>用户 ID 用于关联动态学习画像，当前不可修改。</small></label>
      <div class="user-profile-actions"><button class="btn-secondary" @click="reset">恢复默认</button><button class="btn-primary" @click="save">保存资料</button></div>
      <div v-if="message" class="settings-message">{{ message }}</div>
      <div v-if="error" class="settings-message settings-message-error">{{ error }}</div>
    </section>
  </div>
</template>
