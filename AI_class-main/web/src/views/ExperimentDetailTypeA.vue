<template>
  <div class="experiment-detail-type-a">
    <a-page-header class="top-nav" :ghost="false" @back="goBack">
      <template #title>
        <div class="header-title">
          <experiment-outlined class="header-icon" />
          <span>{{ experiment ? experiment.title : '视觉推理实验' }}</span>
        </div>
      </template>
      <template #subTitle>
        <a-tag color="blue" v-if="experiment?.tag">{{ experiment.tag }}</a-tag>
      </template>
      <template #extra>
        <a-space>
          <a-button
            type="primary"
            @click="startExperiment"
            :disabled="!experiment"
            class="start-button"
          >
            <template #icon><play-circle-outlined /></template>
            开始实验
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-spin :spinning="isLoading" tip="加载中..." size="large">
      <a-alert v-if="error" type="error" show-icon :message="error" class="error-message" />

      <div v-if="experiment" class="detail-content">
        <div class="top-layout">
          <div class="overview-area">
            <a-card :bordered="false" class="overview-section">
              <a-row>
                <a-col :xs="24" :md="16">
                  <div class="experiment-title">
                    {{ experiment.title }}
                  </div>

                  <div class="tag-and-stats">
                    <a-tag color="blue">{{ experiment.tag }}</a-tag>
                    <div class="course-stats">
                      <a-tag color="blue">
                        <template #icon><eye-outlined /></template>
                        视觉推理
                      </a-tag>
                      <a-tag color="blue">
                        <template #icon><bulb-outlined /></template>
                        智能分析
                      </a-tag>
                      <a-tag color="blue">
                        <template #icon><clock-circle-outlined /></template>
                        30 分钟
                      </a-tag>
                    </div>
                  </div>
                </a-col>
              </a-row>

              <a-image
                :src="experiment.image"
                :alt="experiment.title"
                class="detail-image"
                :preview="false"
              />

              <div class="action-buttons">
                <a-button type="default" size="large" v-if="userHasJoined">
                  <template #icon><check-circle-outlined /></template>
                  已加入
                </a-button>
                <a-button type="primary" size="large" @click="startExperiment">
                  <template #icon><play-circle-outlined /></template>
                  开始学习
                </a-button>
              </div>
            </a-card>
          </div>

          <div class="review-sidebar" id="review-sidebar">
            <a-card :bordered="false" class="review-section">
              <template #title>
                <div class="card-title">
                  <star-filled class="card-icon" />
                  实验评价
                </div>
              </template>

              <a-rate
                :value="experiment.overall_rating"
                disabled
                allow-half
                class="overall-rating"
              />
              <a-typography-text class="rating-text">
                {{ experiment.overall_rating }} / 5
              </a-typography-text>

              <a-divider />

              <div v-if="experiment.aspect_ratings" class="aspect-ratings">
                <a-typography-title :level="5">各项评分</a-typography-title>
                <a-list size="small" :split="false">
                  <a-list-item v-for="(rating, aspect) in experiment.aspect_ratings" :key="aspect">
                    <a-row style="width: 100%">
                      <a-col :span="12">{{ aspect }}:</a-col>
                      <a-col :span="12">
                        <a-rate :value="rating" disabled allow-half size="small" />
                      </a-col>
                    </a-row>
                  </a-list-item>
                </a-list>
              </div>

              <a-button type="primary" block @click="openRatingModal" class="rate-button">
                <template #icon><star-outlined /></template>
                我要评分
              </a-button>

              <a-divider orientation="left">评论 ({{ reviews.length }})</a-divider>

              <div v-if="reviews.length === 0" class="empty-comments">
                <a-empty description="暂无评论，快来发表第一条评论吧！" />
              </div>

              <div v-else class="comments-list">
                <a-list :data-source="reviews" :pagination="{ pageSize: 5 }" item-layout="vertical">
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
                            />
                            <div
                              v-if="
                                item.aspect_ratings && Object.keys(item.aspect_ratings).length > 0
                              "
                              class="aspect-comment"
                            >
                              <a-typography-text type="secondary">各项评分: </a-typography-text>
                              <a-typography-text>
                                {{
                                  Object.entries(item.aspect_ratings)
                                    .map(([key, val]) => `${key}: ${val}`)
                                    .join(', ')
                                }}
                              </a-typography-text>
                            </div>
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

        <div class="bottom-content-area">
          <a-tabs
            :activeKey="activeTab"
            @update:activeKey="activeTab = $event"
            class="content-tabs"
          >
            <a-tab-pane key="intro" tab="实验介绍">
              <a-card :bordered="false" class="content-card">
                <a-typography-title :level="4">视觉推理实验介绍</a-typography-title>
                <a-typography-paragraph>{{ experiment.description }}</a-typography-paragraph>
                <a-alert
                  message="实验特色"
                  description="本实验专注于视觉推理能力训练，通过分析图像内容进行智能推理和判断。"
                  type="info"
                  show-icon
                  class="feature-alert"
                />
              </a-card>
            </a-tab-pane>

            <a-tab-pane key="catalog" tab="实验步骤">
              <a-card :bordered="false" class="content-card">
                <div v-if="experiment.curriculum && experiment.curriculum.length > 0">
                  <a-typography-title :level="4">实验步骤</a-typography-title>
                  <a-timeline>
                    <a-timeline-item
                      v-for="(step, index) in experiment.curriculum"
                      :key="index"
                      :color="index % 2 === 0 ? 'blue' : 'green'"
                    >
                      <a-typography-paragraph>{{ step.question }}</a-typography-paragraph>
                    </a-timeline-item>
                  </a-timeline>
                </div>
                <a-empty v-else description="暂无实验步骤" />
              </a-card>
            </a-tab-pane>

            <a-tab-pane key="qa" tab="常见问题">
              <a-card :bordered="false" class="content-card">
                <a-typography-title :level="4">常见问题</a-typography-title>
                <a-collapse>
                  <a-collapse-panel key="1" header="如何开始视觉推理实验？">
                    <p>点击页面上方的"开始实验"按钮即可进入视觉推理实验环境。</p>
                  </a-collapse-panel>
                  <a-collapse-panel key="2" header="视觉推理实验的评分标准是什么？">
                    <p>实验成绩根据您对图像的分析准确性、推理逻辑性和判断正确性进行综合评分。</p>
                  </a-collapse-panel>
                  <a-collapse-panel key="3" header="遇到图像加载问题怎么办？">
                    <p>请检查网络连接，或刷新页面重新加载图像。如问题持续，请联系技术支持。</p>
                  </a-collapse-panel>
                </a-collapse>
              </a-card>
            </a-tab-pane>

            <a-tab-pane key="review" tab="实验评价">
              <a-card :bordered="false" class="content-card">
                <a-typography-title :level="4">实验评价</a-typography-title>
                <a-typography-paragraph>
                  <a-button
                    type="primary"
                    @click="
                      () =>
                        document
                          .getElementById('review-sidebar')
                          .scrollIntoView({ behavior: 'smooth' })
                    "
                  >
                    <template #icon><message-outlined /></template>
                    查看所有评价
                  </a-button>
                </a-typography-paragraph>
              </a-card>
            </a-tab-pane>
          </a-tabs>
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
  PlayCircleOutlined,
  CheckCircleOutlined,
  StarOutlined,
  StarFilled,
  EyeOutlined,
  BulbOutlined,
  ClockCircleOutlined,
  MessageOutlined,
  ExperimentOutlined
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
const activeTab = ref('intro')
const userHasJoined = ref(false)

