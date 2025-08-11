<template>
  <div class="experiment-execution-page">
    <!-- 优化后的顶部导航 -->
    <div class="top-nav">
      <div class="nav-left">
        <a-button type="link" @click="goBack" class="back-link">
          <left-outlined />
          返回实验详情
        </a-button>
      </div>
      <div class="nav-breadcrumb">
        <a-breadcrumb separator=">">
          <a-breadcrumb-item>
            <home-outlined />
          </a-breadcrumb-item>
          <a-breadcrumb-item v-if="experimentData?.question">
            {{ experimentData.question }}
          </a-breadcrumb-item>
          <a-breadcrumb-item> <experiment-outlined /> 实验执行时间线 </a-breadcrumb-item>
        </a-breadcrumb>
      </div>
    </div>

    <div v-if="isLoadingData" class="loading-container">
      <a-spin tip="加载实验数据中..."></a-spin>
    </div>
    <div v-else-if="dataError" class="error-message">{{ dataError }}</div>

    <div v-else-if="experimentData" class="execution-container">
      <!-- 优化后的时间线区域 -->
      <div class="timeline-area">
        <div class="timeline">
          <div
            v-for="(stepInfo, index) in timelineSteps"
            :key="stepInfo.step"
            class="timeline-step-wrapper"
          >
            <div
              :class="[
                'timeline-node',
                {
                  active: currentStep === stepInfo.step,
                  completed: currentStep > stepInfo.step,
                  disabled: currentStep < stepInfo.step
                }
              ]"
              @click="goToStep(stepInfo.step)"
            >
              <div class="node-dot">
                <check-circle-filled v-if="currentStep > stepInfo.step" />
                <span v-else>{{ stepInfo.step }}</span>
              </div>
              <div class="node-label">{{ stepInfo.label }}</div>
            </div>
            <!-- 修改后的箭头，根据步骤状态显示不同颜色 -->
            <div
              v-if="index < timelineSteps.length - 1"
              :class="[
                'step-arrow-container',
                {
                  'arrow-gray': currentStep <= stepInfo.step,
                  'arrow-blue': currentStep === stepInfo.step + 1,
                  'arrow-green': currentStep > stepInfo.step + 1
                }
              ]"
            >
              <div class="step-arrow-line"></div>
              <right-outlined class="step-arrow-icon" />
            </div>
          </div>
        </div>
      </div>

      <div class="step-content-area">
        <div v-if="currentStep === 1" class="experiment-step">
          <div class="step-header">
            <experiment-outlined class="step-icon" />
            <a-typography-title :level="3" class="step-title">
              步骤 1: 完成基础知识测试
            </a-typography-title>
          </div>

          <a-alert
            type="info"
            show-icon
            class="step-info"
            message="实验指引"
            description="实验背景信息，本次实验将引导你通过一系列步骤来分析图片并回答问题"
          />
          <a-typography-title :level="4" class="section-title">
            <ordered-list-outlined class="section-icon" />
            请回答以下问题:
          </a-typography-title>
          <div class="quiz-list">
            <div
              v-for="(quizItem, qIndex) in experimentData.quizQuestions"
              :key="quizItem.id"
              class="quiz-item"
            >
              <p>
                <strong>问题 {{ qIndex + 1 }}:</strong> {{ quizItem.question }}
              </p>
              <div v-if="quizItem.image_1?.path" class="quiz-image-container">
                <img
                  :src="quizItem.image_1.path"
                  :alt="'Quiz ' + (qIndex + 1) + ': ' + quizItem.question"
                  class="quiz-image"
                />
              </div>
              <div v-if="quizItem.options?.length">
                <p><strong>选项:</strong></p>
                <ul>
                  <li v-for="(option, oIndex) in quizItem.options" :key="oIndex">
                    <input
                      type="radio"
                      :id="'q' + qIndex + 'option' + oIndex"
                      :name="'quiz-q' + qIndex"
                      :value="String.fromCharCode(65 + oIndex)"
                      v-model="userQuizAnswers[quizItem.id]"
                    />
                    <label :for="'q' + qIndex + 'option' + oIndex">
                      {{ String.fromCharCode(65 + oIndex) }}. {{ option }}
                    </label>
                  </li>
                </ul>
              </div>
            </div>
          </div>
          <a-button
            type="primary"
            @click="submitQuizAnswers"
            :disabled="!allQuizAnswered || isLoadingStep"
            class="step-button"
            size="large"
            aria-label="提交 Quiz 答案"
          >
            <template #icon><check-outlined /></template>
            {{ isLoadingStep ? '提交中...' : '提交 Quiz 答案' }}
          </a-button>
        </div>

        <Step2Guidance
          v-if="currentStep === 2 && experimentId"
          :experimentId="experimentId"
          :totalScore="totalQuizScore"
          :totalQuestions="experimentData.quizQuestions?.length || 0"
          :guidanceText="guidanceText"
          :isLoading="isLoadingStep"
          @next="goToStep(3)"
          @itemSelectedForStep3="handleItemSelectedFromStep2"
        />

        <Step3DescriptionInput
          v-if="currentStep === 3"
          v-model:initialPrompt="initialPrompt"
          :experimentData="experimentData"
          :isLoading="isLoadingStep"
          v-model:imageDescription="imageDescription"
          @update:imageDescription="updateImageDescription"
          :itemData="selectedItemForStep3"
          @next="goToStep(4)"
        />

        <Step4PlanInput
          v-if="currentStep === 4"
          v-model:planPrompt="planPrompt"
          v-model:imageDescription="imageDescription"
          :experimentData="experimentData"
          :isLoading="isLoadingStep"
          v-model:planList="planList"
          @next="goToStep(5)"
        />

        <Step5ExecutePlan
          v-if="currentStep === 5"
          v-model:planList="planList"
          :isLoading="isLoadingStep"
          v-model:detailedInfo="detailedInfo"
          :imageDescription="imageDescription"
          @update:isLoading="isLoadingStep = $event"
          @next="goToStep(6)"
        />

        <Step6GetAnswer
          v-if="currentStep === 6"
          v-model:detailedInfo="detailedInfo"
          :experimentData="experidata"
          :isLoading="isLoadingStep"
          v-model:modelAnswer="modelAnswer"
          @update:modelAnswer="updateModelAnswer"
          v-model:modelExplanation="modelExplanation"
          :itemData="selectedItemForStep3"
          @next="goToStep(7)"
        />

        <Step7EvaluateResult
          v-if="currentStep === 7"
          v-model:finalAnswer="modelresult"
          v-model:modelexplanation="modelExplanation"
          :experimentData="experidata"
          :isLoading="isLoadingStep"
          v-model:evaluationResult="evaluationResult"
          v-model:score="score"
          @next="goToStep(8)"
        />

        <Step8Completion
          v-if="currentStep === 8"
          :finalAnswer="modelresult"
          :modelExplanations="modelExplanation"
          :correctAnswer="experidata?.quizQuestions?.[0]?.explanation"
          :imagePathForSummary="experidata?.quizQuestions?.[0]?.image_path"
          :questionForSummary="experidata?.quizQuestions?.[0]?.question"
          :currentImageDescription="imageDescription"
          :currentPlanPrompt="planPrompt"
          :currentPlanList="planList"
          :executionSummary="detailedInfo"
          :evaluationData="evaluationResult"
          :myNewScore="score"
          :itemData="selectedItemForStep3"
          :isLoading="isLoadingStep"
          @restart="restartExperiment"
          @save="saveExperimentRecord"
        />
      </div>
    </div>
    <div v-else-if="!isLoadingData && !dataError" class="loading-container">
      <a-spin tip="正在加载实验数据..."></a-spin>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ExperimentOutlined,
  CheckOutlined,
  RightOutlined,
  CheckCircleFilled,
  OrderedListOutlined,
  LoadingOutlined,
  LeftOutlined,
  HomeOutlined
} from '@ant-design/icons-vue'
import {
  Card as ACard,
  Button as AButton,
  Spin as ASpin,
  Alert as AAlert,
  Typography,
  Empty as AEmpty
} from 'ant-design-vue'

