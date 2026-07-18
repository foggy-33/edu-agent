<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import type { PDFDocumentLoadingTask, PDFDocumentProxy, RenderTask } from 'pdfjs-dist'
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import {
  addCoursePdfAnnotation,
  courseMaterialPreviewUrl,
  deleteCoursePdfAnnotation,
  listCoursePdfAnnotations,
} from '../api/client'
import type { CoursePdfAnnotation, CoursePdfMaterial } from '../types'

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker

const props = defineProps<{
  material: CoursePdfMaterial
  course: string
  userId: string
}>()

const emit = defineEmits<{ close: [] }>()
const canvas = ref<HTMLCanvasElement | null>(null)
const pageStage = ref<HTMLDivElement | null>(null)
const noteInput = ref<HTMLTextAreaElement | null>(null)
const pageNumber = ref(1)
const pageCount = ref(0)
const scale = ref(1.15)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const placing = ref(false)
const note = ref('')
const draftPosition = ref<{ x: number; y: number } | null>(null)
const annotations = ref<CoursePdfAnnotation[]>([])
let pdfDocument: PDFDocumentProxy | null = null
let loadingTask: PDFDocumentLoadingTask | null = null
let renderTask: RenderTask | null = null
let renderSequence = 0
const originalBodyOverflow = document.body.style.overflow

const pageAnnotations = computed(() =>
  annotations.value.filter((item) => item.page === pageNumber.value)
)
const displayTitle = computed(() =>
  props.material.name.replace(/^\d+\s*/, '').replace(/-\d+$/, '').trim() || props.course
)

async function loadDocument() {
  loading.value = true
  error.value = ''
  try {
    loadingTask = pdfjsLib.getDocument({
      url: courseMaterialPreviewUrl(props.course, props.material.id),
    })
    pdfDocument = await loadingTask.promise
    pageCount.value = pdfDocument.numPages
    pageNumber.value = 1
    const result = await listCoursePdfAnnotations(props.userId, props.course, props.material.id)
    annotations.value = result.annotations
    await nextTick()
    await renderPage()
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : 'PDF 加载失败'
  } finally {
    loading.value = false
  }
}

async function renderPage() {
  if (!pdfDocument || !canvas.value) return
  const sequence = ++renderSequence
  if (renderTask) {
    renderTask.cancel()
    try {
      await renderTask.promise
    } catch {
      // RenderingCancelledException is expected when the user flips pages quickly.
    }
    renderTask = null
  }
  const page = await pdfDocument.getPage(pageNumber.value)
  const viewport = page.getViewport({ scale: scale.value })
  const outputScale = Math.min(window.devicePixelRatio || 1, 2)
  const target = canvas.value
  if (sequence !== renderSequence) return
  target.width = Math.floor(viewport.width * outputScale)
  target.height = Math.floor(viewport.height * outputScale)
  target.style.width = `${Math.floor(viewport.width)}px`
  target.style.height = `${Math.floor(viewport.height)}px`
  renderTask = page.render({
    canvas: target,
    viewport,
    transform: outputScale === 1 ? undefined : [outputScale, 0, 0, outputScale, 0, 0],
  })
  try {
    await renderTask.promise
  } catch (cause) {
    if (sequence === renderSequence) throw cause
  }
  if (sequence === renderSequence) renderTask = null
}

async function changePage(nextPage: number) {
  if (nextPage < 1 || nextPage > pageCount.value || nextPage === pageNumber.value) return
  pageNumber.value = nextPage
  draftPosition.value = null
  await renderPage()
}

async function changeScale(delta: number) {
  scale.value = Math.max(0.7, Math.min(2, Number((scale.value + delta).toFixed(2))))
  await renderPage()
}

async function choosePosition(event: MouseEvent) {
  if (!placing.value || !pageStage.value) return
  event.stopPropagation()
  const rect = pageStage.value.getBoundingClientRect()
  draftPosition.value = {
    x: Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width)),
    y: Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height)),
  }
  placing.value = false
  await nextTick()
  noteInput.value?.focus()
}

