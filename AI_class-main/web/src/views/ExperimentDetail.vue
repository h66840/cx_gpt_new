<template>
  <div class="experiment-detail-container">
    <component
      :is="detailComponent"
      v-if="experiment"
      :experiment="experiment"
      :reviews="reviews"
      :isLoading="isLoading"
      :error="error"
      @start-experiment="startExperiment"
      @go-back="goBack"
      @open-rating-modal="openRatingModal"
      @close-rating-modal="closeRatingModal"
      @review-submitted="handleReviewSubmitted"
    />

    <a-spin v-else-if="isLoading" tip="加载中..." size="large" class="loading-container">
      <div style="height: 400px"></div>
    </a-spin>

    <a-alert v-else-if="error" type="error" show-icon :message="error" class="error-container" />

    <div v-else class="not-found-container">
      <a-result status="404" title="404" sub-title="抱歉，您访问的实验不存在">
        <template #extra>
          <a-button type="primary" @click="goBack">返回实验列表</a-button>
        </template>
      </a-result>
    </div>

    <RatingModal
      v-if="isRatingModalOpen"
      :experimentId="experiment?.id"
      @close="closeRatingModal"
      @review-submitted="handleReviewSubmitted"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RatingModal from '@/views/RatingModal.vue'
import ExperimentDetailTypeA from './ExperimentDetailTypeA.vue'
import ExperimentDetailTypeB from './ExperimentDetailTypeB.vue'
import { experimentApi } from '@/apis/experiment_api'

const route = useRoute()
const router = useRouter()

const experiment = ref(null)
const reviews = ref([])
const isLoading = ref(true)
const error = ref(null)
const isRatingModalOpen = ref(false)

// 根據實驗類型動態選擇組件
const detailComponent = computed(() => {
  if (!experiment.value) return null

  const experimentType = experiment.value.type || 'A'

  switch (experimentType) {
    case 'A':
      return ExperimentDetailTypeA
    case 'B':
      return ExperimentDetailTypeB
    default:
      return ExperimentDetailTypeA // 默認使用類型A
  }
})

const startExperiment = () => {
  if (experiment.value && experiment.value.id) {
    router.push({ name: 'ExperimentExecution', params: { id: experiment.value.id } })
  } else {
    console.error('无法开始实验：实验数据未加载或缺少ID')
    alert('实验数据未加载完成，请稍候再试。')
  }
}

const goBack = () => {
  router.back()
}

const openRatingModal = () => {
  isRatingModalOpen.value = true
}

const closeRatingModal = () => {
  isRatingModalOpen.value = false
}

const handleReviewSubmitted = async () => {
  closeRatingModal()
  const experimentId = route.params.id
  if (experimentId) {
    await fetchExperimentDetail(experimentId)
  }
}

const fetchExperimentDetail = async (id) => {
  isLoading.value = true
  error.value = null
  try {
    const data = await experimentApi.getExperimentDetails(id)
    experiment.value = data
    reviews.value = data.reviews || []
    console.log(`获取实验 ${id} 详情成功:`, data)
    console.log(`实验类型: ${data.type}`)
  } catch (err) {
    console.error('Error fetching experiment detail:', err)
    if (err.response && err.response.status === 404) {
      error.value = '该实验不存在。'
    } else if (err.detail === '无效的令牌' || (err.response && err.response.status === 401)) {
      error.value = '用户认证失败，请重新登录。'
      router.push('/login')
    } else {
      error.value = `无法加载实验详情: ${
        err.message || (err.response ? err.response.data.detail : '未知错误')
      }`
    }
    experiment.value = null
    reviews.value = []
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  const experimentId = route.params.id
  console.log('实验详情页组件加载，从路由获取到的实验ID是:', experimentId)
  if (experimentId) {
    fetchExperimentDetail(experimentId)
  } else {
    error.value = '无效的实验 ID。'
    isLoading.value = false
  }
})
</script>

<style scoped>
.experiment-detail-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.error-container {
  margin: 24px;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
}

.not-found-container {
  margin-top: 48px;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
}
</style>
