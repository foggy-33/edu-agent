<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  deleteResource,
  getResourceContent,
  listCategories,
  listResources,
  resourceDownloadUrl,
  resourcePreviewUrl,
  updateResourceFolder,
  uploadResource,
} from '../api/client'
import { loadUserProfile } from '../api/userProfile'
import type { UploadedResource } from '../types'
import MermaidRenderer from './MermaidRenderer.vue'

const emit = defineEmits<{
  navigate: [page: 'collaborative']
}>()

const ALL_FOLDERS = '全部资料'
const LEGACY_FOLDER = '历史资料'

const TYPE_FILTERS = [
  { value: 'all', label: '全部类型', icon: '▦' },
  { value: 'pdf', label: 'PDF', icon: 'PDF' },
  { value: 'lecture', label: '讲义', icon: '≡' },
  { value: 'mindmap', label: '思维导图', icon: '⌘' },
  { value: 'reading', label: '阅读材料', icon: '▤' },
  { value: 'markdown', label: '文档', icon: '□' },
]

const userProfile = ref(loadUserProfile())
const fileInput = ref<HTMLInputElement | null>(null)
const resources = ref<UploadedResource[]>([])
const customFolders = ref<string[]>([])
const activeFolder = ref(ALL_FOLDERS)
const activeType = ref('all')
const searchQuery = ref('')
const newFolderName = ref('')
const creatingFolder = ref(false)
const loading = ref(false)
const uploading = ref(false)
const error = ref('')
const previewResource = ref<UploadedResource | null>(null)
const previewContent = ref('')
const previewLoading = ref(false)
const pdfLoading = ref(false)
const movingResource = ref<UploadedResource | null>(null)
const moveTargetFolder = ref('')
const serverCategories = ref<Array<{ name: string; count: number }>>([])

const folders = computed(() => {
  const names = new Set<string>()
  customFolders.value.forEach(name => names.add(name))
  resources.value.forEach(item => names.add(folderName(item)))
  serverCategories.value.forEach(cat => names.add(cat.name))
  return Array.from(names).filter(Boolean)
})

const folderStats = computed(() =>
  folders.value.map(name => ({
    name,
    count: resources.value.filter(item => folderName(item) === name).length,
  }))
)

const uploadTargetFolder = computed(() =>
  activeFolder.value === ALL_FOLDERS ? '' : activeFolder.value
)

const activeFolderCount = computed(() =>
  activeFolder.value === ALL_FOLDERS
    ? resources.value.length
    : resources.value.filter(item => folderName(item) === activeFolder.value).length
)

const visibleResources = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  return resources.value.filter(item => {
    const inFolder = activeFolder.value === ALL_FOLDERS || folderName(item) === activeFolder.value
    const inType = activeType.value === 'all' || item.type === activeType.value
    const matched = !keyword || item.name.toLowerCase().includes(keyword) || folderName(item).toLowerCase().includes(keyword)
    return inFolder && inType && matched
  })
})

function folderName(item: UploadedResource) {
  return item.course_folder || LEGACY_FOLDER
}

function folderStorageKey() {
  return `edu-resource-folders:${userProfile.value.userId}`
}

function loadCustomFolders() {
  try {
    const raw = localStorage.getItem(folderStorageKey())
    const parsed = raw ? JSON.parse(raw) : []
    customFolders.value = Array.isArray(parsed)
      ? parsed
          .filter(item => typeof item === 'string')
          .map(item => item.trim())
          .filter(item => item && item !== '\u672a\u5206\u7c7b')
      : []
  } catch {
    customFolders.value = []
  }
}

function saveCustomFolders(next: string[]) {
  customFolders.value = Array.from(new Set(next.map(item => item.trim()).filter(Boolean)))
  localStorage.setItem(folderStorageKey(), JSON.stringify(customFolders.value))
}

function formatSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(value: string) {
  return new Date(value).toLocaleString('zh-CN')
}

