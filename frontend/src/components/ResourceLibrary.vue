<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { deleteResource, listResources, resourceDownloadUrl, uploadResource } from '../api/client'
import { loadUserProfile } from '../api/userProfile'
import type { UploadedResource } from '../types'

const emit = defineEmits<{
  navigate: [page: 'collaborative']
}>()

const DEFAULT_FOLDER = '未分类'
const ALL_FOLDERS = '全部文件'

const userProfile = ref(loadUserProfile())
const fileInput = ref<HTMLInputElement | null>(null)
const resources = ref<UploadedResource[]>([])
const customFolders = ref<string[]>([])
const activeFolder = ref(DEFAULT_FOLDER)
const searchQuery = ref('')
const newFolderName = ref('')
const creatingFolder = ref(false)
const loading = ref(false)
const uploading = ref(false)
const error = ref('')

const folders = computed(() => {
  const names = new Set<string>([DEFAULT_FOLDER, ...customFolders.value])
  resources.value.forEach(item => names.add(folderName(item)))
  return Array.from(names)
})

const folderStats = computed(() =>
  folders.value.map(name => ({
    name,
    count: resources.value.filter(item => folderName(item) === name).length,
  }))
)

const visibleResources = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  return resources.value.filter(item => {
    const inFolder = activeFolder.value === ALL_FOLDERS || folderName(item) === activeFolder.value
    const matched = !keyword || item.name.toLowerCase().includes(keyword) || folderName(item).toLowerCase().includes(keyword)
    return inFolder && matched
  })
})

const activeFolderCount = computed(() =>
  activeFolder.value === ALL_FOLDERS
    ? resources.value.length
    : resources.value.filter(item => folderName(item) === activeFolder.value).length
)

const uploadTargetFolder = computed(() =>
  activeFolder.value === ALL_FOLDERS ? DEFAULT_FOLDER : activeFolder.value
)

function folderName(item: UploadedResource) {
  return item.course_folder || DEFAULT_FOLDER
}

function folderStorageKey() {
  return `edu-resource-folders:${userProfile.value.userId}`
}

function loadCustomFolders() {
  try {
    const raw = localStorage.getItem(folderStorageKey())
    const parsed = raw ? JSON.parse(raw) : []
    customFolders.value = Array.isArray(parsed)
      ? parsed.filter(item => typeof item === 'string' && item.trim())
      : []
  } catch {
    customFolders.value = []
  }
}

function saveCustomFolders(next: string[]) {
  customFolders.value = next
  localStorage.setItem(folderStorageKey(), JSON.stringify(next))
}

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

function createFolder() {
  const name = newFolderName.value.trim()
  if (!name) {
    creatingFolder.value = true
    return
  }
  if (!folders.value.includes(name)) {
    saveCustomFolders([...customFolders.value, name])
  }
  activeFolder.value = name
  newFolderName.value = ''
  creatingFolder.value = false
}