// 导入步骤组件
import Step2Guidance from '@/components/experimentSteps/Step2Guidance.vue'
import Step3DescriptionInput from '@/components/experimentSteps/Step3DescriptionInput.vue'
import Step4PlanInput from '@/components/experimentSteps/Step4PlanInput.vue'
import Step5ExecutePlan from '@/components/experimentSteps/Step5ExecutePlan.vue'
import Step6GetAnswer from '@/components/experimentSteps/Step6GetAnswer.vue'
import Step7EvaluateResult from '@/components/experimentSteps/Step7EvaluateResult.vue'
import Step8Completion from '@/components/experimentSteps/Step8Completion.vue'

// 导入测试数据
import { createExperimentData } from '@/data/quizQuestions.js'

const route = useRoute()
const router = useRouter()

// 存储状态到 sessionStorage 的 key
const storageKey = computed(() => {
  if (!experimentId.value) return null
  return `experimentState_${experimentId.value}`
})

// 需要持久化的状态变量
const selectedItemForStep3 = ref(null)
const modelresult = ref(null)
const experidata = ref(null)
const experimentId = ref(null)
const experimentData = ref(null)
const isLoadingData = ref(true)
const dataError = ref(null)

const currentStep = ref(1)
const isLoadingStep = ref(false)

// Step 1 (Quiz) 状态
const userQuizAnswers = ref({})
const totalQuizScore = ref(null)
const allQuizAnswered = computed(() => {
  if (!experimentData.value?.quizQuestions?.length) return false
  return experimentData.value.quizQuestions.every(
    (q) =>
      userQuizAnswers.value.hasOwnProperty(q.id) &&
      userQuizAnswers.value[q.id] !== '' &&
      userQuizAnswers.value[q.id] !== null &&
      userQuizAnswers.value[q.id] !== undefined
  )
})

