/**
 * 首页 - 今日用药概览
 * 面向老年人：大字号、清晰状态、一键标记服药
 */
const { recordApi } = require('../../utils/api');
const { getPeriodIcon, getPeriodLabel, getStatusConfig, getTodayStr, speakText } = require('../../utils/util');

Page({
  data: {
    // 日期
    today: '',
    weekday: '',
    greeting: '',

    // 用药概览
    overview: {
      total_count: 0,
      taken_count: 0,
      missed_count: 0,
      pending_count: 0,
      adherence_rate: 0,
      schedules: [],
    },

    // 即将提醒的药品
    upcomingMedicines: [],

    // 状态
    loading: false,
    refreshing: false,

    // 当前时间
    currentTime: '',

    // 弹窗
    showTakePopup: false,
    selectedMedicine: null,
  },

  onLoad() {
    this.updateTimeAndGreeting();
    // 每分钟刷新当前时间
    this.timer = setInterval(() => {
      this.updateTimeAndGreeting();
    }, 60000);
  },

  onShow() {
    this.loadTodayOverview();
  },

  onUnload() {
    if (this.timer) clearInterval(this.timer);
  },

  /**
   * 下拉刷新
   */
  async onPullDownRefresh() {
    this.setData({ refreshing: true });
    await this.loadTodayOverview();
    wx.stopPullDownRefresh();
    this.setData({ refreshing: false });
  },

  /**
   * 加载今日概览数据
   */
  async loadTodayOverview() {
    this.setData({ loading: true });
    try {
      const overview = await recordApi.getToday();
      this.setData({
        overview,
        today: getTodayStr(),
        // 计算即将提醒的（pending 状态且时间未过）
        upcomingMedicines: overview.schedules
          .filter((s) => s.status === 'pending')
          .slice(0, 3),
      });

      // 语音提醒：如果有待服用的药品
      if (overview.pending_count > 0 && overview.pending_count <= 3) {
        const names = overview.schedules
          .filter((s) => s.status === 'pending')
          .map((s) => s.medicine_name)
          .join('、');
        // speakText(`您有${overview.pending_count}种药需要服用：${names}`);
      }
    } catch (err) {
      console.error('加载今日概览失败:', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 更新时间&问候语
   */
  updateTimeAndGreeting() {
    const now = new Date();
    const hour = now.getHours();
    const minute = String(now.getMinutes()).padStart(2, '0');
    const timeStr = `${hour}:${minute}`;

    let greeting = '早上好';
    if (hour >= 6 && hour < 9) greeting = '早上好 ☀️';
    else if (hour >= 9 && hour < 12) greeting = '上午好 🌤️';
    else if (hour >= 12 && hour < 14) greeting = '中午好 ☀️';
    else if (hour >= 14 && hour < 18) greeting = '下午好 🌈';
    else if (hour >= 18 && hour < 22) greeting = '晚上好 🌙';
    else greeting = '夜深了，早点休息 🌙';

    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    const weekday = `星期${weekdays[now.getDay()]}`;

    this.setData({
      currentTime: timeStr,
      weekday,
      greeting,
      today: getTodayStr(),
    });
  },

  /**
   * 点击「我已服药」按钮
   */
  onTakeMedicine(e) {
    const item = e.currentTarget.dataset.item;
    this.setData({
      showTakePopup: true,
      selectedMedicine: item,
    });
  },

  /**
   * 确认服药
   */
  async confirmTakeMedicine() {
    const item = this.data.selectedMedicine;
    if (!item) return;

    try {
      const now = new Date();
      const scheduledTime = `${this.data.today}T${item.reminder_time}:00`;

      await recordApi.create({
        schedule_id: item.schedule_id,
        medicine_id: item.medicine_id,
        scheduled_time: scheduledTime,
        actual_time: now.toISOString(),
        status: 'taken',
      });

      wx.showToast({ title: '✅ 已记录服药', icon: 'none', duration: 2000 });
      this.setData({ showTakePopup: false, selectedMedicine: null });

      // 刷新概览
      setTimeout(() => this.loadTodayOverview(), 500);
    } catch (err) {
      console.error('记录失败:', err);
    }
  },

  /**
   * 跳过服药
   */
  async skipMedicine() {
    const item = this.data.selectedMedicine;
    if (!item) return;

    try {
      const scheduledTime = `${this.data.today}T${item.reminder_time}:00`;
      await recordApi.create({
        schedule_id: item.schedule_id,
        medicine_id: item.medicine_id,
        scheduled_time: scheduledTime,
        status: 'skipped',
      });

      wx.showToast({ title: '已跳过', icon: 'none', duration: 2000 });
      this.setData({ showTakePopup: false, selectedMedicine: null });
      setTimeout(() => this.loadTodayOverview(), 500);
    } catch (err) {
      console.error('操作失败:', err);
    }
  },

  /**
   * 关闭弹窗
   */
  closePopup() {
    this.setData({ showTakePopup: false, selectedMedicine: null });
  },

  /**
   * 跳转到添加药品页
   */
  goAddMedicine() {
    wx.navigateTo({ url: '/pages/medicine/add/add' });
  },

  /**
   * 跳转到用药记录页
   */
  goHistory() {
    wx.switchTab({ url: '/pages/history/history' });
  },

  /**
   * 跳转到家人页
   */
  goFamily() {
    wx.navigateTo({ url: '/pages/family/family' });
  },
});
