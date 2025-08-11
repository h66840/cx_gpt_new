export const themeConfig = {
  token: {
    colorPrimary: '#1677ff', // 蓝色主题色
    colorSuccess: '#52c41a', // 成功色
    colorWarning: '#faad14', // 警告色
    colorError: '#ff4d4f', // 错误色
    colorInfo: '#1677ff', // 信息色
    colorTextBase: '#262626', // 基础文本色
    colorBgBase: '#ffffff', // 基础背景色
    borderRadius: 6, // 统一圆角
    fontFamily:
      "'HarmonyOS Sans SC', 'PingFang SC', 'Microsoft YaHei', Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;"
  },
  components: {
    Button: {
      colorPrimary: '#1677ff',
      algorithm: true
    },
    Card: {
      colorBgContainer: '#ffffff',
      borderRadiusLG: 8
    },
    Input: {
      colorBorder: '#d9d9d9',
      borderRadius: 6
    }
  }
}