// Step 2 (Guidance) 状态
const guidanceText = ref('')

// Step 3 (Description) 状态
const initialPrompt = ref('')
const imageDescription = ref(null)

// Step 4 (Plan) 状态
const planPrompt = ref('')
const planList = ref(null)

// Step 5 (Execute) 状态
const detailedInfo = ref(null)

// Step 6 (Get Answer) 状态
const modelAnswer = ref(null)
const modelExplanation = ref(null)

// Step 7 (Evaluate) 状态
const evaluationResult = ref(null)
const score = ref(null)

// 时间线步骤定义
const timelineSteps = [
  { step: 1, label: '基础测试' },
  { step: 2, label: '分析提示' },
  { step: 3, label: '图像描述' },
  { step: 4, label: '实验计划' },
  { step: 5, label: '执行计划' },
  { step: 6, label: '获取答案' },
  { step: 7, label: '结果评估' },
  { step: 8, label: '实验总结' }
]

// 返回上一页
const goBack = () => {
  router?.back()
}

// 跳转到指定步骤
const goToStep = (stepNumber) => {
  if (stepNumber < 1 || stepNumber > timelineSteps.length) {
    console.warn('无效的步骤编号:', stepNumber)
    return
  }

  // 可以添加逻辑防止跳过必要步骤
  // 例如: if (stepNumber > currentStep.value + 1) return;

  currentStep.value = stepNumber

  // 保存当前状态
  saveState()
}

// 转换选中的题目数据为实验数据格式
function transformItemToExperimentData(itemData) {
  if (
    !itemData ||
    typeof itemData !== 'object' ||
    typeof itemData.question !== 'string' ||
    !Array.isArray(itemData.options)
  ) {
    console.error("提供的题目数据无效。需要: 包含 'question' (字符串) 和 'options' (数组) 的对象。")
    return { quizQuestions: [] }
  }

  const transformedData = {
    quizQuestions: [
      {
        id: itemData.id || 0,
        question: itemData.question,
        options: itemData.options,
        explanation: itemData.explanation,
        image_path: itemData.image_path,
        answer: itemData.answer,
        image_1: itemData.image_1
      }
    ],
    question: itemData.question
  }

  return transformedData
}

