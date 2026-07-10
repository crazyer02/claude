/**
 * 家人绑定页 - 老人展示二维码，家人扫码绑定
 */
const { userApi } = require('../../utils/api');
const app = getApp();

Page({
  data: {
    fontSizeMode: 'large',
    userType: 'elderly',
    userId: null,
    bindedElderly: [],
    familyMembers: [],
    qrcodeUrl: '',
    loading: false,
    showScanTip: false,
  },

  onLoad(options) {
    // 从二维码扫码进入，自动绑定
    if (options.bind) {
      this.autoBind(parseInt(options.bind));
    }
    // 从扫码 API 返回结果
    if (options.q) {
      const match = options.q.match(/elderly_bind:\/\/(\d+)/);
      if (match) {
        this.autoBind(parseInt(match[1]));
      }
    }
  },

  onShow() {
    const userInfo = app.globalData.userInfo || wx.getStorageSync('userInfo') || {};
    // 从本地存储读角色偏好，默认老人
    const savedRole = wx.getStorageSync('familyRole') || 'elderly';
    this.setData({
      fontSizeMode: app.globalData.fontSizeMode || 'large',
      userId: userInfo.id,
      userType: savedRole,
    });
    this.loadQrcode();
    this.loadData();
  },

  switchRole(e) {
    const role = e.currentTarget.dataset.role;
    wx.setStorageSync('familyRole', role);
    this.setData({ userType: role });
    this.loadData();
  },

  loadQrcode() {
    const token = wx.getStorageSync('token') || app.globalData.token;
    this.setData({ qrcodeUrl: `${app.globalData.apiBaseUrl}/user/qrcode?token=${encodeURIComponent(token)}` });
  },

  async loadData() {
    this.setData({ loading: true });
    try {
      const userInfo = app.globalData.userInfo || {};
      if (userInfo.is_elderly) {
        const members = await userApi.getFamilyMembers(userInfo.id);
        this.setData({ familyMembers: members || [] });
      } else {
        const elderly = await userApi.getBindedElderly();
        this.setData({ bindedElderly: elderly || [] });
      }
    } catch (err) {
      console.error('加载家人信息失败:', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 扫码绑定（家人端）
   */
  onScanCode() {
    wx.scanCode({
      onlyFromCamera: true,
      scanType: ['qrCode'],
      success: (res) => {
        const match = res.result.match(/elderly_bind:\/\/(\d+)/);
        if (match) {
          this.autoBind(parseInt(match[1]));
        } else {
          wx.showToast({ title: '无效的绑定二维码', icon: 'none' });
        }
      },
      fail: () => {
        wx.showToast({ title: '扫码取消', icon: 'none' });
      },
    });
  },

  /**
   * 执行绑定
   */
  async autoBind(elderlyId) {
    if (!elderlyId) return;
    try {
      await userApi.bindFamily({ elderly_user_id: elderlyId, relationship: 'other' });
      wx.showToast({ title: '绑定成功', icon: 'success', duration: 2000 });
      this.setData({ userType: 'family' });
      this.loadData();
    } catch (err) {
      wx.showToast({ title: '绑定失败，可能已绑定', icon: 'none' });
    }
  },

  goElderlyDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/index/index?elderly_id=${id}` });
  },

  /**
   * 预览二维码大图
   */
  previewQrcode() {
    wx.previewImage({
      urls: [this.data.qrcodeUrl],
      current: this.data.qrcodeUrl,
    });
  },
});
