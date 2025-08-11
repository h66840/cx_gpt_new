<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <h3>为实验评分和评论</h3>
      <form @submit.prevent="submitReview">
        <div class="form-group">
          <label for="overall-rating">总体评分:</label>
          <input
            type="number"
            id="overall-rating"
            v-model.number="rating"
            min="1"
            max="5"
            placeholder="请输入 1-5 的数字"
          />
        </div>

        <div class="form-group">
          <h4>各项评分 (1-5):</h4>
          <div v-for="(value, aspect) in aspectRatings" :key="aspect" class="aspect-rating">
            <label :for="'aspect-' + aspect">{{ aspect }}:</label>
            <input
              type="number"
              :id="'aspect-' + aspect"
              v-model.number="aspectRatings[aspect]"
              min="1"
              max="5"
              placeholder="请输入 1-5 的数字"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="comment">评论:</label>
          <textarea
            id="comment"
            v-model="comment"
            rows="4"
            placeholder="写下你的评论..."
            required
          ></textarea>
        </div>

        <div class="modal-actions">
          <button type="submit" class="submit-button">提交</button>
          <button type="button" @click="close" class="cancel-button">取消</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits } from 'vue'
import { experimentApi } from '@/apis/experiment_api' // 引入你的 experimentApi
import { useUserStore } from '@/stores/user' // ***** 新增：引入 useUserStore *****

const props = defineProps({
  experimentId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['close', 'review-submitted'])

const rating = ref(null)
const aspectRatings = ref({
  课程内容: null,
  讲师教学: null,
  测验内容: null,
  学习模式: null
})
const comment = ref('')

// ***** 新增：获取用户 store 实例 *****
const userStore = useUserStore()

const submitReview = async () => {
  const hasComment = comment.value && comment.value.trim() !== ''
  const hasOverallRating = rating.value !== null && rating.value >= 1 && rating.value <= 5
  const hasAspectRatings = Object.values(aspectRatings.value).some(
    (val) => val !== null && val >= 1 && val <= 5
  )

  if (!hasComment && !hasOverallRating && !hasAspectRatings) {
    alert('请至少填写评论内容、总体评分或某项细节评分！')
    return
  }

  // ***** 校验用户是否登录，确保 userStore 中有用户名 *****
  if (!userStore.isLoggedIn || !userStore.username) {
    alert('用户未登录或用户信息不完整，无法提交评论。请重新登录。')
    console.error('User not logged in or username missing from store.')
    return // 阻止提交
  }

  try {
    const reviewPayload = {
      // ***** 修改：从 userStore 中获取真实的 user_id 和 user_name *****
      // 注意：后端提交评论时通常只根据 token 解析 user_id，
      // 但如果你的后端 ReviewCreate 模型确实需要前端传 user_id 和 user_name，
      // 那么确保 userStore 中有这些信息。
      // 根据你提供的后端 Review 模型，它只接收 user_id 和 experiment_id，
      // user_name 应该是通过 user_id 关联 User 表获取的。
      // 因此，通常你只需要传递 experimentId 和评论数据，user_id 会由后端根据认证 token 获取。
      // 如果后端 ReviewCreate 模型要求 user_id, 那么需要确保 userStore.userId 存在。
      // 假设后端是根据 token 自动获取 user_id，前端只传 reviewData:
      // user_id: userStore.userId, // 如果后端需要前端传 user_id
      user_name: userStore.username, // 如果后端需要前端传 user_name
      rating: rating.value,
      aspect_ratings: Object.fromEntries(
        Object.entries(aspectRatings.value).filter(
          ([key, val]) => val !== null && val >= 1 && val <= 5
        )
      ),
      comment: comment.value
    }

    await experimentApi.submitReview(props.experimentId, reviewPayload)

    alert('评论提交成功！')
    emit('review-submitted') // 通知父组件刷新评论列表等
  } catch (err) {
    console.error('Error submitting review:', err)
    alert(`提交评论失败: ${err.message || err.detail || '未知错误'}`)
  }
}

const close = () => {
  emit('close')
}
</script>

<style scoped>
/* 模态框样式 (与之前相同) */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  max-height: 90vh;
  /* 限制最大高度 */
  overflow-y: auto;
  /* 内容过多时滚动 */
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 20px;
  text-align: center;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: bold;
}

.form-group input[type='number'],
.form-group textarea {
  width: calc(100% - 20px);
  /* 留出内边距空间 */
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 16px;
}

.aspect-rating {
  margin-bottom: 10px;
  display: flex;
  /* 使用 Flexbox 布局 */
  align-items: center;
  gap: 10px;
  /* 标签和输入框之间的间距 */
}

.aspect-rating label {
  flex-shrink: 0;
  /* 防止标签收缩 */
  margin-bottom: 0;
  /* 重置 label 的 margin-bottom */
  width: 80px;
  /* 给标签固定宽度 */
}

.aspect-rating input[type='number'] {
  flex-grow: 1;
  /* 输入框占据剩余空间 */
  width: auto;
  /* 重置宽度 */
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.submit-button,
.cancel-button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.submit-button {
  background-color: #3964f8;
  color: white;
}

.cancel-button {
  background-color: #ccc;
  color: #333;
}
</style>