// 保存状态到 sessionStorage
const saveState = () => {
  if (!storageKey.value) {
    console.warn('无法保存状态: experimentId 未设置。')
    return
  }
  try {
    const stateToSave = {
      currentStep: currentStep.value,
      userQuizAnswers: userQuizAnswers.value,
      totalQuizScore: totalQuizScore.value,
      guidanceText: guidanceText.value,
      selectedItemForStep3: selectedItemForStep3.value,
      imageDescription: imageDescription.value,
      planPrompt: planPrompt.value,
      planList: planList.value,
      detailedInfo: detailedInfo.value,
      modelAnswer: modelAnswer.value,
      modelExplanation: modelExplanation.value,
      modelresult: modelresult.value,
      experidata: experidata.value,
      evaluationResult: evaluationResult.value,
      score: score.value
    }
    sessionStorage.setItem(storageKey.value, JSON.stringify(stateToSave))
    console.log(`状态已保存: ${storageKey.value}`)
  } catch (e) {
    console.error('保存状态到 sessionStorage 时出错:', e)
  }
}

// 从 sessionStorage 加载状态
const loadState = () => {
  if (!storageKey.value) {
    console.warn('无法加载状态: experimentId 未设置。')
    return false
  }
  try {
    const savedState = sessionStorage.getItem(storageKey.value)
    if (savedState) {
      const state = JSON.parse(savedState)

      if (state.currentStep !== undefined) currentStep.value = state.currentStep
      if (state.userQuizAnswers !== undefined) userQuizAnswers.value = state.userQuizAnswers
      if (state.totalQuizScore !== undefined) totalQuizScore.value = state.totalQuizScore
      if (state.guidanceText !== undefined) guidanceText.value = state.guidanceText
      if (state.selectedItemForStep3 !== undefined)
        selectedItemForStep3.value = state.selectedItemForStep3
      if (state.imageDescription !== undefined) {
        // console.log('加载 imageDescription:', state.imageDescription) // 添加日志
        imageDescription.value = state.imageDescription
      }
      if (state.planPrompt !== undefined) planPrompt.value = state.planPrompt
      if (state.planList !== undefined) planList.value = state.planList
      if (state.detailedInfo !== undefined) detailedInfo.value = state.detailedInfo
      if (state.modelAnswer !== undefined) modelAnswer.value = state.modelAnswer
      if (state.modelExplanation !== undefined) modelExplanation.value = state.modelExplanation
      if (state.modelresult !== undefined) modelresult.value = state.modelresult
      if (state.experidata !== undefined) experidata.value = state.experidata
      if (state.evaluationResult !== undefined) evaluationResult.value = state.evaluationResult
      if (state.score !== undefined) score.value = state.score

      console.log(`状态加载成功: ${storageKey.value}`)
      return true
    }
  } catch (e) {
    console.error('从 sessionStorage 加载状态时出错:', e)
    sessionStorage.removeItem(storageKey.value)
  }
  return false
}

// 清除状态
const clearState = () => {
  if (!storageKey.value) {
    console.warn('无法清除状态: experimentId 未设置。')
    return
  }
  try {
    sessionStorage.removeItem(storageKey.value)
    console.log(`状态已清除: ${storageKey.value}`)
  } catch (e) {
    console.error('从 sessionStorage 清除状态时出错:', e)
  }
}

// 获取实验数据
const fetchExperimentData = async (id) => {
  if (!id) {
    dataError.value = '无效的实验 ID。'
    isLoadingData.value = false
    currentStep.value = 0
    return
  }
  isLoadingData.value = true
  dataError.value = null
  experimentData.value = null

  try {
    await new Promise((resolve) => setTimeout(resolve, 1000))
    const mockData = createExperimentData(id)

    if (mockData.quizQuestions.length !== 10) {
      console.warn(`预期 10 个 Quiz 题目，实际加载 ${mockData.quizQuestions.length} 个`)
    }
    experimentData.value = mockData

    const stateLoaded = loadState()

    if (!stateLoaded || Object.keys(userQuizAnswers.value).length === 0) {
      console.log('初始化新的用户答案。')
      userQuizAnswers.value = mockData.quizQuestions.reduce((acc, q) => {
        if (!userQuizAnswers.value.hasOwnProperty(q.id)) {
          acc[q.id] = ''
        } else {
          acc[q.id] = userQuizAnswers.value[q.id]
        }
        return acc
      }, {})

      if (!stateLoaded) {
        currentStep.value = 1
      }
    } else {
      console.log('用户答案已从状态加载，正在验证。')
      const loadedAnswers = { ...userQuizAnswers.value }
      userQuizAnswers.value = mockData.quizQuestions.reduce((acc, q) => {
        acc[q.id] = loadedAnswers.hasOwnProperty(q.id) ? loadedAnswers[q.id] : ''
        return acc
      }, {})
    }

    console.log('实验数据加载成功:', mockData)
  } catch (err) {
    console.error('加载实验数据出错:', err)
    dataError.value = `无法加载实验数据: ${err.message}`
    experimentData.value = null
    currentStep.value = 0
    clearState()
  } finally {
    isLoadingData.value = false
  }
}

