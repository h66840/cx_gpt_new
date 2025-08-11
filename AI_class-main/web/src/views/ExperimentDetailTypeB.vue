<template>
  <div class="experiment-detail-type-b">
    <a-page-header class="top-nav" :ghost="false" @back="goBack">
      <template #title>
        <div class="header-title">
          <robot-outlined class="header-icon" />
          <span>{{ experiment ? experiment.title : '大模型应用实验' }}</span>
        </div>
      </template>
      <template #subTitle>
        <a-tag color="green" v-if="experiment?.tag">{{ experiment.tag }}</a-tag>
      </template>
      <template #extra>
        <a-space>
          <a-button
            type="primary"
            @click="startExperiment"
            :disabled="!experiment"
            class="start-button"
          >
            <template #icon><rocket-outlined /></template>
            启动实验
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-spin :spinning="isLoading" tip="加载中..." size="large">
      <a-alert v-if="error" type="error" show-icon :message="error" class="error-message" />

      <div v-if="experiment" class="detail-content">
        <div class="hero-section">
          <a-card :bordered="false" class="hero-card">
            <a-row :gutter="24">
              <a-col :xs="24" :md="12">
                <div class="hero-content">
                  <!-- 標題與描述字體統一 -->
                  <div class="hero-title">{{ experiment.title }}</div>
                  <div class="hero-description">{{ experiment.description }}</div>

                  <!-- 美化後的實驗資訊 -->
                  <div class="hero-stats">
                    <div class="stat-item">
                      <clock-circle-outlined class="stat-icon" />
                      <span class="stat-label">实验时长</span>
                      <span class="stat-value">45 分钟</span>
                    </div>
                    <div class="stat-item">
                      <star-outlined class="stat-icon" />
                      <span class="stat-label">难度等级</span>
                      <span class="stat-value">3 / 5</span>
                    </div>
                    <div class="stat-item">
                      <thunderbolt-outlined class="stat-icon" />
                      <span class="stat-label">完成率</span>
                      <span class="stat-value">0%</span>
                    </div>
                  </div>

                  <div class="hero-actions">
                    <a-button type="primary" size="large" @click="startExperiment">
                      <template #icon><rocket-outlined /></template>
                      立即开始
                    </a-button>
                    <a-button size="large">
                      <template #icon><book-outlined /></template>
                      查看教程
                    </a-button>
                  </div>
                </div>
              </a-col>
              <a-col :xs="24" :md="12">
                <div class="hero-image">
                  <a-image
                    :src="experiment.image"
                    :alt="experiment.title"
                    class="main-image"
                    :preview="false"
                  />
                </div>
              </a-col>
            </a-row>
          </a-card>
        </div>

        <div class="content-layout">
          <!-- 左側導航欄 -->
          <div class="sidebar-nav">
            <a-card :bordered="false" class="nav-card">
              <div class="nav-menu">
                <div
                  v-for="item in navItems"
                  :key="item.key"
                  class="nav-item"
                  :class="{ active: activeTab === item.key }"
                  @click="activeTab = item.key"
                >
                  <div class="nav-icon">
                    <component :is="item.icon" />
                  </div>
                  <span class="nav-text">{{ item.title }}</span>
                </div>
              </div>
            </a-card>
          </div>

          <!-- 右側內容區域 -->
          <div class="main-content">
            <a-card :bordered="false" class="content-card">
              <!-- 實驗概覽 -->
              <div v-if="activeTab === 'overview'" class="tab-content">
                <a-typography-title :level="3">实验概览</a-typography-title>
                <a-row :gutter="16">
                  <a-col :span="8">
                    <a-card class="feature-card">
                      <template #title>
                        <a-typography-title :level="5">
                          <bulb-outlined /> 场景图生成
                        </a-typography-title>
                      </template>
                      <p>学习如何使用由粗到细的场景图生成方法把非结构化知识转为结构化知识。</p>
                    </a-card>
                  </a-col>
                  <a-col :span="8">
                    <a-card class="feature-card">
                      <template #title>
                        <a-typography-title :level="5">
                          <code-outlined /> 子问题分解
                        </a-typography-title>
                      </template>
                      <p>学习把大问题拆解为一系列更小、可被验证的、有逻辑顺序的子问题。</p>
                    </a-card>
                  </a-col>
                  <a-col :span="8">
                    <a-card class="feature-card">
                      <template #title>
                        <a-typography-title :level="5">
                          <file-text-outlined /> 智能体设计
                        </a-typography-title>
                      </template>
                      <p>学习智能体对应的结构，并编程实现自己的智能体。</p>
                    </a-card>
                  </a-col>
                </a-row>
              </div>

              <!-- 實驗步驟 -->
              <div v-if="activeTab === 'steps'" class="tab-content">
                <a-typography-title :level="3"></a-typography-title>
                <div v-if="experiment.curriculum && experiment.curriculum.length > 0">
                  <a-steps direction="vertical" size="small">
                    <a-step
                      v-for="(step, index) in experiment.curriculum"
                      :key="index"
                      :title="`步骤 ${index + 1}`"
                      :description="step.question"
                      :status="getStepStatus(index)"
                    />
                  </a-steps>
                </div>
                <a-empty v-else description="暂无师资介绍" />
              </div>

              <!-- 學習資源 -->
              <div v-if="activeTab === 'resources'" class="tab-content">
                <a-typography-title :level="3">学习资源</a-typography-title>
                <a-list :data-source="learningResources" item-layout="horizontal">
                  <template #renderItem="{ item }">
                    <a-list-item>
                      <a-list-item-meta>
                        <template #avatar>
                          <a-avatar :icon="item.icon" :style="{ backgroundColor: item.color }" />
                        </template>
                        <template #title>
                          <a :href="item.url" target="_blank">{{ item.title }}</a>
                        </template>
                        <template #description>{{ item.description }}</template>
                      </a-list-item-meta>
                    </a-list-item>
                  </template>
                </a-list>
              </div>

              <!-- 常見問題 -->
              <div v-if="activeTab === 'faq'" class="tab-content">
                <a-typography-title :level="3">常见问题</a-typography-title>
                <a-collapse>
                  <a-collapse-panel key="1" header="如何开始大模型应用实验？">
                    <p>
                      点击"立即开始"按钮，系统会自动为您配置实验环境，然后按照步骤指引进行操作。
                    </p>
                  </a-collapse-panel>
                  <a-collapse-panel key="2" header="实验需要什么前置知识？">
                    <p>建议具备基础的编程知识和AI概念理解，但我们会提供详细的学习材料。</p>
                  </a-collapse-panel>
                  <a-collapse-panel key="3" header="实验过程中遇到问题怎么办？">
                    <p>可以查看"学习资源"中的文档，或在评论区提问，我们会及时回复。</p>
                  </a-collapse-panel>
                </a-collapse>
              </div>

              <!-- 考核要求 -->
              <div v-if="activeTab === 'assessment'" class="tab-content">
                <a-typography-title :level="3">考核说明</a-typography-title>
                <a-list :data-source="assessmentRequirements" item-layout="vertical">
                  <template #renderItem="{ item, index }">
                    <a-list-item>
                      <a-list-item-meta>
                        <template #avatar>
                          <a-avatar :style="{ backgroundColor: '#1890ff' }">{{
                            index + 1
                          }}</a-avatar>
                        </template>
                        <template #title>
                          <a-typography-text strong>{{ item.title }}</a-typography-text>
                        </template>
                        <template #description>
                          <a-typography-paragraph>{{ item.description }}</a-typography-paragraph>
                        </template>
                      </a-list-item-meta>
                    </a-list-item>
                  </template>
                </a-list>
              </div>

              <!-- 學習記錄 -->
              <div v-if="activeTab === 'records'" class="tab-content">
                <a-typography-title :level="3">学习记录</a-typography-title>
                <a-empty description="暂无学习记录" />
              </div>
            </a-card>
          </div>

          <!-- 右側評價欄 -->
          <div class="rating-sidebar">
            <a-card :bordered="false" class="rating-card">
              <template #title>
                <div class="card-title">
                  <star-filled class="card-icon" />
                  实验评价
                </div>
              </template>

              <div class="rating-summary">
                <a-rate
                  :value="experiment.overall_rating"
                  disabled
                  allow-half
                  class="overall-rating"
                />
                <a-typography-text class="rating-text">
                  {{ experiment.overall_rating }} / 5
                </a-typography-text>
                <a-typography-text type="secondary">
                  基于 {{ reviews.length }} 条评价
                </a-typography-text>
              </div>

              <a-divider />

              <a-button type="primary" block @click="openRatingModal" class="rate-button">
                <template #icon><star-outlined /></template>
                我要评分
              </a-button>

              <a-divider orientation="left">最新评论</a-divider>

              <div v-if="reviews.length === 0" class="empty-comments">
                <a-empty description="暂无评论" />
              </div>

              <div v-else class="comments-list">
                <a-list :data-source="reviews.slice(0, 3)" item-layout="vertical">
                  <template #renderItem="{ item }">
                    <a-list-item>
                      <a-comment
                        :author="item.user_name"
                        :datetime="new Date(item.timestamp).toLocaleString()"
                      >
                        <template #content>
                          <div>
                            <a-rate
                              v-if="item.rating !== null"
                              :value="item.rating"
                              disabled
                              allow-half
                              size="small"
                            />
                            <a-typography-paragraph>{{ item.comment }}</a-typography-paragraph>
                          </div>
                        </template>
                      </a-comment>
                    </a-list-item>
                  </template>
                </a-list>
              </div>
            </a-card>
          </div>
        </div>
      </div>

      <div v-else-if="!isLoading && !error" class="not-found">
        <a-result status="404" title="404" sub-title="抱歉，您访问的实验不存在">
          <template #extra>
            <a-button type="primary" @click="goBack">返回实验列表</a-button>
          </template>
        </a-result>
      </div>
    </a-spin>

    <RatingModal
      v-if="isRatingModalOpen"
      :experimentId="experiment?.id"
      @close="closeRatingModal"
      @review-submitted="handleReviewSubmitted"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RatingModal from '@/views/RatingModal.vue'
