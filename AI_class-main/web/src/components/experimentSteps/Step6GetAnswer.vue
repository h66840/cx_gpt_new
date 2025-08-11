<template>
  <div class="step-header">
    <experiment-outlined class="step-icon" />
    <a-typography-title :level="3" class="step-title">
      步骤6: 根据推理总结选择答案
    </a-typography-title>
  </div>

  <a-alert
    type="info"
    show-icon
    class="step-info"
    message="实验指引"
    description="在这一步，我们将基于已生成的推理总结（通常来自上一步的计划执行结果），结合提供的问题和选项，来选择最合适的答案。"
  />

  <div
    v-if="
      !detailedInfo ||
      !experimentData?.quizQuestions?.[0]?.question ||
      !experimentData?.quizQuestions?.[0]?.options?.length
    "
    class="mb-4"
  >
    <a-alert
      message="请确保已完成前面的步骤，特别是推理总结已生成，并且实验数据包含问题和选项。"
      type="warning"
      show-icon
    />
  </div>

  <div class="step-output mt-6">
    <div class="section-title"><file-text-outlined /> 推理总结</div>
    <a-spin :spinning="internalIsLoading && !parsedStepsForDisplay.length">
      <a-collapse v-model:activeKey="activeKey" accordion class="steps-collapse">
        <a-collapse-panel
          v-for="stepItem in parsedStepsForDisplay"
          :key="stepItem.key"
          :header="stepItem.title"
          class="step-panel"
        >
          <div
            v-if="stepItem.htmlContent"
            v-html="stepItem.htmlContent"
            class="step-content-html"
          ></div>
          <div v-else class="step-content-raw">
            <pre>{{ stepItem.rawContent }}</pre>
          </div>
        </a-collapse-panel>
        <a-collapse-panel
          v-if="parsedStepsForDisplay.length === 0 && formattedDetailedInfo !== '无推理总结'"
          key="raw-fallback"
          header="原始推理总结 (未解析到步骤)"
          :disabled="false"
          class="step-panel"
        >
          <pre style="white-space: pre-wrap; word-wrap: break-word">{{
            formattedDetailedInfo
          }}</pre>
        </a-collapse-panel>
        <a-collapse-panel
          v-if="parsedStepsForDisplay.length === 0 && formattedDetailedInfo === '无推理总结'"
          key="no-content-fallback"
          header="无推理总结"
          :disabled="true"
          class="step-panel"
        >
          <p>{{ formattedDetailedInfo }}</p>
        </a-collapse-panel>
      </a-collapse>
    </a-spin>

    <div>
      <a-button type="primary" @click="handleOpen(true)" class="mt-4 mb-4">问题预览</a-button>
      <a-divider />
      <a-space>
        <a-button ref="ref1">图片</a-button>
        <a-button ref="ref2">问题</a-button>
        <a-button ref="ref3"> <EllipsisOutlined />选项 </a-button>
      </a-space>
      <a-tour
        :open="open"
        :mask="false"
        type="primary"
        :steps="tourSteps"
        @close="handleOpen(false)"
      />
    </div>

    <a-button
      type="primary"
      @click="handleDecideAnswer"
      :disabled="
        !detailedInfo ||
        !experimentData?.quizQuestions?.[0]?.question ||
        !experimentData?.quizQuestions?.[0]?.options?.length ||
        internalIsLoading
      "
      :loading="internalIsLoading"
      class="action-btn mt-6"
      aria-label="获取答案"
    >
      <template #icon><play-circle-outlined /></template>
      {{ internalIsLoading ? '获取中...' : '获取答案' }}
    </a-button>

    <div v-if="apiError" class="error-message mt-4">
      <a-alert type="error" :message="apiError" show-icon />
    </div>

    <div v-if="modelAnswer || (internalIsLoading && !modelAnswer)" class="step-output mt-6">
      <div class="section-title"><check-circle-outlined /> 最终答案及解释</div>
      <a-spin :spinning="internalIsLoading && !modelAnswer">
        <div v-if="!internalIsLoading && modelAnswer">
          <a-typography-paragraph strong copyable class="answer-text">
            <strong>答案:</strong> {{ cleanedModelAnswer }}
          </a-typography-paragraph>
          <div v-if="modelExplanation" class="mt-4">
            <a-typography-paragraph copyable class="explanation-text">
              <strong>解释:</strong>
              <div v-html="modelExplanationHtml" class="step-content-html"></div>
            </a-typography-paragraph>
          </div>
        </div>
        <div v-else-if="!internalIsLoading && !modelAnswer && hasAttemptedDecision">
          <a-empty description="未能获取最终答案或答案为空" />
        </div>
      </a-spin>
    </div>

    <div class="next-step-action mt-6">
      <a-button
        type="primary"
        @click="$emit('next')"
        :disabled="!modelAnswer || internalIsLoading"
        class="next-btn"
        aria-label="前往下一步实验流程"
      >
        <template #icon><arrow-right-outlined /></template>
        前往下一步实验流程
      </a-button>
    </div>
  </div>
