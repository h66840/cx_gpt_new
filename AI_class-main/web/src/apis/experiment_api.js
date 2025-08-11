import { apiGet, apiPost } from './base' // 假设你的API基础封装在这里
import { useUserStore } from '@/stores/user' // 引入真正的用户 store

/**
 * 学生实验平台相关API模块
 *
 * 涵盖课程、实验、实验记录和评论等操作。
 * 所有接口都需要用户认证。
 */

export const experimentApi = {
  /**
   * 获取当前用户订阅的所有课程
   * @returns {Promise<Array>}
   */
  getMyCourses: () => {
    // 对应后端路由: GET /api/experiments/my-courses
    console.log('Calling apiGet for my courses with requiresAuth:', true)
    return apiGet('/api/experiments/courses', {}, true)
  },

  /**
   * 获取指定课程下的所有实验
   * @param {number | string} courseId - 课程的ID
   * @returns {Promise<Array>} 实验列表
   */
  getExperimentsByCourse: (courseId) => {
    // 对应后端路由: GET /api/experiments/course/{course_id}/experiments
    return apiGet(`/api/experiments/course/${courseId}/experiments`, {}, true)
  },

  /**
   * 获取单个实验的详细信息（包含步骤和评论）
   * @param {number | string} experimentId - 实验的ID
   * @returns {Promise<Object>} 实验详情
   */
  getExperimentDetails: (experimentId) => {
    // 对应后端路由: GET /api/experiments/{experiment_id}
    return apiGet(`/api/experiments/${experimentId}`, {}, true)
  },
  startOrContinueExperiment: (experimentId, stepId) => {
    // 后端路由: POST /api/experiments/{experiment_id}/step/{step_id}/start
    // 确保前端请求路径与后端定义完全匹配
    return apiPost(`/api/experiments/${experimentId}/step/${stepId}/start`, {}, {}, true)
  },

  /**
   * 获取指定实验下的所有实验步骤
   * @param {number | string} experimentId - 实验的ID
   * @returns {Promise<Array>} 实验步骤列表
   */
  getExperimentSteps: (experimentId) => {
    // 对应后端路由: GET /api/experiments/{experiment_id}/steps
    return apiGet(`/api/experiments/${experimentId}/steps`, {}, true)
  },
  /**
   * 开始或继续一个实验
   * 这将为用户创建或获取一个实验记录
   * @param {number | string} experimentId - 实验的ID
   * @returns {Promise<Object>} 实验记录对象
   */

  getExperimentRecordDetails: (experimentId) => {
    // 假设没有额外的查询参数，只需要认证
    return apiGet(`/api/experiments/${experimentId}/record_details`, {}, true)
  },
  /**
   * 提交实验答案
   * @param {number | string} recordId - 实验记录的ID
   * @param {Object} answers - 用户的答案，格式为 { step_id: user_answer }
   * @returns {Promise<Object>} 提交结果，包含分数等信息
   */
  submitExperimentAnswers: (recordId, answers) => {
    // 对应后端路由: POST /api/experiments/records/{record_id}/submit
    const payload = { answers: answers }
    return apiPost(`/api/experiments/records/${recordId}/submit`, payload, {}, true)
  },

  /**
   *为指定实验提交一条评论
   * @param {number | string} experimentId - 实验的ID
   * @param {Object} reviewData - 评论数据，包含 { rating, comment, aspect_ratings? }
   * @returns {Promise<Object>} 新创建的评论对象
   */
  submitReview: (experimentId, reviewData) => {
    // 对应后端路由: POST /api/experiments/{experiment_id}/reviews
    return apiPost(`/api/experiments/${experimentId}/reviews`, reviewData, {}, true)
  },

  /**
   * 完成一个实验记录，更新其状态、分数和结束时间。
   * @param {number} userId - 用户ID
   * @param {number} experimentId - 实验ID
   * @param {number} score - 最终分数 (0-100)
   * @param {number} [currentStepId] - 可选，当前完成的步骤ID
   * @returns {Promise<Object>} 更新后的实验记录信息或成功消息
   */
  completeExperimentRecord: (userId, experimentId, score, currentStepId = null) => {
    const payload = {
      user_id: userId,
      experiment_id: experimentId,
      score: parseFloat(score) // 确保分数是浮点数
    }
    if (currentStepId !== null) {
      payload.current_step_id = parseInt(currentStepId) // 确保步骤ID是整数
    }
    // 对应后端路由: POST /api/experiments/records/complete
    return apiPost('/api/experiments/records/complete', payload, {}, true)
  }
}
