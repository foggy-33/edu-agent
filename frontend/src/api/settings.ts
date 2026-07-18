import type { SiliconFlowConfig } from '../types/profile'

const STORAGE_KEY = 'studyflow_siliconflow_config'

export const defaultSiliconFlowConfig: SiliconFlowConfig = {
  active_provider: 'siliconflow',
  api_key: '',
  base_url: 'https://api.siliconflow.cn/v1',
  model: 'deepseek-ai/DeepSeek-V4-Pro',
  spark_api_password: '',
  spark_base_url: '',
  spark_model: ''
}

export function loadSiliconFlowConfig(): SiliconFlowConfig {
  try {
    const stored = { ...defaultSiliconFlowConfig, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') }
    return { ...stored, api_key: '', spark_api_password: '', spark_base_url: '' }
  } catch {
    return { ...defaultSiliconFlowConfig }
  }
}

export function saveSiliconFlowConfig(config: SiliconFlowConfig) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    ...config,
    api_key: '',
    spark_api_password: '',
    spark_base_url: '',
    spark_model: config.spark_model,
  }))
}
