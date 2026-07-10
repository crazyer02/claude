/**
 * 添加/编辑药品页
 */
const { medicineApi } = require('../../../utils/api');
const app = getApp();

Page({
  data: {
    fontSizeMode: 'large',
    isEdit: false,
    readonly: false,
    medicineId: null,
    form: {
      name: '',
      specification: '',
      dosage: '',
      unit: '片',
      frequency: 'daily',
      start_date: '',
      end_date: '',
      total_stock: 0,
      stock_alert_threshold: 5,
      box_position: '',
      notes: '',
    },
    frequencyOptions: [
      { value: 'daily', label: '每天' },
      { value: 'every_other_day', label: '隔天' },
      { value: 'weekly', label: '每周' },
      { value: 'as_needed', label: '按需' },
    ],
    unitOptions: ['片', '粒', '毫升', '包', '颗', '滴'],
    submitting: false,
  },

  onShow() {
    this.setData({ fontSizeMode: app.globalData.fontSizeMode || 'large' });
  },

  onLoad(options) {
    if (options.id) {
      const readonly = options.readonly === '1';
      this.setData({
        readonly,
        isEdit: !readonly,
        medicineId: parseInt(options.id),
      });
      this.loadMedicine(options.id);
      wx.setNavigationBarTitle({ title: readonly ? '药品详情' : '编辑药品' });
    }
  },

  async loadMedicine(id) {
    try {
      const medicine = await medicineApi.getDetail(id);
      this.setData({
        form: {
          name: medicine.name || '',
          specification: medicine.specification || '',
          dosage: medicine.dosage || '',
          unit: medicine.unit || '片',
          frequency: medicine.frequency || 'daily',
          start_date: medicine.start_date || '',
          end_date: medicine.end_date || '',
          total_stock: medicine.total_stock || 0,
          stock_alert_threshold: medicine.stock_alert_threshold || 5,
          box_position: medicine.box_position || '',
          notes: medicine.notes || '',
        },
      });
    } catch (err) {
      console.error('加载药品信息失败:', err);
    }
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    this.setData({ [`form.${field}`]: value });
  },

  onNumberInput(e) {
    const field = e.currentTarget.dataset.field;
    const value = parseInt(e.detail.value) || 0;
    this.setData({ [`form.${field}`]: value });
  },

  onSelectFrequency(e) {
    const value = e.currentTarget.dataset.value;
    this.setData({ 'form.frequency': value });
  },

  onSelectUnit(e) {
    const value = e.currentTarget.dataset.value;
    this.setData({ 'form.unit': value });
  },

  onDateChange(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ [`form.${field}`]: e.detail.value });
  },

  onSelectPosition(e) {
    const positions = [];
    for (let i = 1; i <= 8; i++) positions.push(`${i}`);
    wx.showActionSheet({
      itemList: positions.map((p) => `${p}号仓`),
      success: (res) => {
        this.setData({ 'form.box_position': positions[res.tapIndex] });
      },
    });
  },

  // 清理空值，避免空字符串导致 Pydantic 422 校验失败
  cleanForm(data) {
    const cleaned = {};
    Object.keys(data).forEach((key) => {
      const val = data[key];
      if (val !== '' && val !== null && val !== undefined) {
        cleaned[key] = val;
      }
    });
    // 确保必填字段存在
    cleaned.name = (data.name || '').trim();
    cleaned.dosage = (data.dosage || '').trim();
    return cleaned;
  },

  async onSubmit() {
    // 防止重复提交
    if (this.data.submitting) return;
    this.data.submitting = true;  // 同步锁定

    const form = this.data.form;
    if (!form.name.trim()) {
      wx.showToast({ title: '请输入药品名称', icon: 'none' });
      this.data.submitting = false;
      return;
    }
    if (!form.dosage.trim()) {
      wx.showToast({ title: '请输入单次用量', icon: 'none' });
      this.data.submitting = false;
      return;
    }

    this.setData({ submitting: true });  // UI 更新
    const data = this.cleanForm(form);

    try {
      if (this.data.isEdit) {
        await medicineApi.update(this.data.medicineId, data);
        wx.showToast({ title: '已更新', icon: 'success', duration: 2000 });
      } else {
        await medicineApi.create(data);
        wx.showToast({ title: '已添加', icon: 'success', duration: 2000 });
      }
      setTimeout(() => wx.navigateBack(), 1500);
    } catch (err) {
      console.error('提交失败:', err);
    } finally {
      this.setData({ submitting: false });
    }
  },
});
