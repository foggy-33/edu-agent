<script setup lang="ts">
import { computed, ref } from 'vue'
import { testSiliconFlow } from '../api/client'
import { loadSiliconFlowConfig, saveSiliconFlowConfig } from '../api/settings'

type ModelKind = '全部' | '对话' | '推理' | '编程' | '视觉' | '生图'

interface SiliconFlowModel {
  id: string
  provider: string
  title: string
  description: string
  tags: string[]
  kind: Exclude<ModelKind, '全部'>[]
  hot?: boolean
}

const modelCatalog: SiliconFlowModel[] = [
  {
    id: 'deepseek-ai/DeepSeek-V4-Pro',
    provider: 'DeepSeek',
    title: 'DeepSeek-V4-Pro',
    description: 'DeepSeek V4 系列旗舰 MoE 语言模型，适合复杂推理、长上下文问答和 Agent 协作。',
    tags: ['对话', 'Tools', '1M', 'MoE', '推理模型'],
    kind: ['对话', '推理'],
    hot: true,
  },
  {
    id: 'deepseek-ai/DeepSeek-V4-Flash',
    provider: 'DeepSeek',
    title: 'DeepSeek-V4-Flash',
    description: 'DeepSeek V4 系列轻量高速模型，适合低延迟问答、摘要和快速资源生成。',
    tags: ['对话', 'Tools', '1M', 'MoE'],
    kind: ['对话'],
    hot: true,
  },
  {
    id: 'Pro/deepseek-ai/DeepSeek-V3.2',
    provider: 'DeepSeek',
    title: 'Pro DeepSeek-V3.2',
    description: '当前项目默认模型，兼顾推理质量、工具调用和中文教育内容生成。',
    tags: ['对话', 'Tools', '推理模型', 'Pro'],
    kind: ['对话', '推理'],
  },
  {
    id: 'deepseek-ai/DeepSeek-V3.2',
    provider: 'DeepSeek',
    title: 'DeepSeek-V3.2',
    description: '适合通用中文问答、学习资源生成、总结和轻量多 Agent 任务。',
    tags: ['对话', 'MoE', '推理模型'],
    kind: ['对话', '推理'],
  },
  {
    id: 'zai-org/GLM-5.2',
    provider: '智谱',
    title: 'GLM-5.2',
    description: '面向长程任务和工具调用的旗舰模型，适合复杂学习规划和资料分析。',
    tags: ['对话', 'Tools', '1M', 'MoE'],
    kind: ['对话', '推理'],
    hot: true,
  },
  {
    id: 'Pro/zai-org/GLM-5.1',
    provider: '智谱',
    title: 'Pro GLM-5.1',
    description: '面向智能体工程任务的 Pro 模型，适合规划、代码和长文档理解。',
    tags: ['对话', 'Tools', '754B', 'Vibe Coding'],
    kind: ['对话', '编程'],
  },
  {
    id: 'moonshotai/Kimi-K2.7-Code',
    provider: 'Kimi',
    title: 'Kimi-K2.7-Code',
    description: '面向代码任务的 agentic 模型，适合程序解释、工程问题和代码生成。',
    tags: ['对话', 'Tools', 'Coder', '256K'],
    kind: ['对话', '编程'],
    hot: true,
  },
  {
    id: 'Pro/moonshotai/Kimi-K2.6',
    provider: 'Kimi',
    title: 'Pro Kimi-K2.6',
    description: '原生多模态智能体模型，适合长上下文、多工具任务和复杂问答。',
    tags: ['对话', 'Prefix', 'Tools', '视觉', '256K'],
    kind: ['对话', '视觉'],
  },
  {
    id: 'MiniMaxAI/MiniMax-M2.5',
    provider: 'MiniMax',
    title: 'MiniMax-M2.5',
    description: '大语言 MoE 模型，适合智能体工具调用、对话和内容生成。',
    tags: ['对话', 'Prefix', 'Tools', 'MoE'],
    kind: ['对话', '推理'],
  },
  {
    id: 'nex-agi/Nex-N2-Pro',
    provider: 'nex-agi',
    title: 'Nex-N2-Pro',
    description: '强调自适应思考的模型，适合搜索、工具调用和深度推理任务。',
    tags: ['对话', 'Tools', '推理模型', '256K'],
    kind: ['对话', '推理'],
  },
  {
    id: 'Tongyi-MAI/Z-Image-Turbo',
    provider: 'Tongyi-MAI',
    title: 'Z-Image-Turbo',
    description: '文生图模型，适合快速生成教学插图和视觉素材。',
    tags: ['生图', '6B'],
    kind: ['生图'],
  },
  {
    id: 'Tongyi-MAI/Z-Image',
    provider: 'Tongyi-MAI',
    title: 'Z-Image',
    description: '图像生成基础模型，适合较高质量的图片生成任务。',
    tags: ['生图', '6B'],
    kind: ['生图'],
  },
]

