<script setup>
console.log('ExperimentDashboard.vue script is running!')
import { ref, reactive, onMounted } from 'vue'
import { PanelLeftOpen } from 'lucide-vue-next'
import { experimentApi } from '@/apis/experiment_api' // 确保这里导入的是修改后的 experiment_api.js
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

// --- UI 状态 ---
const isSidebarOpen = ref(localStorage.getItem('dashboard_sidebar_open') === 'true')

// --- 数据状态 ---
const courses = ref([])
const loadingCourses = ref(false)

const selectedCourseId = ref(null)
const experiments = ref([])
const loadingExperiments = ref(false)

const selectedExperimentId = ref(null)
const experimentDetail = ref(null)
const loadingExperimentDetail = ref(false)

const currentRecordId = ref(null)
const userAnswers = reactive({})
const loadingStartExperiment = ref(false)
const submittingAnswers = ref(false)
const submissionResult = ref(null)

const newReview = reactive({
  rating: 5,
  comment: ''
})
const submittingReview = ref(false)
const reviewMessage = ref('')
const reviewStatus = ref('')

const outputLog = ref('所有API响应将显示在这里，请同时查看浏览器控制台 (F12) 获取完整信息。')

// --- 方法 ---

const logOutput = (message, data, isError = false) => {
  const timestamp = new Date().toLocaleTimeString()
  let logEntry
  if (data !== undefined) {
    logEntry = `[${timestamp}] ${isError ? 'ERROR: ' : ''}${message}\n${JSON.stringify(
      data,
      null,
      2
    )}`
  } else {
    logEntry = `[${timestamp}] ${isError ? 'ERROR: ' : ''}${JSON.stringify(message, null, 2)}`
  }
  outputLog.value = logEntry + '\n' + outputLog.value
  if (isError) {
    console.error(message, data)
    if (data?.detail === '无效的令牌' || data?.status === 401) {
      outputLog.value = `[${timestamp}] ERROR: 用户认证失败，请重新登录。\n` + outputLog.value
    }
  } else {
    console.log(message, data)
  }
}

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
  localStorage.setItem('dashboard_sidebar_open', isSidebarOpen.value)
}

const handleLogout = () => {
  logOutput('用户登出...')
  userStore.logout()
  router.push('/login')
}

const fetchAllCourses = async () => {
  loadingCourses.value = true
  try {
    const data = await experimentApi.getAllCourses()
    courses.value = data
    logOutput('获取所有课程成功:', data)
  } catch (error) {
    logOutput('获取所有课程失败:', error, true)
    courses.value = []
  } finally {
    loadingCourses.value = false
  }
}

const selectCourse = (courseId) => {
  selectedCourseId.value = courseId
  experiments.value = [] // 重置实验列表
  selectedExperimentId.value = null // 重置选中的实验
  experimentDetail.value = null // 重置实验详情
  fetchExperimentsInCourse(courseId)
}

const fetchExperimentsInCourse = async (courseId) => {
  if (!courseId) {
    logOutput('请选择课程才能获取实验列表。', true)
    return
  }
  loadingExperiments.value = true
  try {
    const data = await experimentApi.getExperimentsByCourse(courseId)
    experiments.value = data
    logOutput(`获取课程 ${courseId} 下的实验成功:`, data)
  } catch (error) {
    logOutput(`获取课程 ${courseId} 下的实验失败:`, error, true)
    experiments.value = []
  } finally {
    loadingExperiments.value = false
  }
}

const selectExperiment = (experimentId) => {
  selectedExperimentId.value = experimentId
  experimentDetail.value = null // 重置实验详情
  currentRecordId.value = null // 重置当前记录ID
  for (const key in userAnswers) {
    delete userAnswers[key] // 清空用户答案
  }
  submissionResult.value = null // 重置提交结果
  newReview.rating = 5 // 重置评论评分
  newReview.comment = '' // 重置评论内容
  reviewMessage.value = '' // 重置评论消息
  reviewStatus.value = '' // 重置评论状态
  fetchExperimentDetails(experimentId)
}