function turnPageFromSide(event: MouseEvent) {
  if (placing.value || !pageCount.value) return
  const area = event.currentTarget as HTMLElement
  const rect = area.getBoundingClientRect()
  const position = (event.clientX - rect.left) / rect.width
  if (position <= 0.28 && pageNumber.value > 1) {
    void changePage(pageNumber.value - 1)
  } else if (position >= 0.72 && pageNumber.value < pageCount.value) {
    void changePage(pageNumber.value + 1)
  }
}

async function saveAnnotation() {
  if (!note.value.trim()) return
  saving.value = true
  error.value = ''
  try {
    const result = await addCoursePdfAnnotation(props.material.id, {
      user_id: props.userId,
      course: props.course,
      page: pageNumber.value,
      content: note.value.trim(),
      x: draftPosition.value?.x ?? null,
      y: draftPosition.value?.y ?? null,
    })
    annotations.value.push(result.annotation)
    note.value = ''
    draftPosition.value = null
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '批注保存失败'
  } finally {
    saving.value = false
  }
}

async function removeAnnotation(annotation: CoursePdfAnnotation) {
  try {
    await deleteCoursePdfAnnotation(
      props.material.id,
      annotation.id,
      props.userId,
      props.course,
    )
    annotations.value = annotations.value.filter((item) => item.id !== annotation.id)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '批注删除失败'
  }
}

function closeOnEscape(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
  const target = event.target as HTMLElement | null
  if (target?.tagName === 'TEXTAREA' || target?.tagName === 'INPUT') return
  if (event.key === 'ArrowLeft') {
    event.preventDefault()
    void changePage(pageNumber.value - 1)
  } else if (event.key === 'ArrowRight') {
    event.preventDefault()
    void changePage(pageNumber.value + 1)
  }
}

watch(() => props.material.id, loadDocument)
onMounted(() => {
  document.body.style.overflow = 'hidden'
  window.addEventListener('keydown', closeOnEscape)
  loadDocument()
})
onBeforeUnmount(() => {
  renderTask?.cancel()
  document.body.style.overflow = originalBodyOverflow
  window.removeEventListener('keydown', closeOnEscape)
  loadingTask?.destroy()
})
</script>

