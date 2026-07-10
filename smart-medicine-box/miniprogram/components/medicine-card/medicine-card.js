/**
 * 药品卡片组件
 *
 * 属性:
 *   medicine  - 药品数据对象
 *   showActions - 是否显示操作按钮
 */
Component({
  properties: {
    medicine: {
      type: Object,
      value: {},
    },
    showActions: {
      type: Boolean,
      value: true,
    },
  },

  methods: {
    onTapCard() {
      this.triggerEvent('tap', { medicine: this.properties.medicine });
    },

    onEdit() {
      this.triggerEvent('edit', { medicine: this.properties.medicine });
    },

    onDelete() {
      this.triggerEvent('delete', { medicine: this.properties.medicine });
    },

    onSchedule() {
      this.triggerEvent('schedule', { medicine: this.properties.medicine });
    },
  },
});