const config = ref(loadSiliconFlowConfig())
const showKey = ref(false)
const testing = ref(false)
const message = ref('')
const isError = ref(false)
const query = ref('')
const activeKind = ref<ModelKind>('全部')
const customModel = ref(config.value.model)
const modelKinds: ModelKind[] = ['全部', '对话', '推理', '编程', '视觉', '生图']

const selectedModel = computed(() => modelCatalog.find(item => item.id === config.value.model))
const filteredModels = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  return modelCatalog.filter(item => {
    const matchesKind = activeKind.value === '全部' || item.kind.includes(activeKind.value as Exclude<ModelKind, '全部'>)
    const haystack = `${item.id} ${item.title} ${item.provider} ${item.description} ${item.tags.join(' ')}`.toLowerCase()
    return matchesKind && (!keyword || haystack.includes(keyword))
  })
})

function selectModel(model: SiliconFlowModel) {
  config.value.model = model.id
  customModel.value = model.id
  isError.value = false
  message.value = `已选择 ${model.id}`
}

function applyCustomModel() {
  const value = customModel.value.trim()
  if (!value) {
    isError.value = true
    message.value = '请输入模型标识'
    return
  }
  config.value.model = value
  isError.value = false
  message.value = `已使用自定义模型 ${value}`
}

function save() {
  applyCustomModel()
  if (isError.value) return
  saveSiliconFlowConfig(config.value)
  isError.value = false
  message.value = '配置已保存在当前浏览器中'
}