async function loadResourceList() {
  loading.value = true
  error.value = ''
  try {
    const [res, catRes] = await Promise.all([
      listResources(userProfile.value.userId),
      listCategories(userProfile.value.userId).catch(() => ({ categories: [] })),
    ])
    const filtered = res.resources.filter((r: UploadedResource) => r.type !== 'path')
    resources.value = filtered
    serverCategories.value = catRes.categories || []
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '资料加载失败'
  } finally {
    loading.value = false
  }
}

function resourceTypeLabel(type: string) {
  const map: Record<string, string> = {
    pdf: 'PDF',
    markdown: '文档',
    mindmap: '思维导图',
    lecture: '讲义',
    reading: '阅读材料',
    review: '文档',
    exercises: '文档',
  }
  return map[type] || type || '资料'
}

function resourceTypeIcon(type: string) {
  const map: Record<string, string> = {
    pdf: 'PDF',
    markdown: '□',
    mindmap: '⌘',
    lecture: '≡',
    reading: '▤',
    review: '✓',
    exercises: '?',
  }
  return map[type] || '□'
}

function resourceSummary(item: UploadedResource) {
  if (item.summary) return item.summary
  if (item.type === 'pdf') {
    return `${item.page_count} 页 PDF 文档，已提取 ${item.text_length} 字文本内容，支持全文检索和问答引用。`
  }
  if (item.type === 'mindmap') {
    return '结构化思维导图，帮助快速梳理知识框架和核心概念关系。'
  }
  if (item.type === 'lecture') {
    return '系统整理的课程讲义，涵盖知识点讲解、案例分析和重点标注。'
  }
  if (item.type === 'reading') {
    return '拓展阅读材料，深化对主题的理解和多角度思考。'
  }
  if (item.type === 'markdown' || item.type === 'review' || item.type === 'exercises') {
    return '文档资料，便于编辑和二次使用。'
  }
  return `${item.text_length} 字资料内容。`
}

function openMoveDialog(item: UploadedResource) {
  movingResource.value = item
  moveTargetFolder.value = folderName(item)
}

function closeMoveDialog() {
  movingResource.value = null
  moveTargetFolder.value = ''
}

async function confirmMove() {
  if (!movingResource.value || !moveTargetFolder.value.trim()) return
  try {
    const result = await updateResourceFolder(
      userProfile.value.userId,
      movingResource.value.id,
      moveTargetFolder.value.trim()
    )
    const idx = resources.value.findIndex(r => r.id === movingResource.value!.id)
    if (idx !== -1) {
      resources.value[idx] = result.resource
    }
    closeMoveDialog()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '移动失败'
  }
}

function createFolder() {
  const name = newFolderName.value.trim()
  if (!name) {
    creatingFolder.value = true
    return
  }
  if (name === ALL_FOLDERS) {
    error.value = '课程文件夹不能命名为“全部资料”'
    return
  }
  if (!folders.value.includes(name)) {
    saveCustomFolders([...customFolders.value, name])
  }
  activeFolder.value = name
  newFolderName.value = ''
  creatingFolder.value = false
  error.value = ''
}

function chooseFolder(name: string) {
  activeFolder.value = name
  error.value = ''
}

function choosePdf() {
  if (!uploadTargetFolder.value) {
    error.value = '请先选择或新建一个课程文件夹，再上传资料'
    creatingFolder.value = true
    return
  }
  fileInput.value?.click()
}