import { experimentApi } from '@/apis/experiment_api'
import {
  RocketOutlined,
  RobotOutlined,
  StarOutlined,
  StarFilled,
  BulbOutlined,
  CodeOutlined,
  FileTextOutlined,
  BookOutlined,
  FileTextOutlined as DocumentOutlined,
  ExperimentOutlined,
  CheckCircleOutlined,
  HistoryOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined
} from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()

// 接收 props
const props = defineProps({
  experiment: {
    type: Object,
    required: true
  },
  reviews: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  }
})

// 定義事件
const emit = defineEmits([
  'start-experiment',
  'go-back',
  'open-rating-modal',
  'close-rating-modal',
  'review-submitted'
])

const isRatingModalOpen = ref(false)
const activeTab = ref('overview')
const userHasJoined = ref(false)

// 導航項目配置
const navItems = ref([
  {
    key: 'overview',
    title: '实验介绍',
    icon: DocumentOutlined
  },
  {
    key: 'steps',
    title: '师资介绍',
    icon: ExperimentOutlined
  },
  {
    key: 'resources',
    title: '实验指南',
    icon: BookOutlined
  },
  {
    key: 'faq',
    title: '实验资源',
    icon: BulbOutlined
  },
  {
    key: 'assessment',
    title: '考核要求',
    icon: CheckCircleOutlined
  },
  {
    key: 'records',
    title: '学习记录',
    icon: HistoryOutlined
  }
])

