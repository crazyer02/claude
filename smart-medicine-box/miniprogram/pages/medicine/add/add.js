/**
 * 添加/编辑药品页
 */
const { medicineApi } = require('../../../utils/api');

Page({
  data: {
    isEdit: false,
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

  onLoad(options) {
    if (options.id) {
      this.setData({ isEdit: true, medicineId: parseInt(options.id) });
      this.loadMedicine(options.id);
      wx.setNavigationBarTitle({ title: '编辑药品' });
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

  // 输入框事件
  onInput(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    this.setData({ [`form.${field}`]: value });
  },

  // 数字输入
  onNumberInput(e) {
    const field = e.currentTarget.dataset.field;
    const value = parseInt(e.detail.value) || 0;
    this.setData({ [`form.${field}`]: value });
  },

  // 选择频率
  onSelectFrequency(e) {
    const value = e.currentTarget.dataset.value;
    this.setData({ 'form.frequency': value });
  },

  // 选择单位
  onSelectUnit(e) {
    const value = e.currentTarget.dataset.value;
    this.setData({ 'form.unit': value });
  },

  // 选择日期
  onDateChange(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ [`form.${field}`]: e.detail.value });
  },

  // 选择药箱仓位
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

  // 提交表单
  async onSubmit() {
    const form = this.data.form;

    // 验证必填项
    if (!form.name.trim()) {
      wx.showToast({ title: '请输入药品名称', icon: 'none' });
      return;
    }
    if (!form.dosage.trim()) {
      wx.showToast({ title: '请输入单次用量', icon: 'none' });
      return;
    }

    this.setData({ submitting: true });

    try {
      if (this.data.isEdit) {
        await medicineApi.update(this.data.medicineId, form);
        wx.showToast({ title: '✅ 更新成功', icon: 'none', duration: 2000 });
      } else {
        await medicineApi.create(form);
        wx.showToast({ title: '✅ 添加成功', icon: 'none', duration: 2000 });
      }
      setTimeout(() => wx.navigateBack(), 1500);
    } catch (err) {
      console.error('提交失败:', err);
    } finally {
      this.setData({ submitting: false });
    }
  },
});
