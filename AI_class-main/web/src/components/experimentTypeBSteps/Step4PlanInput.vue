<template>
  <div class="step-header">
    <experiment-outlined class="step-icon" />
    <a-typography-title :level="3" class="step-title"> 步骤 4: 生成实验计划 </a-typography-title>
  </div>

  <a-alert
    type="info"
    show-icon
    class="step-info"
    message="实验指引"
    description="基于图像描述，我们需要制定一个实验计划。请提供计划提示词来指导系统生成实验步骤。"
  />

  <a-collapse
    v-if="imageDescription"
    class="description-summary"
    :bordered="false"
    expand-icon-position="start"
    :default-active-key="['1']"
  >
    <a-collapse-panel key="1">
      <template #header>
        <div class="collapse-header"><file-text-outlined /> 图像描述摘要</div>
      </template>
      <div
        class="markdown-content"
        v-html="
          showFullDescription
            ? renderedDescription
            : md.render(
                imageDescription.substring(0, 300) + (imageDescription.length > 300 ? '...' : '')
              )
        "
      ></div>
      <a-button
        v-if="imageDescription && imageDescription.length > 300"
        @click="toggleFullDescription"
        type="link"
        size="small"
        class="toggle-btn"
      >
        {{ showFullDescription ? '收起' : '查看完整描述' }}
      </a-button>
    </a-collapse-panel>
  </a-collapse>

  <a-row :gutter="[24, 24]" class="mt-6">
    <a-col :span="24">
      <a-form layout="vertical" class="prompt-form">
        <a-form-item label="请输入计划提示词：" required class="form-label">
          <a-textarea
            v-model:value="localPlanPrompt"
            :rows="4"
            placeholder="例如：基于图像描述，请制定一个详细的实验计划，包括需要分析的关键点和推理步骤..."
            :disabled="internalIsLoading || !imageDescription"
            allow-clear
            class="prompt-textarea"
          />
        </a-form-item>

        <a-card title="提示词建议" size="small" class="prompt-suggestions">
          <template #title>
            <div class="card-title"><bulb-filled /> 提示词建议</div>
          </template>
          <a-space direction="vertical" style="width: 100%" size="middle">
            <a-tag
              color="blue"
              class="suggestion-tag"
              @click="
                useSuggestion(
                  '您是处理视觉推理任务的专家规划者。您的任务是将给出的问题分解成一个逐步的计划。以提供的图像描述作为背景信息。每个步骤都应独立完整、精确，并直接有助于回答问题。避免不必要的步骤。您无需给出最终答案。您的步骤不应超过 4 步，中文回复'
                )
              "
            >
              <bulb-outlined /> 制定详细实验计划
            </a-tag>
            <a-tag
              color="blue"
              class="suggestion-tag"
              @click="
                useSuggestion(
                  '请设计一个系统性的分析方法，逐步解决图像中的问题。您的步骤不应超过 4 步，中文回复'
                )
              "
            >
              <bulb-outlined /> 设计系统性分析方法
            </a-tag>
            <a-tag
              color="blue"
              class="suggestion-tag"
              @click="
                useSuggestion(
                  '请提供一个分步骤的实验计划，每个步骤都应该有明确目标和预期结果。您的步骤不应超过 4 步，中文回复'
                )
              "
            >
              <bulb-outlined /> 分步骤实验计划
            </a-tag>
          </a-space>
        </a-card>

        <div class="step-actions">
          <a-button
            type="primary"
            size="large"
            :loading="internalIsLoading"
            @click="generatePlan"
            :disabled="!localPlanPrompt.trim() || internalIsLoading || !imageDescription"
            class="generate-btn"
          >
            <template #icon><experiment-outlined /></template>
            {{ internalIsLoading ? '生成计划中...' : '生成实验计划' }}
          </a-button>
        </div>
      </a-form>
    </a-col>
  </a-row>

  <div class="step-status">
    <a-spin
      :spinning="internalIsLoading"
      tip="正在生成实验计划，请稍候..."
      size="large"
      class="loading-spinner"
    >
      <template #indicator>
        <loading-outlined spin class="custom-spin-icon" />
      </template>
    </a-spin>

    <a-alert v-if="apiError" type="error" show-icon class="error-message" :message="apiError" />

    <a-card v-if="stepItems.length > 0" class="step-output" :bordered="false">
      <template #title>
        <div class="card-title"><ordered-list-outlined /> 实验计划</div>
      </template>
      <a-steps
        direction="vertical"
        :current="localPlanList.length"
        :items="stepItems"
        class="plan-steps"
      />
      <div class="next-step-action">
        <a-button type="primary" size="large" @click="goToNextStep" class="next-btn">
          <template #icon><arrow-right-outlined /></template>
          前往下一步实验流程
        </a-button>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, ref, watch, computed } from 'vue'
