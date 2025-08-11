<template>
  <div class="step-header">
    <experiment-outlined class="step-icon" />
    <a-typography-title :level="3" class="step-title"> 步骤 7: 评估模型答案 </a-typography-title>
  </div>

  <a-alert
    v-if="!finalAnswer || !correctAnswer"
    message="请确保已完成前面的步骤，特别是步骤6已获取最终答案，并且实验数据包含正确答案以供比较。"
    type="info"
    show-icon
    class="step-info"
  />

  <a-card class="description-summary" :bordered="false" :title="'答案对比'">
    <template #title>
      <div class="card-title"><file-text-outlined /> 答案对比</div>
    </template>
    <a-descriptions bordered :column="1" class="answer-comparison">
      <a-descriptions-item label="模型给出的最终答案 (来自步骤 6)">
        <a-typography-text strong class="model-answer-text">
          {{ displayAnswer || '未获取到模型答案' }}
        </a-typography-text>
      </a-descriptions-item>

      <a-descriptions-item v-if="parsedAnswerContent?.explanation" label="模型给出的解释">
        <a-typography-paragraph strong copyable class="model-answer-text">
          {{ displayExplanation }}
        </a-typography-paragraph>
      </a-descriptions-item>
      <a-descriptions-item label="标准参考答案">
        <a-typography-text strong>
          {{ correctAnswer || '未提供标准答案' }}
        </a-typography-text>
      </a-descriptions-item>
    </a-descriptions>
  </a-card>

  <div class="step-actions mt-6">
    <a-button
      type="primary"
      size="large"
      @click="handleEvaluateAnswer"
      :disabled="!finalAnswer || !correctAnswer || internalIsLoading"
      :loading="internalIsLoading"
      class="generate-btn"
      aria-label="获取AI评估结果"
    >
      <template #icon><experiment-outlined /></template>
      {{ internalIsLoading ? '评估中...' : '获取 AI 评估结果' }}
    </a-button>
  </div>

  <div class="step-status">
    <a-spin
      :spinning="internalIsLoading && !apiError"
      tip="正在进行AI评估，请稍候..."
      size="large"
      class="loading-spinner"
    >
      <template #indicator>
        <loading-outlined spin class="custom-spin-icon" />
      </template>
    </a-spin>

    <a-alert v-if="apiError" type="error" show-icon class="error-message" :message="apiError" />
  </div>

  <a-card v-if="localEvaluation" class="step-output mt-6" :bordered="false">
    <template #title>
      <div class="card-title"><ordered-list-outlined /> AI 评估结果</div>
    </template>
    <a-descriptions bordered :column="1">
      <a-descriptions-item label="评估分数 (0-100)">
        <a-typography-text strong>{{ localEvaluation.score }}</a-typography-text>
      </a-descriptions-item>
      <a-descriptions-item label="评估理由">
        <a-typography-paragraph strong copyable>
          {{ localEvaluation.justification }}
        </a-typography-paragraph>
      </a-descriptions-item>
    </a-descriptions>
  </a-card>

  <div class="step-actions mt-6 justify-end">
    <a-button
      type="primary"
      size="large"
      @click="$emit('next')"
      class="next-btn"
      aria-label="前往实验总结"
      :disabled="props.isLoading || !localEvaluation"
    >
      <template #icon><arrow-right-outlined /></template>
      前往实验总结
    </a-button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import {
  Card as ACard,
  Descriptions as ADescriptions,
  DescriptionsItem as ADescriptionsItem,
  TypographyText as ATypographyText,
  TypographyParagraph as ATypographyParagraph,
  Tag as ATag,
  Button as AButton,
  Alert as AAlert,
  message
} from 'ant-design-vue'
import {
  ExperimentOutlined,
  ArrowRightOutlined,
  FileTextOutlined,
  OrderedListOutlined,
  LoadingOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  finalAnswer: {
    // From Step 6 (model's answer), might be JSON string format
    type: String,
    default: null
  },
  modelexplanation: {
    // From Step 6 (model's answer), might be JSON string format
    type: String,
    default: null
  },
  experimentData: {
    // Contains correct answer and other experiment details
    type: Object,
    default: () => ({ quizQuestions: [{ explanation: '' }] })
  },
  isLoading: {
    // Controlled by parent
    type: Boolean,
    default: false
  }
})

