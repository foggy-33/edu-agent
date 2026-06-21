<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { deleteResource, listResources, resourceDownloadUrl, uploadResource } from '../api/client'
import { loadUserProfile } from '../api/userProfile'
import type { UploadedResource } from '../types'

const emit = defineEmits<{
  navigate: [page: 'collaborative']
}>()

const userProfile = ref(loadUserProfile())
const fileInput = ref<HTMLInputElement | null>(null)
const resources = ref<UploadedResource[]>([])
const searchQuery = ref('')
const loading = ref(false)
const uploading = ref(false)
const error = ref('')

const filteredResources = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  return keyword
    ? resources.value.filter(item => item.name.toLowerCase().includes(keyword))
    : resources.value
})

function formatSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(value: string) {
  return new Date(value).toLocaleString('zh-CN')
}

async function loadResources() {
  loading.value = true
  error.value = ''
  try {
    resources.value = (await listResources(userProfile.value.userId)).resources
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '资源加载失败'
  } finally {
    loading.value = false
  }
}

function choosePdf() {
  fileInput.value?.click()
}

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
    error.value = '请选择 PDF 文件'
    return
  }

  uploading.value = true
  error.value = ''
  try {
    const result = await uploadResource(userProfile.value.userId, file)
    resources.value = [result.resource, ...resources.value]
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'PDF 上传失败'
  } finally {
    uploading.value = false
  }
}

async function removeResource(item: UploadedResource) {
  if (!window.confirm(`确定删除“${item.name}”吗？`)) return
  try {
    await deleteResource(userProfile.value.userId, item.id)
    resources.value = resources.value.filter(resource => resource.id !== item.id)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '删除失败'
  }
}

onMounted(loadResources)
</script>

<template>
  <div class="resource-library">
    <div class="library-header">
      <div>
        <span class="section-kicker">PDF KNOWLEDGE</span>
        <h1>资源库</h1>
        <p>上传 PDF 后，AI 可基于文件原文生成课程讲解、思维导图和练习题。</p>
      </div>
      <div class="header-actions">
        <button class="generate-btn" @click="emit('navigate', 'collaborative')">
          <span>✦</span><span>基于资料生成</span>
        </button>
        <button class="upload-btn" :disabled="uploading" @click="choosePdf">
          <span>＋</span><span>{{ uploading ? '解析中...' : '上传 PDF' }}</span>
        </button>
        <input ref="fileInput" type="file" accept=".pdf,application/pdf" hidden @change="handleUpload" />
      </div>
    </div>

    <div class="library-toolbar">
      <div class="search-bar">
        <span>⌕</span>
        <input v-model="searchQuery" type="text" placeholder="搜索已上传的 PDF" />
      </div>
      <span>{{ resources.length }} 个文件</span>
    </div>

    <div v-if="error" class="library-error">{{ error }}</div>
    <div v-if="loading" class="library-state">正在加载资源……</div>

    <div v-else-if="filteredResources.length" class="resources-grid">
      <article v-for="resource in filteredResources" :key="resource.id" class="resource-card">
        <div class="pdf-icon">PDF</div>
        <div class="resource-info">
          <h3>{{ resource.name }}</h3>
          <p>{{ resource.page_count }} 页 · {{ formatSize(resource.size) }} · 已提取 {{ resource.text_length }} 字</p>
          <small>{{ formatDate(resource.created_at) }}</small>
        </div>
        <span class="ready-status">可供 AI 使用</span>
        <div class="resource-actions">
          <a :href="resourceDownloadUrl(userProfile.userId, resource.id)" target="_blank" title="查看或下载">↓</a>
          <button title="删除" @click="removeResource(resource)">×</button>
        </div>
      </article>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">PDF</div>
      <h2>{{ searchQuery ? '没有匹配的文件' : '上传第一份 PDF' }}</h2>
      <p>{{ searchQuery ? '尝试更换搜索词。' : '系统会提取文件文字，之后可在资源生成页面引用。' }}</p>
      <button v-if="!searchQuery" :disabled="uploading" @click="choosePdf">选择 PDF 文件</button>
    </div>
  </div>
</template>

<style scoped>
.resource-library { display: grid; gap: 22px; }
.library-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; }
.library-header h1 { margin: 5px 0 7px; color: #202938; font-size: 28px; }
.library-header p { margin: 0; color: #7c8494; font-size: 13px; }
.header-actions { display: flex; gap: 10px; }
.header-actions button { display: flex; align-items: center; gap: 7px; padding: 10px 14px; border-radius: 11px; font-weight: 700; }
.generate-btn { border: 1px solid #d9d4ff; color: #5146cf; background: #f2f0ff; }
.upload-btn { border: 0; color: #fff; background: #5146cf; }
.library-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.library-toolbar > span { color: #8b93a1; font-size: 12px; }
.search-bar { display: flex; align-items: center; width: min(430px, 100%); padding: 0 13px; border: 1px solid #e0e3e9; border-radius: 12px; background: #fff; }
.search-bar span { color: #8c94a2; font-size: 20px; }
.search-bar input { width: 100%; padding: 11px 9px; border: 0; outline: 0; background: transparent; }
.resources-grid { display: grid; gap: 11px; }
.resource-card { display: grid; grid-template-columns: auto minmax(0, 1fr) auto auto; align-items: center; gap: 15px; padding: 16px; border: 1px solid #e5e8ee; border-radius: 15px; background: #fff; box-shadow: 0 7px 20px rgba(31, 42, 68, .04); }
.pdf-icon, .empty-icon { display: grid; place-items: center; width: 48px; height: 56px; border-radius: 9px; color: #c43d3d; background: #fff0f0; font-size: 11px; font-weight: 850; }
.resource-info h3 { margin: 0 0 5px; overflow: hidden; color: #30394a; font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.resource-info p { margin: 0 0 4px; color: #737d8e; font-size: 11px; }
.resource-info small { color: #9aa1ad; font-size: 10px; }
.ready-status { padding: 6px 9px; border-radius: 999px; color: #16734d; background: #e9f8f1; font-size: 10px; font-weight: 700; }
.resource-actions { display: flex; gap: 6px; }
.resource-actions a, .resource-actions button { display: grid; place-items: center; width: 34px; height: 34px; border: 0; border-radius: 9px; color: #5f6878; background: #f2f3f6; text-decoration: none; font-size: 18px; }
.library-state, .library-error { padding: 12px 14px; border-radius: 11px; font-size: 12px; }
.library-state { color: #697386; background: #f2f3f6; }
.library-error { color: #a23737; background: #fff0f0; }
.empty-state { display: grid; justify-items: center; padding: 68px 20px; border: 1px dashed #d9dde5; border-radius: 18px; text-align: center; background: #fff; }
.empty-state h2 { margin: 18px 0 7px; color: #30394a; font-size: 18px; }
.empty-state p { margin: 0 0 18px; color: #89919f; font-size: 12px; }
.empty-state button { padding: 10px 14px; border: 0; border-radius: 10px; color: #fff; background: #5146cf; font-weight: 700; }
button { cursor: pointer; }
button:disabled { cursor: wait; opacity: .6; }
@media (max-width: 720px) {
  .library-header { flex-direction: column; }
  .header-actions, .library-toolbar { width: 100%; }
  .library-toolbar { align-items: stretch; flex-direction: column; }
  .resource-card { grid-template-columns: auto minmax(0, 1fr) auto; }
  .ready-status { display: none; }
}
</style>