import axios from 'axios'
import {
  ExperimentOutlined,
  BulbOutlined,
  BulbFilled,
  ArrowRightOutlined,
  FileTextOutlined,
  OrderedListOutlined,
  LoadingOutlined
} from '@ant-design/icons-vue'
import MarkdownIt from 'markdown-it'

// 创建markdown-it实例
const md = new MarkdownIt({
  html: true, // 启用HTML标签
  breaks: true, // 将\n转换为<br>
  linkify: true // 自动将URL转换为链接
})

// 添加计算属性用于渲染Markdown
const renderedDescription = computed(() => {
  if (!props.imageDescription) return ''
  return md.render(props.imageDescription)
})

const props = defineProps({
  planPrompt: { type: String, default: '' },
  imageDescription: { type: String, default: null },
  experimentData: { type: Object, default: () => null },
  isLoading: { type: Boolean, default: false },
  planList: { type: Array, default: () => [] }
})

const emits = defineEmits(['update:planPrompt', 'update:planList', 'update:isLoading', 'next'])

const localPlanPrompt = ref(props.planPrompt)
const showFullDescription = ref(false)
const internalIsLoading = ref(props.isLoading)
const localPlanList = ref(props.planList)
const apiError = ref(null)

watch(
  () => props.planPrompt,
  (newVal) => {
    localPlanPrompt.value = newVal
  }
)

watch(
  () => props.isLoading,
  (newVal) => {
    internalIsLoading.value = newVal
  }
)

watch(
  () => props.planList,
  (newVal) => {
    localPlanList.value = newVal
  }
)

watch(localPlanPrompt, (newVal) => {
  emits('update:planPrompt', newVal)
})

const stepItems = computed(() => {
  if (!Array.isArray(localPlanList.value) || localPlanList.value.length === 0) {
    return []
  }
  return localPlanList.value.map((stepText, index) => ({
    title: `步骤 ${index + 1}`,
    description: stepText
  }))
})

const toggleFullDescription = () => {
  showFullDescription.value = !showFullDescription.value
}

const useSuggestion = (suggestion) => {
  localPlanPrompt.value = suggestion
}

const generatePlan = async () => {
  if (!localPlanPrompt.value || !localPlanPrompt.value.trim()) {
    apiError.value = '请输入计划提示词！'
    return
  }
  if (!props.imageDescription) {
    apiError.value = '未获取到图像描述信息，无法生成计划！'
    return
  }

  internalIsLoading.value = true
  emits('update:isLoading', true)
  apiError.value = null
  localPlanList.value = []
  emits('update:planList', [])

  try {
    const response = await axios.post('/api/generate-plan', {
      user_question: localPlanPrompt.value,
      image_caption: props.imageDescription,
      system_prompt: null
    })
    console.log("计划是:",response.data.plan)

    if (response.data && response.data.plan && Array.isArray(response.data.plan.steps)) {
      localPlanList.value = response.data.plan.steps
      emits('update:planList', response.data.plan.steps)
    } else {
      throw new Error('后端返回的计划数据结构不正确。')
    }
  } catch (error) {
    apiError.value = `生成计划失败: ${error.response?.data?.detail || error.message || '未知错误'}`
    localPlanList.value = []
    emits('update:planList', [])
  } finally {
    internalIsLoading.value = false
    emits('update:isLoading', false)
  }
}

const goToNextStep = () => {
  if (localPlanList.value.length > 0) {
    emits('next')
  } else {
    alert('请先生成实验计划！')
  }
}
</script>

<style scoped>
.experiment-step {
  margin-bottom: 30px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.08),
    0 8px 24px rgba(0, 0, 0, 0.06);
  padding: 24px;
}

.summary-content {
  user-select: text;
}

.step-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.step-icon {
  font-size: 28px;
  color: #1890ff;
  margin-right: 12px;
}

.step-title {
  margin-bottom: 0 !important;
  font-weight: 600 !important;
  color: #262626;
}

.step-info {
  margin-bottom: 24px;
  border-radius: 8px;
  font-size: 16px;
}

.description-summary {
  margin-bottom: 24px;
  background-color: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
}

