<template>
  <div class="page">
    <div class="header">
      <h1 class="page-title">人工智能创新实验课</h1>
      <input v-model="search" class="search-input" placeholder="搜索模型/关键词..." />
    </div>

    <div class="category-tags">
      <button
        v-for="(tag, index) in tags"
        :key="tag.label"
        :class="['tag-btn', { active: tag.active, hot: tag.hot }]"
        @click="selectTag(index)"
      >
        {{ tag.label }}
        <span v-if="tag.emoji" class="emoji">{{ tag.emoji }}</span>
        <span v-if="tag.badge" class="badge">{{ tag.badge }}</span>
      </button>
      <div class="more-btn">➔</div>
    </div>

    <div class="card-container">
      <div
        v-for="card in paginatedCards"
        :key="card.id"
        class="card"
        @click="navigateToDetails(card.id)"
      >
        <div class="card-image-wrapper">
          <img :src="card.image" class="card-image" :alt="card.title" />
          <div class="zoom-icon">🔍</div>
        </div>
        <div class="card-content">
          <div class="card-title">{{ card.title }}</div>
          <div class="card-tag">{{ card.tag }}</div>
        </div>
      </div>
    </div>

    <div class="pagination" v-if="totalPages > 1">
      <button :disabled="currentPage === 1" @click="currentPage--" class="page-btn">上一页</button>
      <span class="page-info"> 第 {{ currentPage }} 页 / 共 {{ totalPages }} 页 </span>
      <button :disabled="currentPage === totalPages" @click="currentPage++" class="page-btn">
        下一页
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const search = ref('')
const currentPage = ref(1)
const itemsPerPage = 4
const isLoading = ref(true)
const error = ref(null)

const cards = ref([])

const tags = ref([
  { label: '热门推荐', active: true, filter: '' },
  { label: '大模型应用', emoji: '🔥', hot: false, filter: '' },
  { label: '计算机视觉(CV)', filter: '卷积神经网络' }
  // { label: '自然语言处理(NLP)', badge: '聊天机器人', filter: '深层神经网络' }
])

const filteredCards = computed(() => {
  const activeTag = tags.value.find((tag) => tag.active)
  const tagFilter = activeTag ? activeTag.filter : ''
  const searchTerm = search.value.toLowerCase()

  return cards.value.filter((card) => {
    const titleMatch = card.title && card.title.toLowerCase().includes(searchTerm)
    const tagMatch = card.tag && card.tag.toLowerCase().includes(searchTerm)
    const matchesSearch = titleMatch || tagMatch

    const matchesTag = !tagFilter || card.tag === tagFilter
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

const selectTag = (index) => {
  tags.value.forEach((tag, i) => {
    tag.active = i === index
  })
  currentPage.value = 1
}

const navigateToDetails = (id) => {
  if (id !== undefined && id !== null) {
    router.push(`/experiment/experiment/${id}`)
  } else {
    console.error('无效的实验 ID:', id)
  }
}

const fetchExperiments = async () => {
  isLoading.value = true
  error.value = null
  try {
    const response = await fetch('api/experiment/experiments')

    if (!response.ok) {
      throw new Error(`HTTP 请求错误! 状态码: ${response.status}`)
    }
    const data = await response.json()

    cards.value = data
  } catch (err) {
    console.error('获取实验数据时出错:', err)
    error.value = err
    cards.value = []
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchExperiments()
})
</script>

<style scoped>
/* 你提供的原始 CSS 完全保留在此处 */
.page {
  padding: 24px;
  font-family: 'Segoe UI', sans-serif;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  margin: 0;
}

.search-input {
  width: 260px;
  padding: 8px 16px;
  border: 1px solid #ccc;
  border-radius: 999px;
  outline: none;
  font-size: 14px;
}

.category-tags {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  flex-wrap: wrap;
}

.tag-btn {
  padding: 6px 16px;
  border-radius: 999px;
  border: 1px solid #d6d6d6;
  background: white;
  color: #222;
  font-weight: bold;
  font-size: 14px;
  position: relative;
  cursor: pointer;
}

.tag-btn.active {
  background: #3964f8;
  color: white;
  border: none;
}

.tag-btn.hot {
  border-color: #ff6600;
  color: #ff6600;
}

.emoji {
  margin-left: 4px;
}

.badge {
  position: absolute;
  top: -8px;
  right: -12px;
  font-size: 12px;
  background-color: #ff9130;
  color: white;
  padding: 2px 6px;
  border-radius: 8px;
}

.more-btn {
  color: #3964f8;
  font-size: 24px;
  cursor: pointer;
  margin-left: auto;
}

.card-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: 24px;
  /* 移除了 margin-right: -24px; 如果需要可以加回来 */
  /* 确保容器本身不影响内部卡片布局 */
  min-height: 200px;
  /* 添加一个最小高度，防止加载时容器塌陷 */
}

.card {
  background-color: white;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease;
  position: relative;
  cursor: pointer;
}

.card:hover {
  transform: translateY(-6px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.card-image-wrapper {
  position: relative;
  width: 100%;
  height: 240px;
  overflow: hidden;
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.zoom-icon {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  padding: 6px;
  font-size: 14px;
  cursor: pointer;
}

.card-content {
  padding: 24px;
}

.card-title {
  font-weight: bold;
  font-size: 20px;
  color: #222;
  margin-bottom: 12px;
}

.card-tag {
  display: inline-block;
  padding: 4px 14px;
  background-color: #e8f5e9;
  color: #2e7d32;
  font-size: 14px;
  border-radius: 999px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 32px;
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid #d6d6d6;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
}

@media (max-width: 1200px) {
  .card-container {
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  }
}

@media (max-width: 768px) {
  .card-container {
    grid-template-columns: 1fr;
    padding-right: 0;
    /* 原始样式包含此项 */
  }

  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
}
</style>