// 考核要求数据
const assessmentRequirements = ref([
  {
    title: '掌握场景图生成的实验方法',
    description:
      '学习通过精准的认知工程，驱动视觉大模型（VLM）遵循自定义规则，通过由粗到细的场景图生成方法，将非结构化的图像信息，转化为结构化的知识（JSON），并构建为场景图（Scene Graph）。'
  },
  {
    title: '培养对AI能力的批判性评估思维',
    description:
      '学习对照事实（原始图片），系统性地分析和评估AI生成内容的准确性、完整性和潜在的“幻觉”（Hallucination），深刻理解当前AI模型的能力边界和“认知”偏差。'
  },
  {
    title: '学习复杂问题的逻辑分解策略',
    description:
      '面对AI无法一次性回答的复杂或隐性问题，学习如何将其拆解为一系列更小、可被验证的、有逻辑顺序的子问题。这是高级问题解决能力和算法思维的核心体现。'
  },
  {
    title: '理解智能体（Agent）的迭代式推理模式',
    description:
      '从“单次问答”模式进阶，理解Agent如何通过“感知-思考-行动”（Perceive-Think-Act）的循环，进行多步骤、有针对性的信息搜集，从而解决单一模型无法处理的难题。'
  },
  {
    title: '实践动态知识库的构建与补全',
    description:
      '将Agent通过“重新观察”获得的新知识，增补到原有的场景图中。直观体验AI的“世界模型”（World Model）是如何通过与环境的交互而动态增长和修正的。'
  }
])