const startExperiment = () => {
  if (props.experiment && props.experiment.id) {
    userHasJoined.value = true
    emit('start-experiment')
  } else {
    console.error('无法开始实验：实验数据未加载或缺少ID')
    alert('实验数据未加载完成，请稍候再试。')
  }
}

const goBack = () => {
  emit('go-back')
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
</script>

<style scoped>
.experiment-detail-type-a {
  max-width: 1600px; /* 從 1200px 增加到 1600px */
  margin: 0 auto;
  padding: 0 16px 24px; /* 減少左右 padding */
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f5f7fa;
  min-height: 100vh;
  user-select: text;
}

.top-nav {
  margin-bottom: 20px; /* 從 24px 減少到 20px */
  background: linear-gradient(135deg, #ffffff 0%, #e6f7ff 100%);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border-left: 4px solid #1890ff;
  user-select: text;
}

.header-title {
  display: flex;
  align-items: center;
  font-size: 20px;
  font-weight: 600;
  color: #1890ff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.header-icon {
  font-size: 24px;
  margin-right: 8px;
  color: #1890ff;
}

.start-button {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  border: none;
  font-weight: 500;
  height: 40px;
  padding: 0 20px;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.2);
  transition: all 0.3s ease;
}

.start-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.experiment-title {
  font-size: 28px;
  font-weight: 700;
  color: #222;
  margin-top: 0 !important;
  margin-bottom: 16px !important;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.content-tabs :deep(.ant-tabs-tab) {
  font-size: 16px;
  font-weight: 500;
  padding: 12px 16px;
  transition: all 0.3s ease;
}

.content-tabs :deep(.ant-tabs-tab-active) {
  color: #1890ff;
  font-weight: 600;
}

.content-tabs :deep(.ant-tabs-ink-bar) {
  background: linear-gradient(90deg, #1890ff 0%, #096dd9 100%);
  height: 3px;
  border-radius: 3px 3px 0 0;
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

.action-buttons button {
  border-radius: 6px;
  height: 44px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-buttons button:nth-child(2) {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  border: none;
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.2);
}

.action-buttons button:nth-child(2):hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.rate-button {
  background: linear-gradient(135deg, #faad14 0%, #d48806 100%) !important;
  border: none !important;
  box-shadow: 0 2px 6px rgba(250, 173, 20, 0.2) !important;
  height: 40px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.rate-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(250, 173, 20, 0.3) !important;
}

.error-message {
  margin: 20px 0; /* 從 24px 減少到 20px */
}

.detail-content {
  margin-top: 20px; /* 從 24px 減少到 20px */
  user-select: text;
}

.top-layout {
  display: flex;
  gap: 20px; /* 從 24px 減少到 20px */
  margin-bottom: 20px; /* 從 24px 減少到 20px */
}

.overview-area {
  flex: 2;
  min-width: 0;
}

.overview-section {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.tag-and-stats {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px; /* 從 24px 減少到 20px */
}

.course-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-image {
  width: 100%;
  border-radius: 8px;
  margin-bottom: 20px; /* 從 24px 減少到 20px */
  max-height: 400px;
  object-fit: cover;
}

.action-buttons {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.review-sidebar {
  flex: 1;
  min-width: 280px; /* 從 300px 減少到 280px */
}

.review-section {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  height: 100%;
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

.aspect-ratings {
  margin-bottom: 20px; /* 從 24px 減少到 20px */
}

.rate-button {
  margin: 16px 0;
}

.empty-comments {
  padding: 20px 0; /* 從 24px 減少到 20px */
}

.comments-list {
  max-height: 400px;
  overflow-y: auto;
}

.aspect-comment {
  margin: 8px 0;
}

.bottom-content-area {
  margin-top: 20px; /* 從 24px 減少到 20px */
  user-select: text;
}

.content-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 16px;
  background-color: #fff;
  padding: 0 16px;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.content-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.feature-alert {
  margin-top: 16px;
}

.not-found {
  margin-top: 48px;
}

@media (max-width: 1400px) {
  .top-layout {
    flex-direction: column;
  }

  .review-sidebar {
    min-width: 100%;
  }
}

@media (max-width: 768px) {
  .top-layout {
    flex-direction: column;
  }

  .review-sidebar {
    min-width: 100%;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons button {
    width: 100%;
  }
}
</style> 