.collapse-header {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.collapse-header :deep(svg) {
  margin-right: 8px;
  font-size: 20px;
  color: #1890ff;
}

.summary-content {
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
  font-size: 16px;
  line-height: 1.8;
}

.toggle-btn {
  margin-left: 8px;
  padding: 0;
  height: auto;
}

.mt-6 {
  margin-top: 32px;
}

.prompt-form {
  padding: 4px;
}

.form-label :deep(.ant-form-item-label > label) {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.prompt-textarea {
  border-radius: 8px;
  font-size: 16px;
  resize: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  min-height: 120px;
}

.prompt-textarea:hover {
  border-color: #40a9ff;
}

.prompt-suggestions {
  margin-top: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  margin-bottom: 24px;
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.card-title :deep(svg) {
  margin-right: 8px;
  font-size: 20px;
  color: #1890ff;
}

.suggestion-tag {
  cursor: pointer;
  padding: 8px 12px;
  font-size: 14px;
  border-radius: 6px;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
}

.suggestion-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.2);
}

.suggestion-tag :deep(svg) {
  margin-right: 6px;
  font-size: 16px;
}

.step-actions {
  display: flex;
  justify-content: flex-start;
  margin-top: 24px;
}

.generate-btn,
.next-btn {
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
}

.generate-btn {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
}

.next-btn {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.generate-btn:hover,
.next-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.generate-btn:disabled,
.next-btn:disabled {
  background: #f5f5f5;
  color: rgba(0, 0, 0, 0.25);
  border-color: #d9d9d9;
  box-shadow: none;
  transform: none;
}

.step-status {
  margin-top: 32px;
}

.loading-spinner {
  display: flex;
  justify-content: center;
  margin: 40px 0;
}

.custom-spin-icon {
  font-size: 36px;
  color: #1890ff;
}

.error-message {
  margin-bottom: 24px;
  border-radius: 8px;
}

.step-output {
  background-color: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  margin-top: 24px;
}

.plan-steps {
  margin: 16px 0;
  padding: 0 16px;
}

.plan-steps :deep(.ant-steps-item-title) {
  font-weight: 600;
  font-size: 16px;
}

.plan-steps :deep(.ant-steps-item-description) {
  font-size: 15px;
  line-height: 1.8;
  color: #595959;
  padding: 8px 0;
  user-select: text;
}

.next-step-action {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

/* 覆盖一些 Ant Design 默认样式 */
:deep(.ant-collapse-header) {
  font-weight: 500;
  padding: 16px 24px !important;
}

:deep(.ant-collapse-content-box) {
  padding: 0 !important;
}

:deep(.ant-alert-message) {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

:deep(.ant-alert-description) {
  font-size: 14px;
  color: #595959;
  margin-top: 4px;
}

:deep(.ant-spin-text) {
  font-size: 14px;
  margin-top: 8px;
}

:deep(.ant-card-head) {
  min-height: 48px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.ant-card-head-title) {
  padding: 12px 0;
}

@media (max-width: 768px) {
  .step-output .ant-steps-vertical {
    padding: 0 10px;
  }

  .step-output .ant-steps-item-content {
    font-size: 14px;
  }
}

/* Markdown内容样式 */
.markdown-content {
  color: #262626;
}

/* Markdown内容样式优化 */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin-top: 16px;
  margin-bottom: 12px;
  font-weight: 600;
  line-height: 1.4;
  color: #262626;
}

.markdown-content :deep(h1) {
  font-size: 24px;
}

.markdown-content :deep(h2) {
  font-size: 22px;
}

.markdown-content :deep(h3) {
  font-size: 20px;
}

.markdown-content :deep(h4) {
  font-size: 18px;
}

.markdown-content :deep(p) {
  margin-bottom: 12px;
  line-height: 1.8;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 24px;
  margin-bottom: 16px;
}

.markdown-content :deep(li) {
  margin-bottom: 6px;
}

.markdown-content :deep(a) {
  color: #1890ff;
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(blockquote) {
  padding: 8px 16px;
  margin: 16px 0;
  border-left: 4px solid #1890ff;
  background-color: #e6f7ff;
  color: #595959;
}

.markdown-content :deep(code) {
  background-color: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 14px;
}

.markdown-content :deep(pre) {
  background-color: #f0f2f5;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 16px 0;
}

.markdown-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #e8e8e8;
  padding: 8px 12px;
  text-align: left;
}

.markdown-content :deep(th) {
  background-color: #fafafa;
  font-weight: 600;
}

.markdown-content :deep(tr:nth-child(even)) {
  background-color: #fafafa;
}
</style>