const MAX_FILE_SIZE = 500 * 1024 * 1024

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  input.value = ''
  if (!files.length) return
  if (!uploadTargetFolder.value) {
    error.value = '请先选择课程文件夹'
    return
  }

  const invalid = files.find(file => file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf'))
  if (invalid) {
    error.value = `只能上传 PDF 文件：${invalid.name}`
    return
  }

  const oversized = files.find(file => file.size > MAX_FILE_SIZE)
  if (oversized) {
    error.value = `文件大小不能超过 500 MB：${oversized.name} (${formatSize(oversized.size)})`
    return
  }

  uploading.value = true
  error.value = ''
  const uploaded: UploadedResource[] = []
  try {
    for (const file of files) {
      const result = await uploadResource(userProfile.value.userId, file, uploadTargetFolder.value)
      uploaded.push(result.resource)
    }
    resources.value = [...uploaded, ...resources.value]
    activeFolder.value = uploadTargetFolder.value
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

async function openPreview(item: UploadedResource) {
  previewResource.value = item
  previewContent.value = ''
  previewLoading.value = true
  if (item.type === 'mindmap') {
    try {
      const res = await getResourceContent(userProfile.value.userId, item.id)
      previewContent.value = res.content
    } catch {
      previewContent.value = ''
    } finally {
      previewLoading.value = false
    }
  } else {
    pdfLoading.value = true
    setTimeout(() => {
      pdfLoading.value = false
      previewLoading.value = false
    }, 500)
  }
}

function closePreview() {
  previewResource.value = null
  previewContent.value = ''
  previewLoading.value = false
}

onMounted(() => {
  loadCustomFolders()
  loadResourceList()
})
</script>

<template>
  <div class="resource-library">
    <header class="library-header">
      <div>
        <h1>资料库</h1>
        <p>按课程建立资料文件夹，上传 PDF 后可用于问答、思维导图和练习题生成。</p>
      </div>
      <button class="generate-btn" @click="emit('navigate', 'collaborative')">
        基于资料生成
      </button>
    </header>

    <div class="library-shell">
      <aside class="folder-panel" aria-label="课程资料文件夹">
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
          <span>全部资料</span>
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
            <p v-if="uploadTargetFolder">{{ activeFolderCount }} 个资料，上传目标：{{ uploadTargetFolder }}</p>
            <p v-else>{{ activeFolderCount }} 个资料，请选择课程文件夹后上传</p>
          </div>
          <div class="toolbar-actions">
            <label class="search-bar">
              <span>⌕</span>
              <input v-model="searchQuery" type="text" placeholder="搜索资料或课程" />
            </label>
            <button class="upload-btn" :disabled="uploading || !uploadTargetFolder" @click="choosePdf">
              {{ uploading ? '解析中...' : '上传 PDF' }}
            </button>
            <input ref="fileInput" type="file" accept=".pdf,application/pdf" multiple hidden @change="handleUpload" />
          </div>
        </div>

        <div class="type-filter-bar">
          <button
            v-for="filter in TYPE_FILTERS"
            :key="filter.value"
            class="type-filter-chip"
            :class="{ active: activeType === filter.value }"
            @click="activeType = filter.value"
          >
            <span class="chip-icon">{{ filter.icon }}</span>
            <span class="chip-label">{{ filter.label }}</span>
          </button>
        </div>

        <div v-if="error" class="library-error">{{ error }}</div>
        <div v-if="loading" class="library-state">正在加载资料...</div>

        <div v-else-if="visibleResources.length" class="resources-list">
          <article v-for="resource in visibleResources" :key="resource.id" class="resource-list-item">
            <div class="list-item-icon">
              <span :class="['type-glyph', `type-glyph-${resource.type}`]" aria-hidden="true">{{ resourceTypeIcon(resource.type) }}</span>
            </div>
            <div class="list-item-body">
              <div class="list-item-header">
                <h3 class="list-item-title">{{ resource.name }}</h3>
                <div class="list-item-meta-top">
                  <span class="meta-tag type-tag">{{ resourceTypeLabel(resource.type) }}</span>
                  <span class="meta-tag folder-tag">{{ folderName(resource) }}</span>
                </div>
              </div>
              <p class="list-item-summary">{{ resourceSummary(resource) }}</p>
              <div class="list-item-footer">
                <span class="list-item-stats">
                  <template v-if="resource.type === 'pdf'">
                    {{ resource.page_count }} 页 · {{ formatSize(resource.size) }} · {{ resource.text_length }} 字
                  </template>
                  <template v-else>
                    {{ formatSize(resource.size) }} · {{ resource.text_length }} 字
                  </template>
                </span>
                <span class="list-item-date">{{ formatDate(resource.created_at) }}</span>
                <div class="list-item-actions">
                  <button class="list-action-btn" title="预览" aria-label="预览" @click="openPreview(resource)">⌕</button>
                  <button class="list-action-btn" title="移动分类" aria-label="移动分类" @click="openMoveDialog(resource)">↪</button>
                  <a class="list-action-btn" :href="resourceDownloadUrl(userProfile.userId, resource.id)" target="_blank" title="下载" aria-label="下载">↓</a>
                  <button class="list-action-btn danger" title="删除" @click="removeResource(resource)">×</button>
                </div>
              </div>
            </div>
          </article>
        </div>

        <div v-else class="empty-state">
          <div class="empty-icon" aria-hidden="true">▦</div>
          <h2>{{ searchQuery ? '没有匹配的资料' : (uploadTargetFolder ? `向“${uploadTargetFolder}”上传资料` : '先新建课程文件夹') }}</h2>
          <p>{{ searchQuery ? '换个关键词再试试。' : (uploadTargetFolder ? '可一次选择多个 PDF，资料会保存到当前课程文件夹。' : '上传资料前必须选择一个课程文件夹。') }}</p>
          <button v-if="!searchQuery && uploadTargetFolder" :disabled="uploading" @click="choosePdf">选择 PDF 文件</button>
          <button v-else-if="!searchQuery" @click="creatingFolder = true">新建课程文件夹</button>
        </div>
      </section>
    </div>

    <Teleport to="body">
      <div v-if="previewResource" class="preview-modal" @click.self="closePreview">
        <div class="preview-content">
          <header class="preview-header">
            <div>
              <h3>{{ previewResource.name }}</h3>
              <p>
                {{ resourceTypeLabel(previewResource.type) }} · {{ formatSize(previewResource.size) }}
                <template v-if="previewResource.type === 'pdf'"> · {{ previewResource.page_count }} 页</template>
              </p>
            </div>
            <button class="preview-close" @click="closePreview">×</button>
          </header>
          <div class="preview-body">
            <div v-if="previewLoading" class="preview-loading">
              <div class="loading-spinner"></div>
              <p>正在加载...</p>
            </div>
            <template v-else-if="previewResource.type === 'mindmap'">
              <div class="mindmap-preview">
                <MermaidRenderer v-if="previewContent" :chart="previewContent" />
                <div v-else class="preview-empty">暂无思维导图内容</div>
              </div>
            </template>
            <embed
              v-else-if="previewResource.type === 'pdf'"
              :src="resourcePreviewUrl(userProfile.userId, previewResource.id)"
              type="application/pdf"
              class="preview-embed"
              title="预览"
            />
            <iframe
              v-else
              :src="resourcePreviewUrl(userProfile.userId, previewResource.id)"
              class="preview-iframe"
              title="预览"
            />
          </div>
        </div>
      </div>

      <div v-if="movingResource" class="preview-modal" @click.self="closeMoveDialog">
        <div class="move-dialog">
          <header class="preview-header">
            <div>
              <h3>移动到分类</h3>
              <p>{{ movingResource.name }}</p>
            </div>
            <button class="preview-close" @click="closeMoveDialog">×</button>
          </header>
          <div class="move-body">
            <div class="folder-select-list">
              <button
                v-for="folder in folders"
                :key="folder"
                type="button"
                :class="['folder-option', moveTargetFolder === folder ? 'active' : '']"
                @click="moveTargetFolder = folder"
              >
                {{ folder }}
              </button>
            </div>
            <div class="move-new-folder">
              <input
                v-model="newFolderName"
                type="text"
                placeholder="或新建分类..."
                @keyup.enter="() => {
                  if (newFolderName.trim()) {
                    moveTargetFolder = newFolderName.trim()
                    newFolderName = ''
                  }
                }"
              />
            </div>
          </div>
          <div class="move-footer">
            <button class="btn-ghost" @click="closeMoveDialog">取消</button>
            <button class="btn-primary" :disabled="!moveTargetFolder.trim()" @click="confirmMove">确定移动</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.resource-library { display: flex; flex-direction: column; gap: 20px; color: #1f2937; max-width: 1200px; margin: 0 auto; }
.library-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; }
.library-header h1 { margin: 0 0 6px; font-size: 24px; font-weight: 600; }
.library-header p { margin: 0; color: #6b7280; font-size: 14px; }
.generate-btn, .upload-btn, .folder-form button, .empty-state button {
  border: 0;
  border-radius: 8px;
  color: #fff;
  background: #111827;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.generate-btn:hover, .upload-btn:hover { background: #1f2937; }
.generate-btn { padding: 9px 16px; }
.library-shell { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 16px; align-items: start; }
.folder-panel, .file-panel {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
}
.folder-panel { display: flex; flex-direction: column; gap: 6px; padding: 14px; }
.folder-panel-head { display: flex; align-items: center; justify-content: space-between; padding: 4px 2px 10px; }
.folder-panel-head strong { font-size: 14px; font-weight: 600; color: #111827; }
.folder-panel-head button {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 6px;
  background: #f3f4f6;
  color: #374151;
  font-size: 18px;
  cursor: pointer;
}
.folder-panel-head button:hover { background: #e5e7eb; }
.folder-form { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; margin-bottom: 6px; }
.folder-form input {
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  outline: 0;
  font-size: 13px;
}
.folder-form input:focus { border-color: #6b7280; }
.folder-form button { padding: 0 12px; font-size: 13px; }
.folder-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 8px 10px;
  border: 0;
  border-radius: 8px;
  color: #374151;
  background: transparent;
  text-align: left;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.folder-item span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.folder-item small { color: #9ca3af; font-size: 12px; }
.folder-item:hover { background: #f3f4f6; }
.folder-item.active { background: #f3f4f6; font-weight: 600; color: #111827; }
.file-panel { min-width: 0; padding: 18px; }
.library-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 16px; }
.library-toolbar h2 { margin: 0 0 4px; font-size: 18px; font-weight: 600; }
.library-toolbar p { margin: 0; color: #6b7280; font-size: 13px; }
.toolbar-actions { display: flex; align-items: center; gap: 10px; }
.search-bar {
  display: flex;
  align-items: center;
  width: min(280px, 36vw);
  padding: 0 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
}
.search-bar span { color: #9ca3af; font-size: 16px; }
.search-bar input { width: 100%; padding: 8px 8px; border: 0; outline: 0; background: transparent; font-size: 13px; }
.upload-btn { padding: 9px 14px; white-space: nowrap; }
.type-filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  margin-bottom: 16px;
  border-radius: 10px;
  background: #f9fafb;
}

.type-filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  background: #fff;
  color: #6b7280;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.type-filter-chip:hover {
  border-color: #d1d5db;
  color: #374151;
}

.type-filter-chip.active {
  border-color: #111827;
  background: #111827;
  color: #fff;
}

.type-filter-chip .chip-icon {
  font-size: 14px;
}

.resources-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.resource-list-item {
  display: grid;
  grid-template-columns: 56px 1fr;
  align-items: stretch;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
  transition: all 0.15s;
}

.resource-list-item:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.list-item-icon {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: 10px;
  background: #f3f4f6;
}

.list-item-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.list-item-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.list-item-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  line-height: 1.4;
}

.list-item-meta-top {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.meta-tag {
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.4;
}

.type-tag {
  background: #f3f4f6;
  color: #4b5563;
}

.folder-tag {
  background: #eff6ff;
  color: #2563eb;
}

.list-item-summary {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.list-item-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: auto;
  padding-top: 4px;
}

.list-item-stats {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 400;
  white-space: nowrap;
}

.list-item-date {
  font-size: 12px;
  color: #d1d5db;
  white-space: nowrap;
}

.list-item-actions {
  display: flex;
  flex-direction: row;
  gap: 6px;
  margin-left: auto;
}

.list-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s;
}

.list-action-btn:hover {
  border-color: #d1d5db;
  background: #f9fafb;
  color: #374151;
}

.list-action-btn.danger:hover {
  border-color: #fca5a5;
  background: #fef2f2;
  color: #dc2626;
}

.preview-embed {
  width: 100%;
  height: 100%;
  border: 0;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: 0;
  background: #fff;
}

.mindmap-preview {
  width: 100%;
  height: 100%;
  overflow: auto;
  padding: 24px;
  box-sizing: border-box;
  background: #fff;
}

.preview-empty {
  display: grid;
  place-items: center;
  height: 100%;
  color: #9ca3af;
  font-size: 14px;
}

@media (max-width: 720px) {
  .resource-list-item {
    grid-template-columns: 56px 1fr;
    gap: 14px;
    padding: 14px 16px;
  }
  .list-item-icon {
    width: 56px;
    height: 56px;
    border-radius: 12px;
  }
  .list-item-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
  .list-item-footer {
    flex-wrap: wrap;
  }
  .list-item-actions {
    order: 3;
    flex-basis: 100%;
    justify-content: flex-start;
  }
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
button:disabled { cursor: default; opacity: .55; }
@media (max-width: 900px) {
  .library-header, .library-toolbar { flex-direction: column; align-items: stretch; }
  .library-shell { grid-template-columns: 1fr; }
  .toolbar-actions { flex-direction: column; align-items: stretch; }
  .search-bar { width: auto; }
}

.preview-modal {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, .5);
  padding: 20px;
}

.preview-content {
  width: min(100%, 1200px);
  height: min(90vh, 800px);
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 24px 60px rgba(0, 0, 0, .15);
  display: grid;
  grid-template-rows: auto 1fr;
  overflow: hidden;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e7e9ef;
}

.preview-header h3 {
  margin: 0;
  font-size: 16px;
  color: #202938;
}

.preview-header p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #7c8494;
}

.preview-close {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 999px;
  background: #f1f2f5;
  color: #5f6878;
  font-size: 20px;
  cursor: pointer;
}

.preview-body {
  overflow: hidden;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
}

.preview-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e7e9ef;
  border-top-color: #202938;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.preview-embed {
  flex: 1;
  width: 100%;
  height: 100%;
  border: 0;
}

.move-dialog {
  width: min(480px, 90vw);
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 24px 60px rgba(0, 0, 0, .15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.move-body {
  padding: 20px;
  max-height: 60vh;
  overflow-y: auto;
}

.folder-select-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 14px;
}

.folder-option {
  padding: 9px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  color: #4b5563;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}

.folder-option:hover {
  border-color: #d1d5db;
  background: #f9fafb;
}

.folder-option.active {
  border-color: #111827;
  background: #f3f4f6;
  color: #111827;
}

.move-new-folder input {
  width: 100%;
  box-sizing: border-box;
  padding: 9px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s;
}

.move-new-folder input:focus {
  border-color: #6b7280;
}

.move-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #f3f4f6;
}

.btn-ghost {
  padding: 9px 16px;
  border: 1px solid #d1d5db;
  background: #fff;
  color: #374151;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.15s;
}

.btn-ghost:hover {
  background: #f9fafb;
}

.btn-primary {
  padding: 9px 16px;
  border: 1px solid #111827;
  background: #111827;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background: #1f2937;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* GPT-style monochrome resource workspace */
.resource-library {
  width: min(1100px, 100%);
  max-width: none;
  gap: 28px;
  color: #202123;
}

.library-header {
  align-items: center;
  padding: 2px 0 18px;
  border-bottom: 1px solid #ececec;
}

.library-header h1 {
  margin-bottom: 7px;
  color: #202123;
  font-size: 30px;
  font-weight: 650;
  letter-spacing: -.035em;
}

.library-header p {
  color: #6e6e80;
  font-size: 13px;
  line-height: 1.65;
}

.generate-btn,
.upload-btn,
.folder-form button,
.empty-state button,
.btn-primary {
  border-radius: 10px;
  color: #fff;
  background: #202123;
  font-weight: 600;
}

.generate-btn { padding: 11px 16px; }
.generate-btn:hover,
.upload-btn:hover,
.btn-primary:hover:not(:disabled) { background: #000; }

.library-shell {
  grid-template-columns: 210px minmax(0, 1fr);
  gap: 28px;
}

.folder-panel {
  position: sticky;
  top: 20px;
  gap: 3px;
  padding: 12px;
  border: 0;
  border-radius: 14px;
  background: #f7f7f8;
}

.folder-panel-head { padding: 5px 6px 11px; }
.folder-panel-head strong { color: #202123; font-size: 13px; font-weight: 650; }
.folder-panel-head button {
  width: 27px;
  height: 27px;
  border-radius: 8px;
  color: #444654;
  background: transparent;
  font-size: 17px;
}
.folder-panel-head button:hover { background: #e9e9ec; }
.folder-form input { border-color: #d9d9df; border-radius: 9px; background: #fff; }
.folder-item {
  min-height: 39px;
  padding: 9px 10px;
  border-radius: 9px;
  color: #444654;
  font-size: 13px;
}
.folder-item:hover { background: #ededf0; }
.folder-item.active { color: #202123; background: #e7e7ea; font-weight: 650; }
.folder-item small { color: #8e8e9b; font-variant-numeric: tabular-nums; }

.file-panel {
  min-height: 440px;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
}

.library-toolbar {
  align-items: flex-end;
  margin-bottom: 17px;
  padding-bottom: 17px;
  border-bottom: 1px solid #ececec;
}
.library-toolbar h2 { color: #202123; font-size: 20px; font-weight: 650; letter-spacing: -.02em; }
.library-toolbar p { color: #8e8e9b; font-size: 12px; }
.toolbar-actions { gap: 8px; }
.search-bar {
  width: min(270px, 32vw);
  min-height: 38px;
  padding: 0 11px;
  border-color: transparent;
  border-radius: 10px;
  color: #8e8e9b;
  background: #f7f7f8;
}
.search-bar:focus-within { border-color: #cfcfd5; background: #fff; }
.search-bar input { color: #202123; }
.upload-btn { min-height: 38px; padding: 9px 14px; }

.type-filter-bar {
  gap: 7px;
  padding: 0;
  margin-bottom: 12px;
  border-radius: 0;
  background: transparent;
}
.type-filter-chip {
  min-height: 32px;
  gap: 7px;
  padding: 5px 11px;
  border-color: #e1e1e4;
  border-radius: 999px;
  color: #666674;
  background: #fff;
  font-size: 12px;
}
.type-filter-chip:hover { border-color: #bcbcc3; color: #202123; background: #f7f7f8; }
.type-filter-chip.active { border-color: #202123; color: #fff; background: #202123; }
.type-filter-chip .chip-icon {
  min-width: 16px;
  color: inherit;
  text-align: center;
  font-size: 12px;
  font-weight: 650;
  line-height: 1;
}

.resources-list { gap: 0; }
.resource-list-item {
  grid-template-columns: 44px minmax(0, 1fr);
  gap: 14px;
  padding: 18px 8px;
  border: 0;
  border-bottom: 1px solid #eeeeef;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}
.resource-list-item:first-child { border-top: 1px solid #eeeeef; }
.resource-list-item:hover { border-color: #e5e5e7; background: #fafafa; box-shadow: none; }
.list-item-icon {
  width: 42px;
  height: 42px;
  border: 1px solid #e4e4e7;
  border-radius: 11px;
  color: #444654;
  background: #f7f7f8;
}
.type-glyph { display: inline-grid; place-items: center; color: currentColor; font-size: 18px; font-weight: 500; line-height: 1; }
.type-glyph-pdf { font-size: 9px; font-weight: 750; letter-spacing: -.03em; }
.list-item-body { gap: 7px; }
.list-item-title { color: #202123; font-size: 15px; font-weight: 620; }
.list-item-summary { color: #6e6e80; font-size: 12px; line-height: 1.6; }
.meta-tag {
  padding: 3px 7px;
  border: 1px solid #e5e5e7;
  border-radius: 999px;
  color: #6e6e80;
  background: #f7f7f8;
  font-size: 10px;
}
.folder-tag { color: #6e6e80; background: #fff; }
.list-item-stats,
.list-item-date { color: #9b9ba7; font-size: 11px; }
.list-item-actions { opacity: 0; transition: opacity .15s ease; }
.resource-list-item:hover .list-item-actions,
.resource-list-item:focus-within .list-item-actions { opacity: 1; }
.list-action-btn {
  width: 29px;
  height: 29px;
  border-color: transparent;
  border-radius: 8px;
  color: #6e6e80;
  background: transparent;
  font-size: 15px;
}
.list-action-btn:hover { border-color: #e1e1e4; color: #202123; background: #f0f0f1; }
.list-action-btn.danger:hover { border-color: #e1e1e4; color: #202123; background: #ececee; }

.library-state,
.library-error { border-radius: 10px; }
.library-state { color: #6e6e80; background: #f7f7f8; }
.library-error { color: #7f1d1d; background: #faf3f3; }
.empty-state {
  min-height: 300px;
  align-content: center;
  padding: 44px 20px;
  border: 0;
  border-radius: 14px;
  color: #202123;
  background: #fafafa;
}
.empty-icon { display: grid; place-items: center; width: 42px; height: 42px; border: 1px solid #dedee2; border-radius: 12px; color: #555563; background: #fff; font-size: 19px; }
.empty-state h2 { margin: 14px 0 6px; color: #202123; font-size: 16px; font-weight: 650; }
.empty-state p { color: #858592; }

.preview-modal { background: rgba(0, 0, 0, .42); backdrop-filter: blur(2px); }
.preview-content,
.move-dialog { border: 1px solid #dedee2; border-radius: 16px; box-shadow: 0 24px 70px rgba(0, 0, 0, .18); }
.preview-header { border-bottom-color: #ececee; }
.preview-header h3 { color: #202123; }
.preview-header p { color: #858592; }
.preview-close { border-radius: 9px; color: #555563; background: #f2f2f3; }
.preview-body { background: #f7f7f8; }
.loading-spinner { border-color: #dedee2; border-top-color: #202123; }
.folder-option.active { border-color: #202123; color: #202123; background: #f0f0f1; }

@media (max-width: 900px) {
  .library-shell { gap: 18px; }
  .folder-panel { position: static; }
  .library-toolbar { align-items: stretch; }
  .search-bar { width: auto; }
}

@media (max-width: 720px) {
  .resource-library { gap: 20px; }
  .library-header { align-items: stretch; }
  .library-header h1 { font-size: 26px; }
  .generate-btn { align-self: flex-start; }
  .resource-list-item { grid-template-columns: 38px minmax(0, 1fr); gap: 11px; padding: 15px 4px; }
  .list-item-icon { width: 36px; height: 36px; border-radius: 9px; }
  .list-item-actions { opacity: 1; }
  .list-item-date { flex-basis: 100%; }
}
</style>
