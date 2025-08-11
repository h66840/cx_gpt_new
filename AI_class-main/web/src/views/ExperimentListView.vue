<template>
  <div class="experiment-page">
    <a-row class="header-section">
      <a-col :span="24">
        <div class="header">
          <a-typography-title :level="2" class="page-title">
            <experiment-outlined /> 人工智能创新实验课
          </a-typography-title>
          <a-input-search
            v-model:value="search"
            placeholder="搜索课程/关键词..."
            class="search-input"
            :style="{ width: '300px' }"
            allow-clear
          >
            <template #prefix>
              <search-outlined />
            </template>
          </a-input-search>
        </div>
      </a-col>
    </a-row>

    <a-row class="filter-section">
      <a-col :span="24">
        <div class="category-tags">
          <a-space wrap :size="12">
            <a-tag
              v-for="(tag, index) in tags"
              :key="tag.label"
              :color="tag.active ? 'blue' : tag.hot ? 'volcano' : undefined"
              class="custom-tag"
              :class="{ active: tag.active }"
              @click="selectTag(index)"
            >
              {{ tag.label }}
              <span v-if="tag.emoji" class="emoji">{{ tag.emoji }}</span>
              <a-badge
                v-if="tag.badge"
                :count="tag.badge"
                :number-style="{ backgroundColor: '#ff9130' }"
              />
            </a-tag>
            <a-button type="link" class="more-btn"> 更多分类 <right-outlined /> </a-button>
          </a-space>
        </div>
      </a-col>
    </a-row>

    <a-spin :spinning="isLoading" tip="加载中...">
      <a-empty v-if="paginatedCards.length === 0 && !isLoading" description="暂无数据" />

      <a-row :gutter="[24, 24]" v-else class="card-section">
        <a-col
          :xs="24"
          :sm="12"
          :md="12"
          :lg="8"
          :xl="6"
          v-for="card in paginatedCards"
          :key="card.id"
        >
          <a-card hoverable class="experiment-card" @click="navigateToDetails(card.id)">
            <div class="card-image-wrapper">
              <img :src="card.image" class="card-image" :alt="card.title" />
              <div class="card-overlay">
                <eye-outlined class="zoom-icon" />
              </div>
            </div>
            <a-card-meta :title="card.title" class="card-meta">
              <template #description>
                <a-tag color="blue" class="card-tag">{{ card.tag }}</a-tag>
              </template>
            </a-card-meta>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>

    <div class="pagination-container" v-if="totalPages > 1">
      <a-pagination
        v-model:current="currentPage"
        :total="filteredCards.length"
        :pageSize="itemsPerPage"
        show-quick-jumper
        :pageSizeOptions="['4', '8', '12', '16']"
        @change="(page) => (currentPage = page)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
// 导入你的 API 模块和用户 Store
import { experimentApi } from '@/apis/experiment_api' // 确保路径正确
import { useUserStore } from '@/stores/user' // 确保路径正确