// 學習資源數據
const learningResources = ref([
  {
    title: '大模型应用指南',
    description: '详细的使用教程和最佳实践',
    url: '#',
    icon: 'A',
    color: '#1890ff'
  },
  {
    title: 'API 文档',
    description: '完整的接口文档和示例代码',
    url: '#',
    icon: 'B',
    color: '#52c41a'
  },
  {
    title: '视频教程',
    description: '手把手教学视频',
    url: '#',
    icon: 'C',
    color: '#faad14'
  }
])

const startExperiment = () => {
  if (props.experiment && props.experiment.id) {
    userHasJoined.value = true
    router.push({ name: 'ExperimentExecutionTypeB', params: { id: props.experiment.id } })
  } else {
    console.error('无法开始实验：实验数据未加载或缺少ID')
    alert('实验数据未加载完成，请稍候再试。')
  }
}

const goBack = () => {
  emit('go-back')
}

const getStepStatus = (index) => {
  // 這裡可以根據實際的步驟狀態返回不同的狀態
  return 'wait'
}

const openRatingModal = () => {
  emit('open-rating-modal')
}

const closeRatingModal = () => {
  emit('close-rating-modal')
}

const handleReviewSubmitted = async () => {
  emit('review-submitted')
}

// 移除不需要的數據獲取邏輯，因為數據已經從父組件傳入
</script>

<style scoped>
.experiment-detail-type-b {
  max-width: 1600px; /* 擴大最大寬度 */
  margin: 0 auto;
  padding: 0 16px 24px; /* 減少左右 padding */
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f8f9fa;
  min-height: 100vh;
  user-select: text;
}

/* header、按鈕、主色調全部藍色 */
.top-nav {
  border-left: 4px solid #1890ff;
  background: linear-gradient(135deg, #ffffff 0%, #e6f7ff 100%);
  margin-bottom: 24px;
  background: linear-gradient(135deg, #ffffff 0%, #e6f7ff 100%);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-left: 4px solid #1890ff;
  user-select: text;
}
.header-title,
.card-title {
  color: #1890ff;
}
.header-icon,
.stat-icon {
  color: #1890ff;
}
.start-button {
  background: linear-gradient(135deg, #1890ff 0%, #0050b3 100%);
  border: none;
  color: #fff;
  font-weight: 500;
  height: 40px;
  padding: 0 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
  transition: all 0.3s ease;
}
.start-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.3);
}
.hero-actions button:first-child {
  background: linear-gradient(135deg, #1890ff 0%, #0050b3 100%);
  border: none;
  color: #fff;
}
.hero-actions button:first-child:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.3);
}

.error-message {
  margin: 24px 0;
}

.detail-content {
  margin-top: 24px;
  user-select: text;
}

.hero-section {
  margin-bottom: 32px;
}

