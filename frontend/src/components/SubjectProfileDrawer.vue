<script setup lang="ts">
import type { DynamicProfile, SubjectProfileSummary } from '../types/profile'

defineProps<{
  profiles: SubjectProfileSummary[]
  profile: DynamicProfile | null
  currentCourse: string
  loading: boolean
}>()

const emit = defineEmits<{
  close: []
  select: [course: string]
}>()

function displayValue(value: string | string[] | undefined) {
  if (!value) return '等待对话补充'
  return Array.isArray(value) ? value.join('、') : value
}

function formatTime(value: string | null) {
  if (!value) return '尚未更新'
  return new Date(value).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="drawer-mask" @click.self="emit('close')">
    <aside class="profile-drawer">
      <header>
        <div>
          <span>SUBJECT PROFILES</span>
          <h2>各科画像</h2>
        </div>
        <button aria-label="关闭" @click="emit('close')">×</button>
      </header>

      <div class="drawer-content">
        <section class="subject-list-section">
          <p>每个学科独立构建和更新，切换学科不会覆盖其他画像。</p>
          <div v-if="profiles.length" class="subject-list">
            <button
              v-for="item in profiles"
              :key="item.course"
              :disabled="loading"
              :class="{ active: item.course === currentCourse }"
              @click="emit('select', item.course)"
            >
              <div><strong>{{ item.course }}</strong><b>{{ item.completion }}%</b></div>
              <span class="progress"><i :style="{ width: item.completion + '%' }"></i></span>
              <small>V{{ item.version }} · {{ formatTime(item.updated_at) }}</small>
            </button>
          </div>
          <div v-else class="empty">还没有已构建的学科画像</div>
        </section>

        <section class="current-profile">
          <div class="profile-title">
            <div><span>CURRENT PROFILE</span><h3>{{ currentCourse }}学习画像</h3></div>
            <b>{{ profile?.completion || 0 }}%</b>
          </div>

          <p class="summary">
            {{ profile?.llm_context?.summary || `尚未构建${currentCourse}画像，完成几轮访谈后会在这里形成摘要。` }}
          </p>

          <div class="metric-grid">
            <article v-for="(value, name) in profile?.radar_metrics || {}" :key="name">
              <div><span>{{ name }}</span><b>{{ value }}</b></div>
              <i><em :style="{ width: value + '%' }"></em></i>
            </article>
          </div>

          <div class="dimension-list">
            <article v-for="name in profile?.dimension_catalog || []" :key="name">
              <div>
                <strong>{{ name }}</strong>
                <span>{{ Math.round((profile?.dimensions[name]?.confidence || 0) * 100) }}%</span>
              </div>
              <p>{{ displayValue(profile?.dimensions[name]?.value) }}</p>
              <small>{{ profile?.dimensions[name]?.evidence || '继续访谈后补充证据' }}</small>
            </article>
          </div>
        </section>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.drawer-mask { position: fixed; inset: 0; z-index: 80; display: flex; justify-content: flex-end; background: rgba(22, 28, 40, .34); backdrop-filter: blur(2px); }
.profile-drawer { width: min(720px, 92vw); height: 100%; overflow: hidden; background: #f7f8fb; box-shadow: -20px 0 60px rgba(24, 31, 48, .18); animation: slide-in .22s ease-out; }
header { display: flex; align-items: center; justify-content: space-between; padding: 20px 22px; border-bottom: 1px solid #e3e6ec; background: #fff; }
header span, .profile-title span { color: #818ba0; font-size: 10px; font-weight: 800; letter-spacing: .13em; }
h2, h3, p { margin: 0; }
header h2 { margin-top: 4px; font-size: 21px; }
header button { width: 36px; height: 36px; border: 0; border-radius: 50%; color: #5f6673; background: #f0f1f4; font-size: 24px; }
.drawer-content { display: grid; grid-template-columns: 220px minmax(0, 1fr); height: calc(100% - 78px); overflow: hidden; }
.subject-list-section { padding: 17px; overflow-y: auto; border-right: 1px solid #e4e7ed; background: #fff; }
.subject-list-section > p { margin-bottom: 14px; color: #8992a2; font-size: 11px; line-height: 1.6; }
.subject-list { display: grid; gap: 8px; }
.subject-list button { padding: 11px; border: 1px solid #e8eaf0; border-radius: 11px; color: #343d4e; text-align: left; background: #fafbfc; }
.subject-list button.active { border-color: #8176e8; background: #efedff; }
.subject-list button > div, .profile-title, .metric-grid article div, .dimension-list article > div { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.subject-list button b { color: #5c51cd; font-size: 11px; }
.subject-list small { color: #9199a8; font-size: 10px; }
.progress { display: block; height: 4px; margin: 8px 0; overflow: hidden; border-radius: 99px; background: #e5e8ef; }
.progress i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #6559d5, #50bda2); }
.empty { padding: 25px 8px; border: 1px dashed #d9dde6; border-radius: 10px; color: #939baa; text-align: center; font-size: 12px; }
.current-profile { padding: 22px; overflow-y: auto; }
.profile-title h3 { margin-top: 4px; font-size: 19px; }
.profile-title > b { padding: 7px 10px; border-radius: 999px; color: #5146cf; background: #eae7ff; font-size: 12px; }
.summary { margin: 18px 0; padding: 14px; border-left: 3px solid #6c60db; border-radius: 0 11px 11px 0; color: #505b70; background: #fff; font-size: 13px; line-height: 1.7; }
.metric-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }
.metric-grid article { padding: 11px; border: 1px solid #e6e8ee; border-radius: 11px; background: #fff; }
.metric-grid article span { color: #626c7d; font-size: 11px; }
.metric-grid article b { color: #574cc5; font-size: 12px; }
.metric-grid article > i { display: block; height: 4px; margin-top: 8px; overflow: hidden; border-radius: 99px; background: #e8eaf0; }
.metric-grid em { display: block; height: 100%; border-radius: inherit; background: #6d62db; }
.dimension-list { display: grid; gap: 9px; margin-top: 16px; }
.dimension-list article { padding: 13px; border: 1px solid #e6e8ee; border-radius: 12px; background: #fff; }
.dimension-list strong { color: #394254; font-size: 12px; }
.dimension-list article > div span { color: #6559d4; font-size: 11px; font-weight: 700; }
.dimension-list p { margin: 8px 0 4px; color: #505a6e; font-size: 12px; line-height: 1.55; }
.dimension-list small { color: #929aa9; font-size: 10px; line-height: 1.45; }
button { cursor: pointer; }
button:disabled { cursor: default; opacity: .6; }
@keyframes slide-in { from { transform: translateX(32px); opacity: .5; } }
@media (max-width: 650px) {
  .profile-drawer { width: 100vw; }
  .drawer-content { grid-template-columns: 1fr; overflow-y: auto; }
  .subject-list-section, .current-profile { overflow: visible; }
  .subject-list-section { border-right: 0; border-bottom: 1px solid #e4e7ed; }
  .subject-list { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