import {
  SearchOutlined,
  RightOutlined,
  EyeOutlined,
  ExperimentOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const userStore = useUserStore() // 实例化 userStore

const search = ref('')
const currentPage = ref(1)
const itemsPerPage = 4 // 每页显示4个卡片
const isLoading = ref(true)
const error = ref(null)

// cards 现在将存储从后端获取并映射后的课程数据
const cards = ref([])

// tags 数据，可能需要根据你的实际课程分类进行调整
const tags = ref([
  { label: '全部', active: true, filter: '' }, // 新增“全部”标签，不进行过滤
  { label: '视觉推理', filter: '视觉推理' },
  { label: '大模型应用', emoji: '', hot: false, filter: '大模型应用' },
  { label: '计算机视觉(CV)', filter: '计算机视觉' }
  // { label: '自然语言处理(NLP)', badge: 3, filter: '自然语言处理' }
])

// 计算属性 (filteredCards, totalPages, paginatedCards) 保持不变
const filteredCards = computed(() => {
  const activeTag = tags.value.find((tag) => tag.active)
  // tagFilter 现在直接使用 tag.label 进行匹配，因为 description 可能会包含这些词
  const tagFilter = activeTag && activeTag.label !== '全部' ? activeTag.filter.toLowerCase() : ''
  const searchTerm = search.value.toLowerCase()

  return cards.value.filter((card) => {
    const titleMatch = card.title && card.title.toLowerCase().includes(searchTerm)
    const tagMatch = card.tag && card.tag.toLowerCase().includes(searchTerm) // 搜索时也包含 tag 字段
    const matchesSearch = titleMatch || tagMatch

    // 如果 tagFilter 为空，表示不过滤，所有卡片都匹配
    const matchesTag = !tagFilter || (card.tag && card.tag.toLowerCase().includes(tagFilter))
    return matchesSearch && matchesTag
  })
})

const totalPages = computed(() => {
  if (filteredCards.value.length === 0) return 1
  return Math.ceil(filteredCards.value.length / itemsPerPage)
})

const paginatedCards = computed(() => {
  if (currentPage.value > totalPages.value && totalPages.value > 0) {
    currentPage.value = totalPages.value
  } else if (totalPages.value === 0) {
    currentPage.value = 1
  }

  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filteredCards.value.slice(start, end)
})

// 标签点击处理
const selectTag = (index) => {
  tags.value.forEach((tag, i) => {
    tag.active = i === index
  })
  currentPage.value = 1 // 重置到第一页
}

// 跳转方法，现在跳转到课程详情页
const navigateToDetails = (id) => {
  if (id !== undefined && id !== null) {
    // 假设课程详情页的路由是 /courses/:id
    router.push(`/experiment/${id}`)
    // 或者如果你想保持 /experiment/experiment/:id，那么后端需要提供实验ID作为课程的一部分，或者你需要重定向
    // router.push(`/experiment/experiment/${id}`)
  } else {
    console.error('无效的课程 ID:', id)
  }
}

// 新增的获取课程数据的函数
const fetchCourses = async () => {
  isLoading.value = true
  error.value = null
  try {
    // 调用 experimentApi.getAllCourses() 来获取课程数据
    const responseData = await experimentApi.getMyCourses()

    // 映射课程数据到卡片格式
    cards.value = responseData.map((course) => ({
      id: course.id,
      image: course.image || 'https://via.placeholder.com/400x220?text=No+Image', // 如果没有图片，提供一个默认占位符
      title: course.title,
      // 将 description 映射为 tag，用于显示在卡片上和进行过滤
      tag: course.description || '暂无描述'
    }))

    console.log('获取所有课程并映射成功:', cards.value)
  } catch (err) {
    console.error('获取课程数据时出错:', err)
    error.value = err
    cards.value = [] // 出错时清空数据
    // 根据错误类型可能需要跳转到登录页，如果 useUserStore 中有处理认证错误的功能
    if (err?.status === 401 || err?.detail === '无效的令牌') {
      // router.push('/login'); // 如果需要强制跳转登录页
    }
  } finally {
    isLoading.value = false
  }
}

// 在组件挂载时调用获取课程的函数
onMounted(() => {
  // 确保用户已登录才尝试获取数据
  if (userStore.isLoggedIn) {
    fetchCourses()
  } else {
    console.warn('用户未认证，不获取课程数据。')
    // 如果需要，可以在这里重定向到登录页面
    router.push('/login')
  }
})
</script>

<style scoped>
/* 样式部分保持不变 */
.experiment-page {
  padding: 32px;
  max-width: 1400px;
  margin: 0 auto;
  background-color: #f7f8fa;
  min-height: calc(100vh - 64px);
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', sans-serif;
}

.header-section {
  margin-bottom: 32px;
  position: relative;
}

.header-section::after {
  content: '';
  position: absolute;
  bottom: -16px;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(
    90deg,
    rgba(22, 119, 255, 0.2),
    rgba(22, 119, 255, 0.6),
    rgba(22, 119, 255, 0.2)
  );
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  margin: 0 !important;
  color: #1677ff !important;
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 28px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.page-title :deep(.anticon) {
  font-size: 28px;
  background-color: rgba(22, 119, 255, 0.1);
  padding: 10px;
  border-radius: 12px;
  color: #1677ff;
}

.search-input {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.filter-section {
  margin-bottom: 40px;
}

.category-tags {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.custom-tag {
  cursor: pointer;
  padding: 8px 20px;
  font-size: 15px;
  border-radius: 20px;
  transition: all 0.3s;
  font-weight: 500;
  border: none;
}

.custom-tag:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.custom-tag.active {
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.2);
}

.emoji {
  margin-left: 6px;
}

.more-btn {
  margin-left: auto;
  font-size: 15px;
  padding: 0;
  color: #1677ff;
  font-weight: 500;
}

.more-btn:hover {
  text-decoration: underline;
}

.card-section {
  min-height: 200px;
}

.experiment-card {
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  height: 100%;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  border: none;
}

.experiment-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.15);
}

.card-image-wrapper {
  position: relative;
  width: 100%;
  height: 220px;
  overflow: hidden;
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s;
}

.experiment-card:hover .card-image {
  transform: scale(1.08);
}

.card-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.2), transparent);
  opacity: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.4s;
}

.experiment-card:hover .card-overlay {
  opacity: 1;
}

.zoom-icon {
  background: white;
  border-radius: 50%;
  padding: 12px;
  font-size: 20px;
  color: #1677ff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  transform: scale(0.8);
  transition: all 0.3s;
}

.experiment-card:hover .zoom-icon {
  transform: scale(1);
}

.card-meta {
  padding: 16px 8px 8px;
}

.card-meta :deep(.ant-card-meta-title) {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #262626;
}

.card-tag {
  font-size: 14px;
  padding: 4px 12px;
  border-radius: 10px;
}

.pagination-container {
  margin-top: 48px;
  display: flex;
  justify-content: center;
}

.pagination-container :deep(.ant-pagination-item) {
  border-radius: 8px;
  font-size: 15px;
}

.pagination-container :deep(.ant-pagination-item-active) {
  border-color: #1677ff;
  font-weight: 600;
}

.pagination-container :deep(.ant-pagination-options) {
  margin-left: 16px;
}

@media (max-width: 768px) {
  .experiment-page {
    padding: 20px;
  }

  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .search-input {
    width: 100% !important;
  }

  .page-title {
    font-size: 24px !important;
  }

  .page-title :deep(.anticon) {
    font-size: 24px;
    padding: 8px;
  }

  .custom-tag {
    padding: 6px 16px;
    font-size: 14px;
  }

  .card-image-wrapper {
    height: 180px;
  }
}
</style>