// 提交 Quiz 答案
const submitQuizAnswers = async () => {
  if (!allQuizAnswered.value) {
    alert('请回答所有问题再提交！')
    return
  }
  isLoadingStep.value = true
  try {
    await new Promise((resolve) => setTimeout(resolve, 500))
    let score = 0
    const totalQuestions = experimentData.value.quizQuestions.length
    experimentData.value.quizQuestions.forEach((q) => {
      if (userQuizAnswers.value[q.id] === q.answer) {
        score++
      }
    })
    totalQuizScore.value = score
    const passingScore = Math.ceil(totalQuestions * 0.6)
    guidanceText.value =
      score >= passingScore
        ? `你的基础知识测试得分是 ${score} 分。成绩不错！现在你可以选择一个问题进行深入分析。`
        : `你的基础知识测试得分是 ${score} 分。不用担心，这只是帮助你了解自己的知识水平。现在你可以选择一个问题进行深入分析。`

    // 保存状态并前进到下一步
    saveState()
    goToStep(2)
  } catch (err) {
    console.error('提交答案时出错:', err)
    alert(`提交答案时出错: ${err.message}`)
  } finally {
    isLoadingStep.value = false
  }
}

// 处理从 Step2 选择的题目
const handleItemSelectedFromStep2 = (item) => {
  console.log('从 Step2 选择的题目:', item)
  selectedItemForStep3.value = item
  experidata.value = transformItemToExperimentData(item)
  saveState()
}

// 更新图像描述
const updateImageDescription = (description) => {
  imageDescription.value = description
  // 延迟保存状态
  nextTick(() => {
    saveState()
  })
}

// 更新模型答案
const updateModelAnswer = (answer) => {
  modelresult.value = answer
  saveState()
}

// 重启实验
const restartExperiment = () => {
  // 重置所有状态
  currentStep.value = 1
  userQuizAnswers.value = {}
  totalQuizScore.value = null
  guidanceText.value = ''
  selectedItemForStep3.value = null
  imageDescription.value = null
  planPrompt.value = ''
  planList.value = null
  detailedInfo.value = null
  modelAnswer.value = null
  modelExplanation.value = null
  modelresult.value = null
  experidata.value = null
  evaluationResult.value = null
  score.value = null

  // 清除保存的状态
  clearState()

  // 重新加载实验数据
  if (experimentId.value) {
    fetchExperimentData(experimentId.value)
  }
}

// 保存实验记录
const saveExperimentRecord = async () => {
  isLoadingStep.value = true
  try {
    // 模拟保存操作
    await new Promise((resolve) => setTimeout(resolve, 1000))
    alert('实验记录已成功保存！')
    // 可以选择清除状态或保留
    // clearState();
  } catch (err) {
    console.error('保存实验记录时出错:', err)
    alert(`保存实验记录时出错: ${err.message}`)
  } finally {
    isLoadingStep.value = false
  }
}

// 组件挂载时获取实验 ID 并加载数据
onMounted(() => {
  experimentId.value = route.params.id
  if (experimentId.value) {
    fetchExperimentData(experimentId.value)
  } else {
    dataError.value = '未提供实验 ID。'
    isLoadingData.value = false
  }
})

// 监听路由变化，重新加载数据
watch(
  () => route.params.id,
  (newId) => {
    if (newId && newId !== experimentId.value) {
      experimentId.value = newId
      fetchExperimentData(newId)
    }
  }
)
</script>

