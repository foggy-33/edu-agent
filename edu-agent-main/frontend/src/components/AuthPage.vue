<script setup lang="ts">
import { computed, ref } from 'vue'
import { login, register, type AuthUser } from '../api/auth'

const emit = defineEmits<{ authenticated: [user: AuthUser] }>()

const mode = ref<'login' | 'register'>('login')
const username = ref('')
const displayName = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

const title = computed(() => mode.value === 'login' ? '欢迎回来' : '创建学习账号')
const subtitle = computed(() => mode.value === 'login' ? '登录后继续你的个性化学习旅程' : '建立账号，保存你的学习画像与进度')

function switchMode(next: 'login' | 'register') {
  mode.value = next
  error.value = ''
}

async function submit() {
  error.value = ''
  if (mode.value === 'register' && password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  loading.value = true
  try {
    const user = mode.value === 'login'
      ? await login(username.value, password.value)
      : await register(username.value, displayName.value, password.value)
    localStorage.setItem('justLoggedIn', 'true')
    emit('authenticated', user)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '操作失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-story">
      <div class="auth-brand"><span class="brand-mark">AI</span><b>智学空间</b></div>
      <div class="auth-story-content">
        <span class="auth-kicker">智能学习工作台</span>
        <h1>让每一次学习<br />都更懂你。</h1>
        <p>多智能体协作分析学习状态，生成个性化资源，并持续构建你的动态学习画像。</p>
        <div class="auth-features">
          <span>动态学生画像</span><span>个性化资源生成</span><span>学习效果评估</span>
        </div>
      </div>
      <small>智学空间 · 个性化智能学习工作台</small>
    </section>

    <section class="auth-panel">
      <form class="auth-card" @submit.prevent="submit">
        <div class="auth-mobile-brand"><span class="brand-mark">AI</span><b>智学空间</b></div>
        <div>
          <span class="section-kicker">{{ mode === 'login' ? '账号登录' : '免费注册' }}</span>
          <h2>{{ title }}</h2>
          <p>{{ subtitle }}</p>
        </div>

        <label v-if="mode === 'register'"><span>显示名称</span><input v-model.trim="displayName" maxlength="30" required placeholder="例如：小明" /></label>
        <label><span>用户名</span><input v-model.trim="username" minlength="3" maxlength="24" pattern="[a-zA-Z0-9_]+" required autocomplete="username" placeholder="字母、数字或下划线" /></label>
        <label><span>密码</span><div class="auth-password"><input v-model="password" :type="showPassword ? 'text' : 'password'" minlength="8" required :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" placeholder="至少 8 位密码" /><button type="button" @click="showPassword = !showPassword">{{ showPassword ? '隐藏' : '显示' }}</button></div></label>
        <label v-if="mode === 'register'"><span>确认密码</span><input v-model="confirmPassword" type="password" minlength="8" required autocomplete="new-password" placeholder="再次输入密码" /></label>

        <div v-if="error" class="auth-error">{{ error }}</div>
        <button class="auth-submit" :disabled="loading">{{ loading ? '正在处理...' : mode === 'login' ? '登录工作台' : '创建账号' }}</button>
        <p class="auth-switch">
          {{ mode === 'login' ? '还没有账号？' : '已有账号？' }}
          <button type="button" @click="switchMode(mode === 'login' ? 'register' : 'login')">{{ mode === 'login' ? '立即注册' : '返回登录' }}</button>
        </p>
      </form>
    </section>
  </main>
</template>