const fetchExperimentDetails = async (experimentId) => {
  if (!experimentId) {
    logOutput('请选择实验才能获取实验详情。', true)
    return
  }
  loadingExperimentDetail.value = true
  try {
    const data = await experimentApi.getExperimentDetails(experimentId)
    experimentDetail.value = data
    logOutput(`获取实验 ${experimentId} 详情成功:`, data)
    // 初始化用户答案
    if (data.curriculum) {
      data.curriculum.forEach((step) => {
        userAnswers[step.id] = ''
      })
    }
  } catch (error) {
    logOutput(`获取实验 ${experimentId} 详情失败:`, error, true)
    experimentDetail.value = null
  } finally {
    loadingExperimentDetail.value = false
  }
}

const startOrContinueExperiment = async () => {
  if (!selectedExperimentId.value) {
    logOutput('请选择实验才能开始实验。', true)
    return
  }
  loadingStartExperiment.value = true
  try {
    const data = await experimentApi.startOrContinueExperiment(selectedExperimentId.value)
    currentRecordId.value = data.id
    // 如果有历史答案，加载它们
    if (data.answers) {
      Object.assign(userAnswers, data.answers)
      logOutput('已加载历史答案:', data.answers)
    }
    logOutput('开始/继续实验成功:', data)
  } catch (error) {
    logOutput('开始/继续实验失败:', error, true)
  } finally {
    loadingStartExperiment.value = false
  }
}

const submitAnswers = async () => {
  if (!currentRecordId.value) {
    logOutput('请先开始实验才能提交答案。', true)
    return
  }
  submittingAnswers.value = true
  try {
    // 过滤掉空答案，只提交有内容的答案
    const answersToSend = Object.entries(userAnswers).reduce((acc, [stepId, answer]) => {
      if (answer !== '') {
        acc[stepId] = answer
      }
      return acc
    }, {})

    const data = await experimentApi.submitExperimentAnswers(currentRecordId.value, answersToSend)
    submissionResult.value = data
    logOutput('提交答案成功:', data)
  } catch (error) {
    logOutput('提交答案失败:', error, true)
  } finally {
    submittingAnswers.value = false
  }
}

const submitReview = async () => {
  if (!selectedExperimentId.value) {
    logOutput('请选择实验才能提交评论。', true)
    return
  }
  if (!newReview.comment || newReview.rating < 1 || newReview.rating > 5) {
    reviewMessage.value = '评论内容和评分是必填的，评分需在1-5之间。'
    reviewStatus.value = 'error'
    return
  }

  submittingReview.value = true
  reviewMessage.value = '' // 清空之前的消息
  reviewStatus.value = '' // 清空之前的状态

  try {
    const data = await experimentApi.submitReview(selectedExperimentId.value, newReview)
    reviewMessage.value = '评论提交成功！'
    reviewStatus.value = 'success'
    logOutput('提交评论成功:', data)
    // 提交成功后清空表单并刷新实验详情以显示新评论
    newReview.comment = ''
    newReview.rating = 5
    await fetchExperimentDetails(selectedExperimentId.value)
  } catch (error) {
    reviewMessage.value = `评论提交失败: ${error?.detail || '未知错误'}`
    reviewStatus.value = 'error'
    logOutput('提交评论失败:', error, true)
  } finally {
    submittingReview.value = false
  }
}

// --- 生命周期钩子 ---
onMounted(() => {
  if (userStore.isLoggedIn) {
    logOutput('组件已挂载，用户已认证，正在获取所有课程...')
    fetchAllCourses()
  } else {
    logOutput('用户未认证，请先登录。', true)
    router.push('/login')
  }
})
</script>