async function testConnection() {
  applyCustomModel()
  if (isError.value) return
  testing.value = true
  message.value = ''
  try {
    const result = await testSiliconFlow(config.value)
    saveSiliconFlowConfig(config.value)
    isError.value = false
    message.value = `${result.model}：${result.message}`
  } catch (error) {
    isError.value = true
    message.value = error instanceof Error ? error.message : '连接测试失败'
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <div class="model-settings-page">
    <section class="model-settings-hero">
      <div>
        <span>SILICONFLOW MODELS</span>
        <h2>硅基流动模型设置</h2>
        <p>选择一个模型用于首页对话、多 Agent 协作生成和画像对话，也可以直接填写硅基流动支持的任意模型标识。</p>
      </div>
      <div class="active-model">
        <small>当前模型</small>
        <strong>{{ config.model }}</strong>
      </div>
    </section>

    <section class="model-config-card">
      <label>
        <span>API Key</span>
        <div class="secret-input">
          <input v-model="config.api_key" :type="showKey ? 'text' : 'password'" placeholder="sk-..." />
          <button type="button" @click="showKey = !showKey">{{ showKey ? '隐藏' : '显示' }}</button>
        </div>
      </label>
      <label>
        <span>Base URL</span>
        <input v-model="config.base_url" type="url" placeholder="https://api.siliconflow.cn/v1" />
      </label>
      <label>
        <span>自定义模型标识</span>
        <div class="model-input-row">
          <input v-model="customModel" type="text" placeholder="例如 deepseek-ai/DeepSeek-V4-Pro" @change="applyCustomModel" />
          <button type="button" @click="applyCustomModel">应用</button>
        </div>
      </label>
    </section>

    <section class="model-toolbar">
      <div class="kind-tabs">
        <button
          v-for="kind in modelKinds"
          :key="kind"
          type="button"
          :class="{ active: activeKind === kind }"
          @click="activeKind = kind"
        >
          {{ kind }}
        </button>
      </div>
      <div class="model-search">
        <span>⌕</span>
        <input v-model="query" placeholder="请输入模型名称" />
      </div>
    </section>

    <section class="model-grid">
      <button
        v-for="model in filteredModels"
        :key="model.id"
        type="button"
        :class="['model-card', config.model === model.id ? 'selected' : '']"
        @click="selectModel(model)"
      >
        <i v-if="model.hot">New</i>
        <div class="model-logo">{{ model.provider.slice(0, 1).toUpperCase() }}</div>
        <div class="model-info">
          <h3>{{ model.id }}</h3>
          <b>{{ model.provider }}</b>
          <p>{{ model.description }}</p>
          <div class="model-tags">
            <span v-for="tag in model.tags" :key="tag">{{ tag }}</span>
          </div>
        </div>
      </button>
    </section>

    <section class="model-actions">
      <div>
        <strong>{{ selectedModel?.title || '自定义模型' }}</strong>
        <span>{{ selectedModel?.description || '将直接使用你输入的硅基流动模型标识。' }}</span>
      </div>
      <button class="btn-secondary" @click="save">保存设置</button>
      <button class="btn-primary" :disabled="testing" @click="testConnection">{{ testing ? '正在测试...' : '测试连接' }}</button>
    </section>

    <div v-if="message" :class="['settings-message', isError ? 'settings-message-error' : '']">{{ message }}</div>
  </div>
</template>

<style scoped>
.model-settings-page { display: grid; gap: 18px; color: #202123; }
.model-settings-hero, .model-config-card, .model-actions { border: 1px solid #ece8ff; border-radius: 18px; background: #fff; box-shadow: 0 12px 30px rgba(82, 62, 180, .07); }
.model-settings-hero { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 24px; }
.model-settings-hero span { color: #8067df; font-size: 11px; font-weight: 850; letter-spacing: .12em; }
.model-settings-hero h2 { margin: 6px 0 8px; color: #25144f; font-size: 28px; }
.model-settings-hero p { max-width: 720px; margin: 0; color: #746c84; line-height: 1.7; }
.active-model { min-width: 260px; padding: 14px; border-radius: 14px; color: #5b35c8; background: #f4f0ff; }
.active-model small, .active-model strong { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.active-model small { color: #917ee2; font-size: 11px; }
.active-model strong { margin-top: 5px; font-size: 13px; }
.model-config-card { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; padding: 18px; }
.model-config-card label { display: grid; gap: 8px; color: #5f526f; font-size: 12px; font-weight: 700; }
.model-config-card label:last-child { grid-column: 1 / -1; }
.model-config-card input { width: 100%; min-width: 0; padding: 11px 12px; border: 1px solid #e6ddff; border-radius: 12px; color: #241d35; background: #fff; outline: none; }
.model-config-card input:focus { border-color: #8b5cf6; box-shadow: 0 0 0 4px rgba(139, 92, 246, .1); }
.secret-input, .model-input-row { display: flex; align-items: center; gap: 8px; }
.secret-input button, .model-input-row button { flex: 0 0 auto; padding: 10px 12px; border: 0; border-radius: 11px; color: #5b35c8; background: #f0ebff; font-weight: 750; }
.model-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.kind-tabs { display: flex; flex-wrap: wrap; gap: 8px; }
.kind-tabs button { padding: 9px 12px; border: 1px solid #e6ddff; border-radius: 999px; color: #655875; background: #fff; }
.kind-tabs button.active { color: #fff; border-color: #7c5cff; background: #7c5cff; }
.model-search { width: min(360px, 100%); display: flex; align-items: center; gap: 9px; padding: 10px 12px; border: 1px solid #e6ddff; border-radius: 13px; background: #fff; }
.model-search span { color: #8a7cc4; }
.model-search input { width: 100%; border: 0; outline: 0; background: transparent; }
.model-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.model-card { position: relative; display: grid; grid-template-columns: 48px 1fr; gap: 14px; min-height: 174px; padding: 18px; border: 1px solid transparent; border-radius: 14px; color: #3a4050; background: #fff; text-align: left; box-shadow: 0 8px 22px rgba(31, 42, 68, .04); }
.model-card:hover, .model-card.selected { border-color: #8b63ff; box-shadow: 0 12px 30px rgba(109, 93, 242, .13); }
.model-card > i { position: absolute; top: 0; right: 0; padding: 4px 8px; border-radius: 0 14px 0 9px; color: #fff; background: #df5b55; font-style: normal; font-size: 12px; font-weight: 800; }
.model-logo { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 11px; color: #fff; background: linear-gradient(135deg, #6d5df2, #a855f7); font-weight: 900; }
.model-info h3 { margin: 0; color: #303648; font-size: 17px; line-height: 1.35; }
.model-info b { display: block; margin-top: 3px; color: #8991a3; font-size: 12px; }
.model-info p { min-height: 45px; margin: 12px 0; color: #778194; font-size: 12px; line-height: 1.65; }
.model-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.model-tags span { padding: 4px 7px; border-radius: 6px; color: #7958e8; background: #eee8ff; font-size: 11px; font-weight: 700; }
.model-actions { display: flex; align-items: center; gap: 12px; padding: 16px; }
.model-actions div { min-width: 0; flex: 1; display: grid; gap: 4px; }
.model-actions strong { color: #25144f; }
.model-actions span { color: #746c84; font-size: 12px; }
.model-actions button { padding: 10px 14px; border-radius: 11px; font-weight: 750; }
.settings-message { padding: 12px 14px; border-radius: 12px; color: #5b35c8; background: #f0ebff; }
.settings-message-error { color: #b91c1c; background: #fef2f2; }
@media (max-width: 1100px) {
  .model-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .model-settings-hero, .model-toolbar, .model-actions { align-items: stretch; flex-direction: column; }
  .active-model { min-width: 0; }
  .model-config-card, .model-grid { grid-template-columns: 1fr; }
}
</style>