</template>

<script setup>
// ... (script setup code remains the same as the previous response)
import { ref, watch, computed, createVNode } from 'vue'
import {
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  RadioGroup as ARadioGroup,
  Radio as ARadio,
  Button as AButton,
  Spin as ASpin,
  Alert as AAlert,
  Empty as AEmpty,
  Typography,
  TypographyParagraph as ATypographyParagraph,
  Collapse as ACollapse,
  CollapsePanel as ACollapsePanel,
  message,
  Divider as ADivider, // Added for tour section
  Space as ASpace, // Added for tour section
  Tour as ATour // Added for tour section
} from 'ant-design-vue'
import {
  ExperimentOutlined,
  FileTextOutlined,
  PlayCircleOutlined,
  ArrowRightOutlined,
  CheckCircleOutlined,
  EllipsisOutlined // For tour
} from '@ant-design/icons-vue'
import { marked } from 'marked' // Import marked

const ATypographyTitle = Typography.Title

const props = defineProps({
  detailedInfo: {
    type: [Object, String, null],
    default: null
  },
  experimentData: {
    type: Object,
    default: () => ({ quizQuestions: [{ question: '', options: [] }] })
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  modelAnswer: {
    type: String,
    default: null
  },
  modelExplanation: {
    type: String,
    default: null
  },
  itemData: {
    // Preserved from your script
    type: Object,
    default: () => null
  }
})

const emits = defineEmits([
  'update:modelAnswer',
  'update:modelExplanation',
  'next',
  'update:isLoading'
])

/**
 * Removes specific leading and trailing markers (like '''json, ```json, ''' , ```)
 * from a string and trims whitespace.
 * Uses regex for flexibility.
 * @param {string | null | undefined} str The input string.
 * @returns {string | null} The cleaned string, or null if input is null/undefined.
 */
function cleanJsonStringWrapper(str) {
  if (typeof str !== 'string') {
    return str // Return null or non-string as is
  }

  // Regex to match the full wrapped string and capture the inner content.
  // Handles:
  // - Start: '''json OR ```json
  // - End:   ''' OR ```
  // - Allows optional whitespace after the start marker and before the end marker.
  // - Captures the content in between (([\s\S]*?)). [\s\S] matches any character including newline.
  // - The 's' flag makes the dot (.) match newline characters if we used .*?, but [\s\S] is explicit.
  // - (?:...) creates non-capturing groups for the markers, we only want the content captured.
  const wrappedJsonRegex = /^(?:'''json|```json)\s*([\s\S]*?)\s*(?:'''|```)$/s

  const match = str.match(wrappedJsonRegex)

  if (match && match[1] !== undefined) {
    // If the string matches the pattern, return the captured content (Group 1)
    // We trim the captured content just in case there's lingering whitespace right inside the markers.
    return match[1].trim()
  } else {
    // If the string does NOT match the specific wrapped pattern,
    // return the original string trimmed. This handles cases
    // where the API might return a plain string like "光环" or "无推理总结",
    // or other unexpected formats.
    return str.trim()
  }
}
const cleanedModelAnswer = computed(() => {
  return cleanJsonStringWrapper(props.modelAnswer)
})
// --- Tour Logic ---
const open = ref(false)
const ref1 = ref(null) // Ref for Image button
const ref2 = ref(null) // Ref for Question button
const ref3 = ref(null) // Ref for Options button

const selectedImage = computed(() => {
  if (props.itemData && props.itemData.image_path) {
    return {
      path: props.itemData.image_path,
      description: props.itemData.image_description || '实验图片'
    }
  }
  return null
})

const currentQuestion = computed(() => props.experimentData?.quizQuestions?.[0]?.question || '')
const currentOptions = computed(() => props.experimentData?.quizQuestions?.[0]?.options || [])

const tourSteps = computed(() => [
  {
    title: '关联图片',
    description: selectedImage.value
      ? createVNode('div', {}, [
          createVNode('p', {}, '实验关联图片：'),
          // Basic styling for the image in the tour step
          createVNode('img', {
            src: selectedImage.value.path,
            alt: selectedImage.value.description,
            style: {
              maxWidth: '200px',
              maxHeight: '200px',
              marginTop: '8px',
              border: '1px solid #eee'
            }
          })
        ])
      : createVNode('p', {}, '无关联图片'),
    target: () => ref1.value && ref1.value.$el
  },
  {
    title: '当前问题',
    description: currentQuestion.value
      ? createVNode('div', {}, [
          createVNode('p', {}, '问题：'),
          createVNode('p', { style: { fontWeight: 'bold' } }, currentQuestion.value)
        ])
      : createVNode('p', {}, '无问题'),
    target: () => ref2.value && ref2.value.$el
  },
  {
    title: '所有选项',
    description:
      currentOptions.value.length > 0
        ? createVNode('div', {}, [
            createVNode('p', {}, '选项列表：'),
            createVNode(
              'ul',
              { style: { paddingLeft: '20px' } },
              currentOptions.value.map((option, index) =>
                createVNode('li', { key: index, style: { marginBottom: '4px' } }, option)
              )
            )
          ])
        : createVNode('p', {}, '无选项'),
    target: () => ref3.value && ref3.value.$el
  }
])

const handleOpen = (val) => {
  open.value = val
}
// --- End of Tour Logic ---

const internalIsLoading = ref(props.isLoading)
const apiError = ref(null)
const hasAttemptedDecision = ref(false)
const activeKey = ref([])

watch(
  () => props.isLoading,
  (newVal) => {
    internalIsLoading.value = newVal
  }
)

const formattedDetailedInfo = computed(() => {
  if (!props.detailedInfo) return '无推理总结'
  if (typeof props.detailedInfo === 'string') return props.detailedInfo
  return JSON.stringify(props.detailedInfo, null, 2)
})

// Updated extractSteps to match the refined version
function extractIndividualSteps(resultText) {
  if (!resultText || typeof resultText !== 'string' || resultText === '无推理总结') {
    return []
  }
  // Regex to find "Step:" or "Step X:", then capture content.
  // This version is slightly different to be more robust for content after "Step X:"
  const stepRegex = /步骤(?: \d*)?:\s*([\s\S]*?)(?=步骤(?: \d*)?:|$)/gs
  const matches = Array.from(resultText.matchAll(stepRegex))

  if (!matches || matches.length === 0) {
    return []
  }
  return matches.map((match) => match[1].trim()) // match[1] is the content after "Step X: "
}

const parsedStepsForDisplay = computed(() => {
  const rawSteps = extractIndividualSteps(formattedDetailedInfo.value)
  if (rawSteps.length === 0) return []

  return rawSteps.map((stepContent, index) => {
    let htmlContent = ''
    let isMarkdown = true
    try {
      if (
        (stepContent.startsWith('{') && stepContent.endsWith('}')) ||
        (stepContent.startsWith('[') && stepContent.endsWith(']'))
      ) {
        isMarkdown = false // Don't parse JSON-like strings as Markdown
      }

      if (isMarkdown) {
        htmlContent = marked(stepContent)
      }
    } catch (e) {
      console.error(`Error parsing Markdown for step ${index + 1}:`, e)
      htmlContent = ''
      isMarkdown = false
    }
    return {
      key: String(index + 1),
      title: `步骤 ${index + 1}`,
      htmlContent: isMarkdown ? htmlContent : null,
      rawContent: stepContent
    }
  })
})

watch(
  parsedStepsForDisplay,
  (newSteps) => {
    if (newSteps && newSteps.length > 0) {
      if (
        activeKey.value.length === 0 ||
        !newSteps.find((step) => activeKey.value.includes(step.key))
      ) {
        activeKey.value = [newSteps[0].key]
      }
    } else {
      activeKey.value = []
    }
  },
  { immediate: true, deep: true }
)

const modelExplanationHtml = computed(() => {
  if (!props.modelExplanation) return ''
  try {
    return marked(props.modelExplanation)
  } catch (e) {
    console.error('Error parsing modelExplanation as Markdown:', e)
    return `<pre>${props.modelExplanation}</pre>`
  }
})
const handleDecideAnswer = async () => {
  if (
    // detailedInfo 仍然是必须的，因为它是 parsedStepsForDisplay 的来源
    !props.detailedInfo ||
    !props.experimentData?.quizQuestions?.[0]?.question ||
    !props.experimentData?.quizQuestions?.[0]?.options?.length
  ) {
    message.warn('必要数据缺失，无法获取答案。')
    return
  }
  emits('update:isLoading', true)
  internalIsLoading.value = true
  apiError.value = null
  hasAttemptedDecision.value = true

  let reasoningSummaryForAPI = ''

  if (parsedStepsForDisplay.value && parsedStepsForDisplay.value.length > 0) {
    // 获取解析后步骤的最后一个
    reasoningSummaryForAPI =
      parsedStepsForDisplay.value[parsedStepsForDisplay.value.length - 1].rawContent
  } else if (props.detailedInfo) {
    console.warn('未能从 detailedInfo 解析出独立步骤，将使用完整的 detailedInfo 作为推理总结。')
    reasoningSummaryForAPI =
      typeof props.detailedInfo === 'string'
        ? props.detailedInfo
        : JSON.stringify(props.detailedInfo)
  }

  try {
    const API_URL = '/api/decide-answer'
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reasoning_summary: reasoningSummaryForAPI,
        question: currentQuestion.value,
        options: currentOptions.value
      })
    })
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: '获取答案失败' }))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    if (data.result) {
      if (typeof data.result === 'object' && data.result.answer) {
        emits('update:modelAnswer', data.result.answer)
        if (data.result.explanation) {
          emits('update:modelExplanation', data.result.explanation)
        }
      } else {
        emits('update:modelAnswer', data.result) // 如果 result 直接是答案字符串
      }
      message.success('最终答案获取成功！')
    } else {
      if (data.hasOwnProperty('result')) {
        // 确保 result 字段存在
        emits('update:modelAnswer', null)
        emits('update:modelExplanation', null)
        message.info('模型未能提供答案。')
      } else {
        throw new Error('返回的答案格式不正确或为空。')
      }
    }
  } catch (error) {
    console.error('获取答案时出错:', error)
    apiError.value = error.message || '获取答案时发生未知错误。'
    message.error(apiError.value)
    emits('update:modelAnswer', null)
    emits('update:modelExplanation', null)
  } finally {
    emits('update:isLoading', false)
    internalIsLoading.value = false
  }
}
</script>

<style scoped>
/* Paste the comprehensive styles from the previous advanced version here */
.experiment-step {
  margin-bottom: 30px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.08),
    0 8px 24px rgba(0, 0, 0, 0.06);
  padding: 24px;
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
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.section-title :deep(svg) {
  margin-right: 8px;
  font-size: 20px;
  color: #1890ff;
}

.steps-collapse {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #f0f0f0;
  user-select: text;
}

.step-panel :deep(.ant-collapse-header) {
  font-weight: 500;
  background-color: #f0f5ff;
}

.step-panel :deep(.ant-collapse-content-box) {
  padding: 16px;
  background-color: #fff;
}

.step-content-raw pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: #f7f7f7;
  padding: 10px;
  border-radius: 4px;
  margin: 0;
  /* override default pre margin */
  font-family: inherit;
  font-size: inherit;
}

.mb-4 {
  margin-bottom: 16px !important;
}

.mt-4 {
  margin-top: 16px !important;
}

.mt-6 {
  margin-top: 24px !important;
}

.ml-4 {
  margin-left: 16px !important;
}

/* Added margin-bottom to the 问题预览 button */
.mb-4 {
  margin-bottom: 16px !important;
}

.error-message {
  margin-top: 16px;
}

.step-output {
  margin-top: 24px;
  background-color: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  padding: 20px;
}

.answer-text,
.explanation-text {
  background-color: #f7f9fc;
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 1em;
  border: 1px solid #e8e8e8;
  user-select: text;
}

.answer-text strong,
.explanation-text strong {
  display: block;
  margin-bottom: 8px;
  font-size: 1.05em;
  color: #333;
}

.action-btn,
.next-btn {
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  padding: 0 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  border: none;
}

.action-btn :deep(svg),
.next-btn :deep(svg) {
  margin-right: 8px;
}

.action-btn {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: white;
}

.action-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #40a9ff 0%, #1890ff 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.next-btn {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  color: white;
}

.next-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #73d13d 0%, #52c41a 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn:disabled,
.next-btn:disabled {
  background: #f5f5f5;
  color: rgba(0, 0, 0, 0.25);
  /* border-color: #d9d9d9 !important; Ant Button handles its own disabled border */
  box-shadow: none;
  transform: none;
  cursor: not-allowed;
}

.next-step-action {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

.ant-radio-group {
  display: flex;
  flex-direction: column;
}

.ant-radio-wrapper {
  margin-bottom: 8px;
}

.ant-spin-container {
  width: 100%;
}

.step-content-html :deep(h1),
.step-content-html :deep(h2),
.step-content-html :deep(h3),
.step-content-html :deep(h4),
.step-content-html :deep(h5),
.step-content-html :deep(h6) {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.3;
}

.step-content-html :deep(h1) {
  font-size: 1.8em;
}

.step-content-html :deep(h2) {
  font-size: 1.6em;
}

.step-content-html :deep(h3) {
  font-size: 1.4em;
}

.step-content-html :deep(p) {
  margin-bottom: 1em;
  line-height: 1.7;
  color: #333;
}

.step-content-html :deep(ul),
.step-content-html :deep(ol) {
  margin-bottom: 1em;
  padding-left: 2em;
}

.step-content-html :deep(li) {
  margin-bottom: 0.5em;
  line-height: 1.7;
}

.step-content-html :deep(pre) {
  background-color: #f0f8ff;
  padding: 12px;
  border-radius: 6px;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
  border: 1px solid #d9eaff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.step-content-html :deep(code) {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  background-color: #e6f7ff;
  padding: 0.2em 0.5em;
  border-radius: 4px;
  font-size: 0.9em;
}

.step-content-html :deep(pre code) {
  background-color: transparent;
  padding: 0;
  font-size: 0.95em;
  border: none;
  box-shadow: none;
}

.step-content-html :deep(blockquote) {
  border-left: 5px solid #add8e6;
  padding: 10px 15px;
  margin-left: 0;
  margin-bottom: 1em;
  color: #4a4a4a;
  background-color: #f0f8ff;
  border-radius: 0 4px 4px 0;
}

.step-content-html :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 1em;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.step-content-html :deep(th),
.step-content-html :deep(td) {
  border: 1px solid #cce7ff;
  padding: 10px 12px;
  text-align: left;
}

.step-content-html :deep(th) {
  background-color: #e6f7ff;
  font-weight: 600;
}

:deep(.ant-alert-message) {
  font-weight: 600;
}

:deep(.ant-spin-text) {
  font-size: 14px;
  margin-top: 8px;
}
</style>