<style scoped>
.experiment-execution-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  user-select: text;
  /* 确保文本可以被选择 */
  background-color: #f5f7fa;
}

/* 优化顶部导航 */
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border-left: 4px solid #1890ff;
}

.nav-left {
  display: flex;
  align-items: center;
}

.back-link {
  display: flex;
  align-items: center;
  color: #1890ff;
  font-weight: 500;
  font-size: 15px;
  padding: 0;
  transition: all 0.3s;
}

.back-link:hover {
  color: #40a9ff;
  transform: translateX(-3px);
}

.nav-breadcrumb {
  flex: 1;
  margin-left: 20px;
}

.breadcrumb-link {
  color: #1890ff;
  text-decoration: none;
  transition: color 0.3s;
}

.breadcrumb-link:hover {
  color: #40a9ff;
  text-decoration: underline;
}

/* 优化时间线区域 */
.timeline-area {
  margin-bottom: 30px;
  padding: 24px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.timeline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  padding: 0 20px;
}

.timeline-step-wrapper {
  display: flex;
  align-items: center;
  flex: 1;
}

.timeline-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  position: relative;
  z-index: 2;
  transition: all 0.3s;
}

.node-dot {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  font-weight: 600;
  color: #595959;
  border: 2px solid #d9d9d9;
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.node-label {
  font-size: 14px;
  color: #595959;
  text-align: center;
  font-weight: 500;
  transition: all 0.3s;
  white-space: nowrap;
}

/* 步骤状态样式 */
.timeline-node.active .node-dot {
  background-color: #e6f7ff;
  color: #1890ff;
  border-color: #1890ff;
  transform: scale(1.1);
  box-shadow: 0 0 0 4px rgba(24, 144, 255, 0.2);
}

.timeline-node.active .node-label {
  color: #1890ff;
  font-weight: 600;
}

.timeline-node.completed .node-dot {
  background-color: #1890ff;
  color: white;
  border-color: #1890ff;
}

.timeline-node.completed .node-label {
  color: #1890ff;
}

.timeline-node.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

/* 长箭头样式 */
.step-arrow-container {
  display: flex;
  align-items: center;
  /* 箭头向上移动 */
  transform: translateY(-10px);
  flex: 1;
  position: relative;
  height: 4px;
  /* 增加线条粗度 */
  margin: 0 1px;
  opacity: 1;
  /* 默认显示 */
  transition: all 0.5s ease;
  /* 添加过渡效果 */
}

/* 灰色箭头 - 初始状态和未到达的步骤 */
.step-arrow-container.arrow-gray .step-arrow-line {
  background: #d9d9d9;
}

.step-arrow-container.arrow-gray .step-arrow-icon {
  color: #d9d9d9;
}

/* 蓝色箭头 - 指向当前正在做的步骤 */
.step-arrow-container.arrow-blue .step-arrow-line {
  background: #1890ff;
}

.step-arrow-container.arrow-blue .step-arrow-icon {
  color: #1890ff;
}

/* 绿色箭头 - 已完成的步骤 */
.step-arrow-container.arrow-green .step-arrow-line {
  background: #52c41a;
}

.step-arrow-container.arrow-green .step-arrow-icon {
  color: #52c41a;
}

.step-arrow-line {
  height: 8px;
  width: 100%;
  position: relative;
  border-radius: 2px;
}

.step-arrow-icon {
  position: absolute;
  right: -8px;
  /* 调整位置使箭头更靠近下一个节点 */
  font-size: 28px;
  /* 增大箭头图标 */
  z-index: 2;
  /* 确保箭头在线条上方 */
}

/* 响应式调整 */
@media (max-width: 768px) {
  .timeline {
    flex-direction: column;
    align-items: flex-start;
  }

  .timeline-step-wrapper {
    width: 100%;
    margin-bottom: 15px;
  }

  .step-arrow-container {
    transform: rotate(90deg);
    margin: 10px 0;
    width: 30px;
    align-self: center;
  }

  .node-label {
    margin-bottom: 5px;
  }
}

/* 确保其他元素也可以选择文本 */
.quiz-item p,
.quiz-item label,
.step-output,
.section-title {
  user-select: text;
}

.top-nav {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e8e8e8;
}

.back-link {
  color: #1890ff;
  cursor: pointer;
  font-weight: 500;
  transition: color 0.3s;
}

.back-link:hover {
  color: #40a9ff;
  text-decoration: underline;
}

.breadcrumb-path {
  margin-left: 12px;
  color: #8c8c8c;
}

.breadcrumb-link {
  color: #1890ff;
  text-decoration: none;
}

.breadcrumb-link:hover {
  text-decoration: underline;
}

.breadcrumb-current {
  color: #262626;
  font-weight: 500;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.error-message {
  padding: 16px;
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  color: #ff4d4f;
  margin-bottom: 24px;
}

.execution-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 优化后的时间线样式 */
.timeline-area {
  background-color: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-bottom: 24px;
}

.timeline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  padding: 0 20px;
}

.timeline-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background-color: #e8e8e8;
  z-index: 1;
  transform: translateY(-50%);
}

