<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getRegisteredUsers, type AdminUser, type AdminUserListResponse } from '../api/auth'

const data = ref<AdminUserListResponse>({ total: 0, onboarding_completed: 0, active_users: 0, users: [] })
const loading = ref(true)
const error = ref('')
const search = ref('')

const filteredUsers = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  if (!keyword) return data.value.users
  return data.value.users.filter(user => [
    user.username,
    user.display_name,
    user.email,
    user.phone,
    user.school,
    user.major,
  ].some(value => String(value || '').toLowerCase().includes(keyword)))
})

function initial(user: AdminUser) {
  return (user.display_name || user.username).trim().slice(0, 1).toUpperCase()
}

function formatDate(value: string | null | undefined) {
  if (!value) return '暂无记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  }).format(date)
}

async function loadUsers() {
  loading.value = true
  error.value = ''
  try {
    data.value = await getRegisteredUsers()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '用户列表加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadUsers)
</script>

<template>
  <div class="admin-page">
    <header class="admin-header">
      <div>
        <span class="eyebrow">ADMIN CONSOLE</span>
        <h1>用户管理</h1>
        <p>查看系统中已注册的用户及账号使用情况，不展示密码或登录令牌。</p>
      </div>
      <button type="button" :disabled="loading" @click="loadUsers">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"></path></svg>
        {{ loading ? '正在刷新' : '刷新数据' }}
      </button>
    </header>

    <section class="admin-stats" aria-label="用户统计">
      <article>
        <span>注册用户</span>
        <strong>{{ data.total }}</strong>
        <small>系统内全部账号</small>
      </article>
      <article>
        <span>完成初始化</span>
        <strong>{{ data.onboarding_completed }}</strong>
        <small>已完成初始学习信息</small>
      </article>
      <article>
        <span>有有效会话</span>
        <strong>{{ data.active_users }}</strong>
        <small>当前保留登录会话的用户</small>
      </article>
    </section>

    <section class="user-panel">
      <div class="panel-head">
        <div>
          <h2>注册用户</h2>
          <p>共 {{ data.total }} 人，当前显示 {{ filteredUsers.length }} 人</p>
        </div>
        <label class="admin-search">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="m20 20-4-4"></path></svg>
          <input v-model="search" type="search" placeholder="搜索姓名、账号、学校或专业" />
        </label>
      </div>

      <div v-if="error" class="admin-error">
        <span>{{ error }}</span>
        <button type="button" @click="loadUsers">重新加载</button>
      </div>

      <div v-else-if="loading" class="admin-loading">
        <i></i><span>正在读取用户数据...</span>
      </div>

      <div v-else-if="!filteredUsers.length" class="admin-empty">
        <span>⌕</span>
        <strong>没有找到用户</strong>
        <p>请更换关键词后重试。</p>
      </div>

      <div v-else class="user-table-wrap">
        <table>
          <thead>
            <tr>
              <th>用户</th>
              <th>联系方式</th>
              <th>学校与专业</th>
              <th>初始化</th>
              <th>注册时间</th>
              <th>最近登录</th>
              <th>会话</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.username">
              <td>
                <div class="user-identity">
                  <span class="table-avatar">
                    <img v-if="user.avatar" :src="user.avatar" alt="" />
                    <b v-else>{{ initial(user) }}</b>
                  </span>
                  <span>
                    <strong>{{ user.display_name }}</strong>
                    <small>@{{ user.username }}</small>
                  </span>
                  <em v-if="user.role === 'admin'">管理员</em>
                </div>
              </td>
              <td>
                <div class="cell-stack"><span>{{ user.phone || '未填写手机号' }}</span><small>{{ user.email || '未填写邮箱' }}</small></div>
              </td>
              <td>
                <div class="cell-stack"><span>{{ user.school || '未填写学校' }}</span><small>{{ user.major || '未填写专业' }}</small></div>
              </td>
              <td><span :class="['status-pill', user.onboarding_completed ? 'complete' : 'pending']">{{ user.onboarding_completed ? '已完成' : '未完成' }}</span></td>
              <td>{{ formatDate(user.created_at) }}</td>
              <td>{{ formatDate(user.last_login_at) }}</td>
              <td><span class="session-count">{{ user.active_sessions }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.admin-page { width: min(1320px, 100%); margin: 0 auto; color: #202123; }
.admin-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 28px; margin-bottom: 24px; }
.eyebrow { color: #6d5ce7; font-size: 10px; font-weight: 850; letter-spacing: .14em; }
.admin-header h1 { margin: 6px 0 5px; font-size: clamp(28px, 3vw, 38px); letter-spacing: -.04em; }
.admin-header p { margin: 0; color: #777d89; font-size: 13px; }
.admin-header button { display: inline-flex; align-items: center; gap: 8px; min-height: 40px; padding: 0 15px; border: 1px solid #dedede; border-radius: 999px; color: #333; background: #fff; font-weight: 700; cursor: pointer; }
.admin-header button:hover:not(:disabled) { border-color: #bdb5f5; color: #5542c7; background: #faf9ff; }
.admin-header button:disabled { opacity: .55; cursor: wait; }
.admin-header svg, .admin-search svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.admin-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-bottom: 18px; }
.admin-stats article { display: grid; gap: 5px; min-height: 132px; padding: 20px; border: 1px solid #e7e7ec; border-radius: 18px; background: rgba(255,255,255,.94); box-shadow: 0 12px 30px rgba(36, 32, 80, .045); }
.admin-stats span { color: #777d89; font-size: 12px; }
.admin-stats strong { font-size: 32px; letter-spacing: -.04em; }
.admin-stats small { align-self: end; color: #a0a4ad; font-size: 11px; }
.user-panel { overflow: hidden; border: 1px solid #e5e5ea; border-radius: 20px; background: rgba(255,255,255,.96); box-shadow: 0 18px 44px rgba(33, 29, 76, .055); }
.panel-head { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 19px 20px; border-bottom: 1px solid #ededf1; }
.panel-head h2 { margin: 0; font-size: 17px; }
.panel-head p { margin: 4px 0 0; color: #9599a3; font-size: 11px; }
.admin-search { display: flex; align-items: center; gap: 8px; width: min(340px, 42vw); height: 40px; padding: 0 12px; border: 1px solid #dedee4; border-radius: 999px; color: #8e929c; background: #fafafa; }
.admin-search:focus-within { border-color: #9d91ec; box-shadow: 0 0 0 3px rgba(109,92,231,.09); background: #fff; }
.admin-search input { min-width: 0; width: 100%; border: 0; outline: 0; color: #303038; background: transparent; font-size: 12px; }
.user-table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 1080px; }
th { padding: 12px 14px; color: #9397a1; background: #fafafd; text-align: left; font-size: 10px; font-weight: 750; white-space: nowrap; }
td { padding: 14px; border-top: 1px solid #f0f0f3; color: #555b67; font-size: 11px; vertical-align: middle; }
tbody tr { transition: background .16s ease; }
tbody tr:hover { background: #faf9ff; }
.user-identity { display: flex; align-items: center; gap: 10px; min-width: 210px; }
.table-avatar { display: grid; place-items: center; width: 36px; height: 36px; flex: 0 0 auto; overflow: hidden; border-radius: 50%; color: #fff; background: #6d5ce7; }
.table-avatar img { width: 100%; height: 100%; object-fit: cover; }
.table-avatar b { font-size: 12px; }
.user-identity > span:nth-child(2), .cell-stack { display: grid; gap: 3px; }
.user-identity strong { color: #202123; font-size: 12px; }
.user-identity small, .cell-stack small { color: #9a9ea8; font-size: 10px; }
.user-identity em { padding: 3px 6px; border-radius: 999px; color: #5b45c6; background: #efedff; font-size: 9px; font-style: normal; font-weight: 750; }
.cell-stack span { color: #4f5560; }
.status-pill { display: inline-flex; padding: 5px 8px; border-radius: 999px; font-size: 10px; font-weight: 700; white-space: nowrap; }
.status-pill.complete { color: #24714a; background: #eaf8f0; }
.status-pill.pending { color: #866510; background: #fff6d9; }
.session-count { display: grid; place-items: center; width: 26px; height: 26px; border-radius: 50%; color: #5c49c7; background: #efedff; font-weight: 800; }
.admin-loading, .admin-empty, .admin-error { min-height: 260px; display: grid; place-items: center; align-content: center; gap: 10px; padding: 28px; color: #858a95; text-align: center; }
.admin-loading i { width: 24px; height: 24px; border: 2px solid #ddd8ff; border-top-color: #6d5ce7; border-radius: 50%; animation: spin .8s linear infinite; }
.admin-empty span { font-size: 32px; }
.admin-empty strong { color: #333; }
.admin-empty p { margin: 0; font-size: 11px; }
.admin-error { color: #a33e3e; background: #fffafa; }
.admin-error button { padding: 8px 12px; border: 0; border-radius: 999px; color: #fff; background: #202123; cursor: pointer; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 760px) {
  .admin-header { align-items: flex-start; flex-direction: column; }
  .admin-stats { grid-template-columns: 1fr; }
  .admin-stats article { min-height: 108px; }
  .panel-head { align-items: stretch; flex-direction: column; }
  .admin-search { width: 100%; }
}
</style>