<template>
  <div class="experiment-dashboard">
    <div class="dashboard-header">
      <div class="header__left">
        <div class="nav-btn" @click="toggleSidebar">
          <PanelLeftOpen size="20" color="var(--gray-800)" />
        </div>
        <div class="dashboard-title">学生实验平台</div>
      </div>
      <div class="header__right">
        <button @click="handleLogout">登出</button>
      </div>
    </div>

    <div class="dashboard-content">
      <div
        :class="{ sidebar: true, 'sidebar-open': isSidebarOpen, 'sidebar-closed': !isSidebarOpen }"
      >
        <h2>导航</h2>
        <ul>
          <li>
            <button @click="fetchAllCourses" :disabled="loadingCourses">
              {{ loadingCourses ? '加载中...' : '所有课程' }}
            </button>
          </li>
          <li v-if="selectedCourseId">
            <button
              @click="fetchExperimentsInCourse(selectedCourseId)"
              :disabled="loadingExperiments"
            >
              {{ loadingExperiments ? '加载中...' : `课程 ${selectedCourseId} 实验` }}
            </button>
          </li>
          <li v-if="selectedExperimentId">
            <button
              @click="fetchExperimentDetails(selectedExperimentId)"
              :disabled="loadingExperimentDetail"
            >
              {{ loadingExperimentDetail ? '加载中...' : `实验 ${selectedExperimentId} 详情` }}
            </button>
          </li>
        </ul>
      </div>

      <div class="main-panel">
        <div class="section">
          <h2>所有课程</h2>
          <div v-if="courses.length">
            <ul>
              <li
                v-for="course in courses"
                :key="course.id"
                @click="selectCourse(course.id)"
                class="clickable-card"
              >
                <strong>{{ course.title }}</strong> (ID: {{ course.id }})
                <p>{{ course.description }}</p>
              </li>
            </ul>
          </div>
          <p v-else-if="loadingCourses">正在加载课程...</p>
          <p v-else>暂无可用课程。</p>
        </div>

        <div class="section" v-if="selectedCourseId">
          <h2>课程 {{ selectedCourseId }} 下的实验</h2>
          <div v-if="experiments.length">
            <ul>
              <li
                v-for="exp in experiments"
                :key="exp.id"
                @click="selectExperiment(exp.id)"
                class="clickable-card"
              >
                <strong>{{ exp.title }}</strong> (ID: {{ exp.id }})
                <p>{{ exp.description }}</p>
                <p>标签: {{ exp.tag || '无' }}</p>
                <img
                  v-if="exp.image"
                  :src="exp.image"
                  alt="实验图片"
                  style="max-width: 100px; max-height: 100px"
                />
              </li>
            </ul>
          </div>
          <p v-else-if="loadingExperiments">正在加载实验...</p>
          <p v-else>该课程下暂无实验。</p>
        </div>

        <div class="section" v-if="selectedExperimentId">
          <h2>实验详情 (ID: {{ selectedExperimentId }})</h2>
          <div v-if="experimentDetail">
            <h3>{{ experimentDetail.title }}</h3>
            <p>描述: {{ experimentDetail.description }}</p>
            <p>标签: {{ experimentDetail.tag || '无' }}</p>
            <p>总评分: {{ experimentDetail.overall_rating }} / 5</p>

            <h4>实验步骤 (Curriculum)</h4>
            <div v-if="experimentDetail.curriculum && experimentDetail.curriculum.length">
              <div
                v-for="(step, index) in experimentDetail.curriculum"
                :key="step.id"
                class="experiment-step"
              >
                <p>
                  <strong>步骤 {{ index + 1 }} (ID: {{ step.id }}):</strong> {{ step.question }}
                </p>
                <p v-if="step.explanation">{{ step.explanation }}</p>
                <label :for="'answer-' + step.id">你的答案:</label>
                <input
                  v-if="!step.options"
                  type="text"
                  :id="'answer-' + step.id"
                  v-model="userAnswers[step.id]"
                  placeholder="输入你的答案"
                />
                <div v-if="step.options">
                  <p>选项:</p>
                  <div v-for="(value, key) in step.options" :key="key">
                    <input
                      type="radio"
                      :id="'option-' + step.id + '-' + key"
                      :name="'step-' + step.id"
                      :value="key"
                      v-model="userAnswers[step.id]"
                    />
                    <label :for="'option-' + step.id + '-' + key">{{ key }}: {{ value }}</label>
                  </div>
                </div>
              </div>
              <button @click="startOrContinueExperiment" :disabled="loadingStartExperiment">
                {{ loadingStartExperiment ? '处理中...' : '开始/继续实验' }}
              </button>
              <button @click="submitAnswers" :disabled="!currentRecordId || submittingAnswers">
                {{ submittingAnswers ? '提交中...' : '提交答案' }}
              </button>
              <p v-if="currentRecordId">当前实验记录ID: {{ currentRecordId }}</p>
              <p v-if="submissionResult">提交结果: {{ submissionResult.score }} 分</p>

              <h4>提交评论</h4>
              <div class="review-form">
                <label for="review-rating">评分 (1-5):</label>
                <input
                  type="number"
                  id="review-rating"
                  v-model.number="newReview.rating"
                  min="1"
                  max="5"
                />
                <label for="review-comment">评论内容:</label>
                <textarea id="review-comment" v-model="newReview.comment" rows="3"></textarea>
                <button @click="submitReview" :disabled="submittingReview">
                  {{ submittingReview ? '提交中...' : '提交评论' }}
                </button>
                <p :class="reviewStatus">{{ reviewMessage }}</p>
              </div>

              <h4>用户评论</h4>
              <div v-if="experimentDetail.reviews && experimentDetail.reviews.length">
                <ul>
                  <li v-for="review in experimentDetail.reviews" :key="review.id">
                    <strong>{{ review.user_name }}</strong> 评分: {{ review.rating }}/5
                    <p>{{ review.comment }}</p>
                    <small>{{ new Date(review.timestamp).toLocaleString() }}</small>
                  </li>
                </ul>
              </div>
              <p v-else>暂无评论。</p>
            </div>
            <p v-else>该实验暂无步骤。</p>
          </div>
          <p v-else-if="loadingExperimentDetail">正在加载实验详情...</p>
        </div>
      </div>
    </div>

    <!-- <div class="output">
      <h2>API 响应和日志 (查看Console获取完整信息)</h2>
      <pre>{{ outputLog }}</pre>
    </div> -->
  </div>
