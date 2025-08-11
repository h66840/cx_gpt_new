import { apiGet } from './base' 

/**
 * @typedef {object} DailyActivityStat
 * @property {string} date - 统计日期 (格式: 'YYYY-MM-DD').
 * @property {number} total_operations - 当日总操作数.
 * @property {number} registration_count - 当日新注册用户数.
 */

export const dashboardApi = {
  /**
   * 获取最近14天的每日活动统计数据
   * 用于在管理员仪表盘上展示用户活动趋势图表。
   * @returns {Promise<Array<DailyActivityStat>>} 
   */
  getActivityStats: () => {
    console.log('Calling apiGet for dashboard activity stats, requires admin auth:', true)
    return apiGet('/api/dashboard/activity-stats', {}, true)
  }
}