const emits = defineEmits(['next', 'update:isLoading', 'update:evaluationResult', 'update:score'])

const internalIsLoading = ref(false)
const apiError = ref(null)
const localEvaluation = ref(null) // To store { score, justification }

watch(
  () => props.isLoading,
  (newVal) => {
    if (internalIsLoading.value !== newVal) {
      // Sync only if parent changes it
      internalIsLoading.value = newVal
    }
  }
)

// Computed property to parse the finalAnswer string and extract answer/explanation
const parsedAnswerContent = computed(() => {
  const rawAnswer = props.finalAnswer
  const expla = props.modelexplanation // 获取 props.modelExplanations 作为解释

  console.log('原始答案 (rawAnswer) 是:', rawAnswer)
  console.log('外部解释 (expla) 是:', expla)

  let answerToReturn = '未获取' // 默认答案
  let explanationToReturn = expla // 默认解释就是 props.modelExplanations

  // 尝试从 rawAnswer 中解析 JSON 结构
  if (rawAnswer && typeof rawAnswer === 'string') {
    const jsonMatch = rawAnswer.match(/```json\s*([\s\S]*?)\s*```/)

    if (jsonMatch && jsonMatch[1]) {
      try {
        const parsed = JSON.parse(jsonMatch[1])
        if (typeof parsed === 'object' && parsed !== null) {
          // 如果 JSON 中有 answer 字段，则使用它
          if (typeof parsed.answer === 'string') {
            answerToReturn = parsed.answer
          } else {
            // 如果 JSON 中没有 answer，但 JSON 存在，就使用整个原始答案
            answerToReturn = rawAnswer
          }
          // 如果 JSON 中有 explanation 字段，且外部 expla 未提供，则使用 JSON 中的
          // 否则，优先使用外部 expla
          if (!explanationToReturn && typeof parsed.explanation === 'string') {
            explanationToReturn = parsed.explanation
          }
        }
      } catch (e) {
        console.error('Failed to parse finalAnswer JSON:', e)
        // 如果解析失败，回退到使用原始答案
        answerToReturn = rawAnswer
      }
    } else {
      // 如果没有找到 ```json``` 块，则将整个 rawAnswer 作为答案
      answerToReturn = rawAnswer
    }
  }

  // 如果最终答案仍然是 '未获取' 且 rawAnswer 不为空，则用 rawAnswer
  if (answerToReturn === '未获取' && rawAnswer) {
    answerToReturn = rawAnswer
  }
  // 确保如果 expla 传入的是 null，仍然返回 null，而不是 '未提供' 等字符串
  if (explanationToReturn === undefined || explanationToReturn === '') {
    explanationToReturn = null
  }

  return {
    answer: answerToReturn,
    explanation: explanationToReturn
  }
})

// Computed property for the string to display as the model's answer
const displayAnswer = computed(() => {
  return parsedAnswerContent.value?.answer ?? props.finalAnswer ?? '未获取到模型答案'
})

// Computed property for the string to display as the model's explanation
const displayExplanation = computed(() => {
  return parsedAnswerContent.value?.explanation || '未提供解释'
})

// Computed property for the string used in comparison logic and sent to API
const answerForComparisonAndAPI = computed(() => {
  const answer = parsedAnswerContent.value?.answer ?? props.finalAnswer
  const explanation = parsedAnswerContent.value?.explanation // 获取解释

  let combinedString = answer

  if (explanation) {
    combinedString += '\n\n解释：' + explanation
  }

  return combinedString
})

const correctAnswer = computed(() => {
  return props.experimentData?.quizQuestions?.[0]?.explanation || null
})

// Updated to use answerForComparisonAndAPI
const getAnswerMatchType = (modelAns, correctAns) => {
  if (!modelAns || !correctAns) return 'secondary'
  // Ensure comparison is also on the correct string
  return String(modelAns).trim().toLowerCase() === String(correctAns).trim().toLowerCase()
    ? 'success'
    : 'danger'
}

// Updated to use answerForComparisonAndAPI
const getAnswerMatchColor = (modelAns, correctAns) => {
  if (!modelAns || !correctAns) return 'default'
  // Ensure comparison is also on the correct string
  return String(modelAns).trim().toLowerCase() === String(correctAns).trim().toLowerCase()
    ? 'green'
    : 'red'
}