.hero-card {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  background: linear-gradient(135deg, #ffffff 0%, #f6ffed 100%);
}

.hero-content {
  padding: 20px 0; /* 減少 hero 內邊距 */
}

/* 標題與描述字體統一 */
.hero-title {
  font-size: 28px;
  font-weight: 700;
  color: #222;
  margin-bottom: 12px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.hero-description {
  font-size: 16px;
  color: #555;
  margin-bottom: 24px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* 美化後的實驗資訊 */
.hero-stats {
  display: flex;
  gap: 24px; /* 減少統計項目間距 */
  margin-bottom: 24px;
}
.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f0f9ff;
  border-radius: 8px;
  padding: 8px 16px;
}
.stat-icon {
  color: #1890ff;
  font-size: 22px;
}
.stat-label {
  color: #666;
  font-size: 14px;
}
.stat-value {
  color: #222;
  font-size: 16px;
  font-weight: 600;
}

.hero-actions {
  display: flex;
  gap: 16px;
}

.hero-actions button {
  height: 48px;
  font-weight: 500;
  border-radius: 8px;
}

.hero-actions button:first-child {
  background: linear-gradient(135deg, #1890ff 0%, #0050b3 100%);
  border: none;
  color: #fff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
}

.hero-actions button:first-child:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.3);
}

.hero-image {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.main-image {
  width: 100%;
  border-radius: 12px;
  max-height: 400px;
  object-fit: cover;
}

/* 新的佈局樣式 */
.content-layout {
  display: grid;
  grid-template-columns: 220px 1fr 280px; /* 調整三欄寬度 */
  gap: 20px; /* 減少間距 */
  align-items: start;
}

.sidebar-nav {
  position: sticky;
  top: 24px;
}

.nav-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  background: #ffffff;
}

.nav-menu {
  padding: 12px 0; /* 減少導航內邊距 */
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 8px;
  margin: 4px 12px;
  color: #666;
}

/* 藍色主題 */
.nav-item.active {
  background-color: #e6f7ff;
  color: #1890ff;
  border-left: 3px solid #1890ff;
  margin-left: 8px;
}
.nav-item:hover {
  background-color: #f0f9ff;
  color: #1890ff;
}

.nav-icon {
  margin-right: 12px;
  font-size: 18px;
  display: flex;
  align-items: center;
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
}

.main-content {
  min-width: 0;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  background: #ffffff;
}

.tab-content {
  padding: 20px; /* 減少內邊距 */
}

.feature-card {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.rating-sidebar {
  position: sticky;
  top: 24px;
}

.rating-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  background: #ffffff;
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
}

.card-icon {
  margin-right: 8px;
  color: #faad14;
  font-size: 20px;
}

.rating-summary {
  text-align: center;
  margin-bottom: 16px;
}

.overall-rating {
  font-size: 24px;
  color: #faad14;
}

.rating-text {
  margin-left: 8px;
  font-size: 16px;
  font-weight: 600;
}

.rate-button {
  background: linear-gradient(135deg, #faad14 0%, #d48806 100%) !important;
  border: none !important;
  box-shadow: 0 2px 8px rgba(250, 173, 20, 0.2) !important;
  height: 40px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.rate-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(250, 173, 20, 0.3) !important;
}

.empty-comments {
  padding: 24px 0;
}

.comments-list {
  max-height: 400px;
  overflow-y: auto;
}

.not-found {
  margin-top: 48px;
}

/* 響應式調整 */
@media (max-width: 1400px) {
  .content-layout {
    grid-template-columns: 220px 1fr;
  }

  .rating-sidebar {
    grid-column: 1 / -1;
    margin-top: 20px;
  }
}

@media (max-width: 768px) {
  .content-layout {
    grid-template-columns: 1fr;
  }

  .sidebar-nav {
    position: static;
    margin-bottom: 20px;
  }

  .rating-sidebar {
    position: static;
  }

  .nav-menu {
    display: flex;
    overflow-x: auto;
    padding: 8px 0; /* 進一步減少移動端內邊距 */
  }

  .nav-item {
    flex-shrink: 0;
    margin: 0 6px; /* 減少移動端間距 */
    padding: 10px 12px; /* 減少移動端內邊距 */
  }
}
</style> 