function chooseFolder(name: string) {
  activeFolder.value = name
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
    const result = await uploadResource(userProfile.value.userId, file, uploadTargetFolder.value)
    resources.value = [result.resource, ...resources.value]
    activeFolder.value = result.resource.course_folder || uploadTargetFolder.value
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

onMounted(() => {
  loadCustomFolders()
  loadResources()
})
</script>

<template>
  <div class="resource-library">
    <header class="library-header">
      <div>
        <span class="section-kicker">FILE LIBRARY</span>
        <h1>文件库</h1>
        <p>按课程建立文件夹，上传 PDF 后可用于问答、思维导图和练习题生成。</p>
      </div>
      <button class="generate-btn" @click="emit('navigate', 'collaborative')">
        基于资料生成
      </button>
    </header>

    <div class="library-shell">
      <aside class="folder-panel" aria-label="课程文件夹">
        <div class="folder-panel-head">
          <strong>课程文件夹</strong>
          <button title="新建课程文件夹" @click="creatingFolder = !creatingFolder">+</button>
        </div>

        <form v-if="creatingFolder" class="folder-form" @submit.prevent="createFolder">
          <input v-model="newFolderName" type="text" placeholder="例如：数据库系统" autofocus />
          <button type="submit">创建</button>
        </form>

        <button
          class="folder-item"
          :class="{ active: activeFolder === ALL_FOLDERS }"
          @click="chooseFolder(ALL_FOLDERS)"
        >
          <span>全部文件</span>
          <small>{{ resources.length }}</small>
        </button>

        <button
          v-for="folder in folderStats"
          :key="folder.name"
          class="folder-item"
          :class="{ active: activeFolder === folder.name }"
          @click="chooseFolder(folder.name)"
        >
          <span>{{ folder.name }}</span>
          <small>{{ folder.count }}</small>
        </button>
      </aside>

      <section class="file-panel">
        <div class="library-toolbar">
          <div>
            <h2>{{ activeFolder }}</h2>
            <p>{{ activeFolderCount }} 个文件，上传目标：{{ uploadTargetFolder }}</p>
          </div>
          <div class="toolbar-actions">
            <label class="search-bar">
              <span>⌕</span>
              <input v-model="searchQuery" type="text" placeholder="搜索文件或课程" />
            </label>
            <button class="upload-btn" :disabled="uploading" @click="choosePdf">
              {{ uploading ? '解析中...' : '上传 PDF' }}
            </button>
            <input ref="fileInput" type="file" accept=".pdf,application/pdf" hidden @change="handleUpload" />
          </div>
        </div>

        <div v-if="error" class="library-error">{{ error }}</div>
        <div v-if="loading" class="library-state">正在加载资源...</div>

        <div v-else-if="visibleResources.length" class="resources-grid">
          <article v-for="resource in visibleResources" :key="resource.id" class="resource-card">
            <div class="pdf-icon">PDF</div>
            <div class="resource-info">
              <div class="resource-title-row">
                <h3>{{ resource.name }}</h3>
                <span>{{ folderName(resource) }}</span>
              </div>
              <p>{{ resource.page_count }} 页 · {{ formatSize(resource.size) }} · 已提取 {{ resource.text_length }} 字</p>
              <small>{{ formatDate(resource.created_at) }}</small>
            </div>
            <div class="resource-actions">
              <a :href="resourceDownloadUrl(userProfile.userId, resource.id)" target="_blank" title="查看或下载">↗</a>
              <button title="删除" @click="removeResource(resource)">×</button>
            </div>
          </article>
        </div>

        <div v-else class="empty-state">
          <div class="empty-icon">PDF</div>
          <h2>{{ searchQuery ? '没有匹配的文件' : `向“${uploadTargetFolder}”上传第一份 PDF` }}</h2>
          <p>{{ searchQuery ? '换个关键词再试试。' : '文件会保存在当前课程文件夹中，之后可直接作为 AI 生成资料。' }}</p>
          <button v-if="!searchQuery" :disabled="uploading" @click="choosePdf">选择 PDF 文件</button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.resource-library { display: grid; gap: 22px; color: #202938; }
.library-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; }
.library-header h1 { margin: 5px 0 7px; font-size: 28px; }
.library-header p { margin: 0; color: #7c8494; font-size: 13px; }
.generate-btn, .upload-btn, .folder-form button, .empty-state button {
  border: 0;
  border-radius: 10px;
  color: #fff;
  background: #202938;
  font-weight: 700;
}
.generate-btn { padding: 10px 14px; }
.library-shell { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 16px; align-items: start; }
.folder-panel, .file-panel {
  border: 1px solid #e7e9ef;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 12px 30px rgba(31, 42, 68, .04);
}
.folder-panel { display: grid; gap: 8px; padding: 14px; }
.folder-panel-head { display: flex; align-items: center; justify-content: space-between; padding: 4px 2px 8px; }
.folder-panel-head strong { font-size: 14px; }
.folder-panel-head button {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: 0;
  border-radius: 50%;
  background: #f1f2f5;
  color: #202938;
  font-size: 20px;
}
.folder-form { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; margin-bottom: 6px; }
.folder-form input {
  min-width: 0;
  padding: 10px 11px;
  border: 1px solid #dfe3ea;
  border-radius: 10px;
  outline: 0;
}
.folder-form button { padding: 0 12px; }
.folder-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 11px 12px;
  border: 0;
  border-radius: 10px;
  color: #2c3442;
  background: transparent;
  text-align: left;
}
.folder-item span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.folder-item small { color: #8b93a1; }
.folder-item.active { background: #f0f1f4; font-weight: 750; }
.file-panel { min-width: 0; padding: 18px; }
.library-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 16px; }
.library-toolbar h2 { margin: 0 0 4px; font-size: 21px; }
.library-toolbar p { margin: 0; color: #8b93a1; font-size: 12px; }
.toolbar-actions { display: flex; align-items: center; gap: 10px; }
.search-bar {
  display: flex;
  align-items: center;
  width: min(330px, 36vw);
  padding: 0 12px;
  border: 1px solid #e0e3e9;
  border-radius: 999px;
  background: #fff;
}
.search-bar span { color: #8c94a2; font-size: 18px; }
.search-bar input { width: 100%; padding: 10px 8px; border: 0; outline: 0; background: transparent; }
.upload-btn { padding: 10px 14px; white-space: nowrap; }
.resources-grid { display: grid; gap: 11px; }
.resource-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border: 1px solid #edf0f4;
  border-radius: 14px;
  background: #fff;
}
.pdf-icon, .empty-icon {
  display: grid;
  place-items: center;
  width: 48px;
  height: 56px;
  border-radius: 9px;
  color: #c43d3d;
  background: #fff0f0;
  font-size: 11px;
  font-weight: 850;
}
.resource-title-row { display: flex; align-items: center; gap: 10px; min-width: 0; }
.resource-title-row h3 {
  margin: 0;
  overflow: hidden;
  color: #30394a;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.resource-title-row span {
  flex: none;
  padding: 4px 8px;
  border-radius: 999px;
  color: #5f6878;
  background: #f2f3f6;
  font-size: 11px;
}
.resource-info p { margin: 6px 0 4px; color: #737d8e; font-size: 11px; }
.resource-info small { color: #9aa1ad; font-size: 10px; }
.resource-actions { display: flex; gap: 6px; }
.resource-actions a, .resource-actions button {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 9px;
  color: #5f6878;
  background: #f2f3f6;
  text-decoration: none;
  font-size: 18px;
}
.library-state, .library-error { margin-bottom: 12px; padding: 12px 14px; border-radius: 11px; font-size: 12px; }
.library-state { color: #697386; background: #f2f3f6; }
.library-error { color: #a23737; background: #fff0f0; }
.empty-state {
  display: grid;
  justify-items: center;
  padding: 70px 20px;
  border: 1px dashed #d9dde5;
  border-radius: 18px;
  text-align: center;
  background: #fff;
}
.empty-state h2 { margin: 18px 0 7px; color: #30394a; font-size: 18px; }
.empty-state p { margin: 0 0 18px; color: #89919f; font-size: 12px; }
.empty-state button { padding: 10px 14px; }
button { cursor: pointer; }
button:disabled { cursor: wait; opacity: .6; }
@media (max-width: 900px) {
  .library-header, .library-toolbar { flex-direction: column; align-items: stretch; }
  .library-shell { grid-template-columns: 1fr; }
  .toolbar-actions { flex-direction: column; align-items: stretch; }
  .search-bar { width: auto; }
}
</style>