</template>
<style scoped>
/* STYLE部分保持不变 */
.experiment-dashboard {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: 'Arial', sans-serif;
  background-color: var(--gray-50);
  color: var(--gray-900);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background-color: var(--primary-600);
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.header__left {
  display: flex;
  align-items: center;
}

.nav-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  margin-right: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dashboard-title {
  font-size: 24px;
  font-weight: bold;
}

.header__right button {
  background-color: var(--primary-700);
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.header__right button:hover {
  background-color: var(--primary-800);
}

.dashboard-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 250px;
  background-color: var(--gray-100);
  padding: 20px;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.05);
  transition: width 0.3s ease-in-out;
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-closed {
  width: 0;
  padding: 0;
  overflow: hidden;
}

.sidebar-open {
  width: 250px;
  padding: 20px;
}

.sidebar h2 {
  color: var(--primary-600);
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 20px;
}

.sidebar ul {
  list-style: none;
  padding: 0;
}

.sidebar li {
  margin-bottom: 10px;
}

.sidebar button {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid var(--primary-300);
  border-radius: 5px;
  background-color: var(--primary-100);
  color: var(--primary-800);
  text-align: left;
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    border-color 0.2s ease;
}

.sidebar button:hover:not(:disabled) {
  background-color: var(--primary-200);
  border-color: var(--primary-400);
}

.sidebar button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: var(--gray-200);
  color: var(--gray-500);
  border-color: var(--gray-300);
}

.main-panel {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: var(--white);
}

