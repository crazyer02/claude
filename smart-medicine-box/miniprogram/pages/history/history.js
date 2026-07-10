/**
 * 用药记录页
 */
const app = getApp();
const { recordApi } = require('../../utils/api');
const { getStatusConfig, formatTime, formatDateStr } = require('../../utils/util');

Page({
  data: {
    fontSizeMode: 'large',
    records: [],
    selectedDate: '',
    selectedStatus: '',
    loading: false,
    statusOptions: [
      { value: '', label: '全部' },
      { value: 'taken', label: '已服用' },
      { value: 'missed', label: '未服用' },
      { value: 'skipped', label: '已跳过' },
    ],
  },

  onShow() {
    this.setData({ fontSizeMode: app.globalData.fontSizeMode || 'large' });
    this.setData({ selectedDate: formatDateStr(new Date()) });
    this.loadRecords();
  },

  onPullDownRefresh() {
    this.loadRecords().then(() => wx.stopPullDownRefresh());
  },

  /**
   * 格式化时间：把 ISO datetime 转成 "HH:MM"
   */
  formatRecordTime(raw) {
    if (!raw) return '';
    const match = raw.match(/[T ](\d{2}:\d{2})/);
    return match ? match[1] : raw;
  },

  async loadRecords() {
    this.setData({ loading: true });
    try {
      const params = {};
      if (this.data.selectedDate) params.date = this.data.selectedDate;
      if (this.data.selectedStatus) params.status = this.data.selectedStatus;

      const records = await recordApi.getList(params);
      // 格式化时间显示
      const formatted = records.map(r => ({
        ...r,
        scheduled_time: this.formatRecordTime(r.scheduled_time),
        actual_time: this.formatRecordTime(r.actual_time),
      }));
      this.setData({ records: formatted });
    } catch (err) {
      console.error('加载记录失败:', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  onDateChange(e) {
    this.setData({ selectedDate: e.detail.value });
    this.loadRecords();
  },

  onStatusChange(e) {
    const status = e.currentTarget.dataset.status;
    this.setData({ selectedStatus: status });
    this.loadRecords();
  },

  goPrevDay() {
    const d = new Date(this.data.selectedDate);
    d.setDate(d.getDate() - 1);
    this.setData({ selectedDate: formatDateStr(d) });
    this.loadRecords();
  },

  goNextDay() {
    const d = new Date(this.data.selectedDate);
    d.setDate(d.getDate() + 1);
    this.setData({ selectedDate: formatDateStr(d) });
    this.loadRecords();
  },
});
