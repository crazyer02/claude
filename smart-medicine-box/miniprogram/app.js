/**
 * 智能药箱小程序 - 主入口
 * 面向老年人设计：大字体、简洁交互、语音提示
 */
App({
  globalData: {
    // 后端 API 地址（开发环境）
    apiBaseUrl: 'http://localhost:8000/api',
    // 用户信息
    userInfo: null,
    token: null,
    // 今日用药概览缓存
    todayOverview: null,
    // 字体大小模式: 'normal' | 'large' | 'xlarge'
    fontSizeMode: 'large',
  },

  onLaunch() {
    // 检查登录状态
    this.checkLoginStatus();
    // 读取字体设置
    const fontSize = wx.getStorageSync('fontSizeMode');
    if (fontSize) {
      this.globalData.fontSizeMode = fontSize;
    }
    // 默认使用大字体（适合老年人）
    if (!fontSize) {
      wx.setStorageSync('fontSizeMode', 'large');
    }
  },

  /**
   * 检查登录状态，有 token 则自动恢复
   */
  checkLoginStatus() {
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');
    if (token && userInfo) {
      this.globalData.token = token;
      this.globalData.userInfo = userInfo;
    }
  },

  /**
   * 微信登录
   */
  wxLogin(callback) {
    wx.login({
      success: (res) => {
        if (res.code) {
          wx.request({
            url: `${this.globalData.apiBaseUrl}/user/login`,
            method: 'POST',
            data: { code: res.code },
            success: (resp) => {
              if (resp.statusCode === 200 && resp.data) {
                const { access_token, user } = resp.data;
                this.globalData.token = access_token;
                this.globalData.userInfo = user;
                wx.setStorageSync('token', access_token);
                wx.setStorageSync('userInfo', user);
                if (callback) callback(user);
              }
            },
            fail: (err) => {
              console.error('登录失败:', err);
              wx.showToast({ title: '登录失败，请重试', icon: 'none' });
            },
          });
        }
      },
    });
  },

  /**
   * 获取全局字体大小（rpx）
   */
  getFontSize(baseSize) {
    const mode = this.globalData.fontSizeMode;
    const scale = { normal: 1, large: 1.3, xlarge: 1.6 };
    return Math.round(baseSize * (scale[mode] || 1));
  },

  /**
   * 设置字体大小模式
   */
  setFontSizeMode(mode) {
    this.globalData.fontSizeMode = mode;
    wx.setStorageSync('fontSizeMode', mode);
  },
});