.section {
  background-color: var(--gray-50);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.section h2 {
  color: var(--primary-700);
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 22px;
}

.section h3 {
  color: var(--primary-600);
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 18px;
}

.section h4 {
  color: var(--primary-500);
  margin-top: 15px;
  margin-bottom: 10px;
  font-size: 16px;
}

.section ul {
  list-style: none;
  padding: 0;
}

/* 新增或修改以下样式，使卡片可点击 */
.section li {
  background-color: var(--white);
  border: 1px solid var(--gray-200);
  border-radius: 5px;
  padding: 15px;
  margin-bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  /* 使整个列表项可点击 */
  cursor: pointer;
  /* 添加过渡效果，提升用户体验 */
  transition:
    background-color 0.2s ease,
    border-color 0.2s ease,
    transform 0.2s ease;
}

/* 悬停效果 */
.section li.clickable-card:hover {
  background-color: var(--primary-50); /* 鼠标悬停时背景变浅 */
  border-color: var(--primary-300); /* 边框颜色变化 */
  transform: translateY(-2px); /* 稍微上浮 */
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* 增加阴影 */
}

.section li strong {
  font-size: 1.1em;
  color: var(--gray-800);
}

/* 移除原有的 li 内部 button 的样式，因为现在不再使用 */
/* .section li button {
  background-color: var(--secondary-500);
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  align-self: flex-start;
  margin-top: 5px;
}

.section li button:hover {
  background-color: var(--secondary-600);
} */

.experiment-step {
  background-color: var(--gray-100);
  border: 1px dashed var(--gray-300);
  border-radius: 5px;
  padding: 15px;
  margin-bottom: 15px;
}

.experiment-step input[type='text'],
.experiment-step input[type='number'],
.experiment-step textarea {
  width: calc(100% - 20px);
  padding: 8px 10px;
  margin-top: 5px;
  margin-bottom: 10px;
  border: 1px solid var(--gray-300);
  border-radius: 4px;
}

.experiment-step input[type='radio'] {
  margin-right: 5px;
}

.experiment-step label {
  font-weight: bold;
  margin-top: 10px;
  display: block;
}

.review-form {
  margin-top: 20px;
  padding: 15px;
  background-color: var(--gray-100);
  border-radius: 8px;
  border: 1px solid var(--gray-200);
}

.review-form label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.review-form input[type='number'],
.review-form textarea {
  width: calc(100% - 20px);
  padding: 8px 10px;
  margin-bottom: 10px;
  border: 1px solid var(--gray-300);
  border-radius: 4px;
}

.review-form button {
  background-color: var(--primary-500);
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.review-form button:hover:not(:disabled) {
  background-color: var(--primary-600);
}

.review-form button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.review-form .success {
  color: var(--green-600);
  margin-top: 10px;
  font-weight: bold;
}

.review-form .error {
  color: var(--red-600);
  margin-top: 10px;
  font-weight: bold;
}

.output {
  background-color: var(--gray-800);
  color: var(--gray-100);
  padding: 20px;
  margin-top: 20px;
  border-radius: 8px;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
}

.output h2 {
  color: var(--primary-300);
  margin-top: 0;
  margin-bottom: 15px;
}

.output pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.4;
}

/* 变量定义，可以放在一个单独的CSS文件或顶层样式中 */
:root {
  --primary-50: #e0f2f7;
  --primary-100: #b3e0e7;
  --primary-200: #80ceda;
  --primary-300: #4dc2cb;
  --primary-400: #26b1bb;
  --primary-500: #00a0ac; /* 主色 */
  --primary-600: #008f9c;
  --primary-700: #007e8c;
  --primary-800: #006d7b;
  --primary-900: #005c6b;

  --secondary-50: #fef3e6;
  --secondary-100: #fde2b4;
  --secondary-200: #fbc67b;
  --secondary-300: #f9a941;
  --secondary-400: #f78d0d;
  --secondary-500: #f57200; /* 次要色 */
  --secondary-600: #de6600;
  --secondary-700: #c75a00;
  --secondary-800: #b04d00;
  --secondary-900: #994200;

  --gray-50: #f8f9fa;
  --gray-100: #e9ecef;
  --gray-200: #dee2e6;
  --gray-300: #ced4da;
  --gray-400: #adb5bd;
  --gray-500: #6c757d;
  --gray-600: #495057;
  --gray-700: #343a40;
  --gray-800: #212529;
  --gray-900: #1a1d20;

  --white: #ffffff;
  --black: #000000;
  --red-600: #dc3545;
  --green-600: #28a745;
}
</style>
