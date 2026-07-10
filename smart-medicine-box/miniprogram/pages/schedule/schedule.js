/**
 * 用药计划页面
 */
const { scheduleApi } = require('../../utils/api');
const { showConfirm } = require('../../utils/util');

// 时段配置
const PERIOD_CONFIG = {
  morning:  { label: '早上', icon: '🌅' },
  noon:     { label: '中午', icon: '☀️' },
  evening:  { label: '晚上', icon: '🌇' },
  night:    { label: '睡前', icon: '🌙' },
};

Page({
  data: {
    medicineId: null,
    schedules: [],
    // 按时间段分组后的数据
    scheduleGroups: [],
    loading: false,
  },

  onLoad(options) {
    if (options.medicine_id) {
      this.setData({ medicineId: parseInt(options.medicine_id) });
    }
  },

  onShow() {
    this.loadSchedules();
  },

  async loadSchedules() {
    this.setData({ loading: true });
    try {
      const schedules = await scheduleApi.getList(this.data.medicineId);
      // 在 JS 中按时间段分组，避免 WXML 中使用 filter
      const scheduleGroups = this.groupByPeriod(schedules);
      this.setData({ schedules, scheduleGroups });
    } catch (err) {
      console.error('加载用药计划失败:', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 按时间段分组（WXML 不支持 filter/复杂表达式）
   */
  groupByPeriod(schedules) {
    const order = ['morning', 'noon', 'evening', 'night'];
    const grouped = {};
    schedules.forEach((s) => {
      if (!grouped[s.period]) {
        grouped[s.period] = [];
      }
      grouped[s.period].push(s);
    });

    // 按固定顺序返回有数据的分组
    return order
      .filter((key) => grouped[key] && grouped[key].length > 0)
      .map((key) => ({
        periodKey: key,
        periodLabel: PERIOD_CONFIG[key].label,
        periodIcon: PERIOD_CONFIG[key].icon,
        items: grouped[key],
      }));
  },

  goAddSchedule() {
    const mid = this.data.medicineId;
    const url = mid ? `/pages/schedule/add/add?medicine_id=${mid}` : '/pages/schedule/add/add';
    wx.navigateTo({ url });
  },

  async onDeleteSchedule(e) {
    const id = e.currentTarget.dataset.id;
    const confirmed = await showConfirm({ title: '确认删除', content: '确定要删除这条用药计划吗？' });
    if (confirmed) {
      try {
        await scheduleApi.delete(id);
        wx.showToast({ title: '已删除', icon: 'success' });
        this.loadSchedules();
      } catch (err) {
        console.error('删除失败:', err);
      }
    }
  },

  onEditSchedule(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/schedule/add/add?id=${id}` });
  },
});
