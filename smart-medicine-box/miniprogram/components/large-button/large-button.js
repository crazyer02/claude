/**
 * 大按钮组件 - 针对老年人设计的大触控区域按钮
 *
 * 属性:
 *   text      - 按钮文字
 *   type      - 样式类型: primary | success | warning | outline | danger
 *   icon      - 可选图标文本
 *   disabled  - 是否禁用
 *   loading   - 是否加载中
 */
Component({
  properties: {
    text: {
      type: String,
      value: '按钮',
    },
    type: {
      type: String,
      value: 'primary', // primary | success | warning | outline | danger
    },
    icon: {
      type: String,
      value: '',
    },
    disabled: {
      type: Boolean,
      value: false,
    },
    loading: {
      type: Boolean,
      value: false,
    },
    customStyle: {
      type: String,
      value: '',
    },
  },

  data: {
    typeClass: '',
  },

  observers: {
    'type': function(type) {
      const classMap = {
        primary: 'btn-primary',
        success: 'btn-success',
        warning: 'btn-warning',
        outline: 'btn-outline',
        danger: 'btn-danger',
      };
      this.setData({ typeClass: classMap[type] || 'btn-primary' });
    },
  },

  methods: {
    onTap() {
      if (this.properties.disabled || this.properties.loading) return;
      this.triggerEvent('tap');
    },
  },
});