// Updated to use answerForComparisonAndAPI
const getAnswerMatchText = (modelAns, correctAns) => {
  if (!modelAns || !correctAns) return '信息不全'
  // Ensure comparison is also on the correct string
  return String(modelAns).trim().toLowerCase() === String(correctAns).trim().toLowerCase()
    ? '匹配一致'
    : '不匹配'
}

const handleEvaluateAnswer = async () => {
  // Use answerForComparisonAndAPI for evaluation check and payload
  if (!answerForComparisonAndAPI.value || !correctAnswer.value) {
    message.warn('模型答案或标准答案缺失，无法进行评估。')
    return
  }

  internalIsLoading.value = true
  emits('update:isLoading', true)
  apiError.value = null
  localEvaluation.value = null

  try {
    const response = await axios.post('/api/evaluate-response', {
      predicted: answerForComparisonAndAPI.value, // Send the string for comparison/evaluation
      groundtruth: correctAnswer.value
    })
    if (response.data && typeof response.data.score !== 'undefined') {
      localEvaluation.value = response.data
      emits('update:evaluationResult', response.data)
      console.log('分数是：', response.data.score)
      emits('update:score', response.data.score)
      message.success('AI评估完成！')
    } else {
      throw new Error('AI评估返回数据格式不正确。')
    }
  } catch (error) {
    console.error('调用评估API时出错:', error)
    apiError.value = `AI评估失败: ${error.response?.data?.detail || error.message || '未知错误'}`
    message.error(apiError.value)
    emits('update:evaluationResult', null) // Clear previous result on error
  } finally {
    internalIsLoading.value = false
    emits('update:isLoading', false)
  }
}
</script>

<style scoped>
/* Import or duplicate the styles from the previous component */
/* It's recommended to extract common styles into a shared CSS file */

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
  font-size: 16px;
}

/* Reusing description-summary class for the answer comparison card */
.description-summary {
  margin-bottom: 24px;
  background-color: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
  user-select: text;
  /* Adjust padding for the card body if needed, default Ant Card padding might be okay */
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
  /* Consistent icon color */
}

/* Specific styles for the descriptions within the card */
.answer-comparison :deep(.ant-descriptions-header) {
  padding: 0px 0px 16px !important;
  /* Adjust padding if needed */
  margin-bottom: 16px;
  /* Space below header */
}

/* Consistent margin classes */
.mt-4 {
  margin-top: 16px;
}

.mt-6 {
  margin-top: 32px;
}

.mb-4 {
  margin-bottom: 16px;
}

.mb-6 {
  margin-bottom: 32px;
}

.ml-4 {
  margin-left: 16px;
}

/* Step actions container */
.step-actions {
  display: flex;
  justify-content: flex-start;
  /* Default for generate button */
  margin-top: 24px;
}

.step-actions.justify-end {
  justify-content: flex-end;
  /* For the next button */
}

/* Button styles */
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

/* Status section */
.step-status {
  margin-top: 32px;
  /* Added margin for consistency */
  display: flex;
  flex-direction: column;
  align-items: center;
  /* Center spinner and error */
}

.loading-spinner {
  /* display: flex; Removed as step-status is flex column now */
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
  width: 100%;
  /* Make alert take full width */
}

/* AI Evaluation Output Card */
.step-output {
  background-color: #fff;
  /* Card background */
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  /* margin-top is handled by the element itself (mt-6) */
}

/* Ant Design Overrides (copied from Step 4 and adjusted) */
:deep(.ant-card-head) {
  min-height: 48px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.ant-card-head-title) {
  padding: 12px 0;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 600;
  /* Labels bold */
  color: #595959;
  /* Label color */
}

:deep(.ant-descriptions-item-content) {
  font-size: 15px;
  /* Content font size */
  line-height: 1.8;
  /* Content line height */
  color: #262626;
  /* Content color */
}

:deep(.ant-descriptions-bordered .ant-descriptions-item-label) {
  background-color: #f5f7fa;
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

/* Custom style for model answer text (always black) */
.model-answer-text {
  color: #262626 !important;
  /* Ensure black color */
}

/* Custom style for model explanation text - Removed italic */
.model-explanation-text {
  color: #595959;
  /* A slightly lighter color for explanation */
  /* font-style: italic; Removed */
}

@media (max-width: 768px) {
  /* Add any responsive styles needed for this specific page if different from common styles */
}
</style>