.timeline-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 2;
  cursor: pointer;
  transition: all 0.3s;
  padding: 0 10px;
}

.node-dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #fff;
  border: 2px solid #d9d9d9;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 600;
  color: #8c8c8c;
  transition: all 0.3s;
}

.timeline-node.active .node-dot {
  background-color: #1890ff;
  border-color: #1890ff;
  color: #fff;
}

.timeline-node.completed .node-dot {
  background-color: #52c41a;
  border-color: #52c41a;
  color: #fff;
}

.timeline-node.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.node-label {
  font-size: 14px;
  font-weight: 500;
  color: #8c8c8c;
  text-align: center;
  transition: all 0.3s;
  white-space: nowrap;
}

.timeline-node.active .node-label {
  color: #1890ff;
  font-weight: 600;
}

.timeline-node.completed .node-label {
  color: #52c41a;
}

/* 新增: 步骤之间的箭头 */
.step-arrow {
  position: absolute;
  right: -15px;
  top: 18px;
  color: #8c8c8c;
  font-size: 16px;
  z-index: 3;
}

.timeline-node.completed .step-arrow {
  color: #52c41a;
}

.timeline-node.active .step-arrow {
  color: #1890ff;
}

.step-content-area {
  background-color: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.experiment-step {
  margin-bottom: 30px;
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

.section-title {
  margin-top: 24px !important;
  margin-bottom: 16px !important;
  display: flex;
  align-items: center;
  color: #262626 !important;
}

.section-icon {
  margin-right: 10px;
  font-size: 20px;
  color: #1890ff;
}

.quiz-list {
  margin-top: 24px;
}

.quiz-item {
  margin-bottom: 24px;
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background-color: #fafafa;
}

.quiz-image-container {
  margin: 20px 0;
  text-align: center;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.quiz-image {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

.quiz-item ul {
  list-style: none;
  padding: 0;
  margin-top: 16px;
}

.quiz-item li {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background-color 0.2s ease;
}

.quiz-item li:hover {
  background-color: #f5f7fa;
}

.quiz-item input[type='radio'] {
  margin-right: 12px;
  cursor: pointer;
  width: 18px;
  height: 18px;
  accent-color: #1890ff;
}

.quiz-item label {
  cursor: pointer;
  color: #262626;
  font-size: 16px;
  line-height: 1.5;
  flex: 1;
}

.step-button {
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: white;
  border: none;
  cursor: pointer;
  margin-top: 24px;
}

.step-button:disabled {
  background: #f5f5f5;
  color: rgba(0, 0, 0, 0.25);
  border: 1px solid #d9d9d9;
  cursor: not-allowed;
  box-shadow: none;
}

.step-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.step-output {
  margin-top: 24px;
  padding: 20px;
  background-color: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.step-output h4 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.step-output pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', 'Monaco', 'Andale Mono', 'Ubuntu Mono', monospace;
  background-color: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  max-height: 400px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

/* 添加滚动条样式 */
.step-output pre::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.step-output pre::-webkit-scrollbar-thumb {
  background-color: #c0c0c0;
  border-radius: 4px;
}

.step-output pre::-webkit-scrollbar-track {
  background-color: #f0f0f0;
  border-radius: 4px;
}
</style>