<template>
  <div class="pdf-reader" role="dialog" aria-modal="true" aria-label="课程 PDF 阅读器">
    <header class="reader-header">
      <div class="title-group">
        <span class="pdf-badge">PDF</span>
        <div>
          <strong>{{ displayTitle }}</strong>
          <span>{{ course }} · {{ Math.max(1, Math.round(material.size / 1024 / 1024 * 10) / 10) }} MB</span>
        </div>
      </div>
      <div class="page-controls">
        <button :disabled="pageNumber <= 1" @click="changePage(pageNumber - 1)" aria-label="上一页">←</button>
        <span>{{ pageNumber }} / {{ pageCount || '—' }}</span>
        <button :disabled="pageNumber >= pageCount" @click="changePage(pageNumber + 1)" aria-label="下一页">→</button>
        <i></i>
        <button @click="changeScale(-0.15)" aria-label="缩小">−</button>
        <span>{{ Math.round(scale * 100) }}%</span>
        <button @click="changeScale(0.15)" aria-label="放大">＋</button>
      </div>
      <button class="close-button" @click="emit('close')" aria-label="关闭 PDF 阅读器">×</button>
    </header>

    <main class="reader-body">
      <section class="document-area" @click="turnPageFromSide">
        <span v-if="pageNumber > 1" class="page-side-hint previous" aria-hidden="true">‹</span>
        <span v-if="pageNumber < pageCount" class="page-side-hint next" aria-hidden="true">›</span>
        <div v-if="loading" class="reader-state">正在打开 PDF…</div>
        <div v-else-if="error && !pageCount" class="reader-state error-state">{{ error }}</div>
        <div v-show="!loading && pageCount" class="page-stage" ref="pageStage" :class="{ placing }" @click="choosePosition">
          <canvas ref="canvas"></canvas>
          <button
            v-for="(item, index) in pageAnnotations"
            :key="item.id"
            class="note-marker"
            :style="{ left: `${(item.x ?? 0.97) * 100}%`, top: `${(item.y ?? (0.06 + index * 0.055)) * 100}%` }"
            :title="item.content"
            @click.stop
          >
            {{ annotations.indexOf(item) + 1 }}
          </button>
          <span
            v-if="draftPosition"
            class="draft-marker"
            :style="{ left: `${draftPosition.x * 100}%`, top: `${draftPosition.y * 100}%` }"
          ></span>
        </div>
      </section>

      <aside class="annotation-panel">
        <div class="panel-heading">
          <div>
            <h2>页面批注</h2>
            <p>第 {{ pageNumber }} 页 · {{ pageAnnotations.length }} 条</p>
          </div>
          <button :class="{ active: placing }" @click="placing = !placing">
            {{ placing ? '点击正文定位' : '＋ 定位批注' }}
          </button>
        </div>

        <textarea
          ref="noteInput"
          v-model="note"
          rows="4"
          maxlength="2000"
          placeholder="记录这一页的要点、疑问或补充…"
          @keydown.ctrl.enter="saveAnnotation"
          @keydown.meta.enter="saveAnnotation"
        ></textarea>
        <div class="compose-footer">
          <span>{{ draftPosition ? '已关联页面位置' : '保存为整页批注' }}</span>
          <button :disabled="saving || !note.trim()" @click="saveAnnotation">
            {{ saving ? '保存中…' : '保存批注' }}
          </button>
        </div>
        <p v-if="error" class="inline-error">{{ error }}</p>

        <div class="annotation-list">
          <article v-for="item in annotations" :key="item.id" :class="{ current: item.page === pageNumber }">
            <button class="annotation-content" @click="changePage(item.page)">
              <span>第 {{ item.page }} 页</span>
              <p>{{ item.content }}</p>
            </button>
            <button class="delete-note" @click="removeAnnotation(item)" aria-label="删除批注">×</button>
          </article>
          <div v-if="!annotations.length" class="empty-notes">
            <span>⌁</span>
            <p>还没有批注</p>
            <small>选择页面位置或直接输入整页笔记</small>
          </div>
        </div>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.pdf-reader { position: fixed; inset: 0; z-index: 1200; display: flex; flex-direction: column; background: #f3f3f1; color: #171717; }
.reader-header { min-height: 68px; padding: 10px 20px; background: rgba(255,255,255,.96); border-bottom: 1px solid #dededb; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 20px; }
.title-group { display: flex; align-items: center; gap: 12px; min-width: 0; }
.title-group div { min-width: 0; display: flex; flex-direction: column; }
.title-group strong { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 14px; }
.title-group span:not(.pdf-badge) { color: #777; font-size: 12px; }
.pdf-badge { width: 38px; height: 38px; border: 1px solid #d2d2cf; border-radius: 10px; display: grid; place-items: center; font-size: 10px; font-weight: 800; }
.page-controls { display: flex; align-items: center; gap: 5px; padding: 5px; border: 1px solid #dededb; border-radius: 12px; background: #fafafa; }
.page-controls button, .close-button { border: 0; background: transparent; border-radius: 8px; cursor: pointer; color: #222; }
.page-controls button { width: 30px; height: 30px; font-size: 16px; }
.page-controls button:hover:not(:disabled), .close-button:hover { background: #ececea; }
.page-controls button:disabled { opacity: .3; cursor: default; }
.page-controls span { min-width: 58px; text-align: center; font-size: 12px; }
.page-controls i { width: 1px; height: 18px; background: #ddd; margin: 0 3px; }
.close-button { justify-self: end; width: 38px; height: 38px; font-size: 26px; font-weight: 300; }
.reader-body { min-height: 0; flex: 1; display: grid; grid-template-columns: minmax(0, 1fr) 340px; }
.document-area { position: relative; min-width: 0; overflow: auto; padding: 32px; display: flex; justify-content: center; align-items: flex-start; }
.page-side-hint { position: fixed; top: 50%; z-index: 3; width: 42px; height: 42px; border: 1px solid rgba(0,0,0,.1); border-radius: 50%; background: rgba(255,255,255,.82); color: #555; display: grid; place-items: center; font: 300 30px/1 sans-serif; box-shadow: 0 4px 18px rgba(0,0,0,.08); pointer-events: none; opacity: .48; }
.page-side-hint.previous { left: 20px; }
.page-side-hint.next { right: 360px; }
.page-stage { position: relative; flex: 0 0 auto; box-shadow: 0 14px 50px rgba(0,0,0,.14); background: white; line-height: 0; }
.page-stage.placing { cursor: crosshair; outline: 3px solid rgba(23,23,23,.15); outline-offset: 5px; }
.page-stage canvas { display: block; max-width: none; }
.note-marker, .draft-marker { position: absolute; transform: translate(-50%, -50%); width: 25px; height: 25px; border-radius: 50%; border: 2px solid white; background: #171717; color: white; display: grid; place-items: center; font: 700 11px/1 sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,.28); }
.draft-marker { background: white; border: 6px solid #171717; animation: marker-pulse 1.2s infinite; }
@keyframes marker-pulse { 50% { transform: translate(-50%,-50%) scale(1.25); } }
.annotation-panel { overflow: auto; padding: 22px; background: #fff; border-left: 1px solid #dededb; }
.panel-heading { display: flex; justify-content: space-between; align-items: start; gap: 12px; margin-bottom: 18px; }
.panel-heading h2 { margin: 0; font-size: 18px; }
.panel-heading p { margin: 3px 0 0; color: #888; font-size: 12px; }
.panel-heading button, .compose-footer button { border: 1px solid #d8d8d5; background: white; border-radius: 999px; padding: 8px 12px; font-size: 12px; cursor: pointer; }
.panel-heading button.active, .compose-footer button { background: #171717; border-color: #171717; color: white; }
.annotation-panel textarea { width: 100%; resize: vertical; box-sizing: border-box; border: 1px solid #d8d8d5; border-radius: 13px; padding: 12px; font: inherit; font-size: 13px; line-height: 1.6; outline: none; }
.annotation-panel textarea:focus { border-color: #777; box-shadow: 0 0 0 3px #f0f0ee; }
.compose-footer { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin: 9px 0 18px; }
.compose-footer span { color: #888; font-size: 11px; }
.compose-footer button:disabled { opacity: .35; cursor: default; }
.inline-error { background: #f7eeee; color: #8a2929; border-radius: 9px; padding: 9px; font-size: 12px; }
.annotation-list { display: flex; flex-direction: column; gap: 9px; }
.annotation-list article { display: flex; border: 1px solid #e4e4e1; border-radius: 12px; background: #fafafa; }
.annotation-list article.current { border-color: #999; background: white; }
.annotation-content { flex: 1; min-width: 0; padding: 11px 4px 11px 12px; text-align: left; border: 0; background: transparent; cursor: pointer; }
.annotation-content span { font-size: 11px; color: #777; }
.annotation-content p { margin: 4px 0 0; color: #333; font-size: 13px; line-height: 1.45; white-space: pre-wrap; }
.delete-note { width: 36px; border: 0; background: transparent; color: #999; cursor: pointer; font-size: 18px; }
.delete-note:hover { color: #111; }
.empty-notes, .reader-state { color: #8a8a86; text-align: center; }
.empty-notes { padding: 40px 10px; }
.empty-notes span { font-size: 30px; }
.empty-notes p { margin: 8px 0 3px; color: #444; }
.empty-notes small { font-size: 11px; }
.reader-state { margin-top: 25vh; }
.error-state { color: #8a2929; }
@media (max-width: 900px) {
  .reader-header { grid-template-columns: minmax(0,1fr) auto; }
  .page-controls { grid-column: 1 / -1; grid-row: 2; justify-self: center; }
  .reader-body { grid-template-columns: 1fr; overflow: auto; }
  .document-area { min-height: 60vh; overflow: visible; padding: 18px; }
  .page-side-hint.previous { left: 10px; }
  .page-side-hint.next { right: 10px; }
  .annotation-panel { border-left: 0; border-top: 1px solid #dededb; overflow: visible; }
}
</style>
