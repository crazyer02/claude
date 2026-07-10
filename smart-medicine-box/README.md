# 🏥 智能药箱 - 老年人用药提醒小程序

> 专为老年人设计的智能用药提醒微信小程序，支持药品管理、定时提醒、家人远程监护等功能。

## 📁 项目结构

```
smart-medicine-box/
├── backend/                        # Python FastAPI 后端
│   ├── app/
│   │   ├── config.py               # 应用配置
│   │   ├── main.py                 # FastAPI 主入口
│   │   ├── models/                 # SQLAlchemy 数据模型
│   │   │   ├── database.py         # 数据库连接
│   │   │   ├── user.py             # 用户模型
│   │   │   └── medicine.py         # 药品/计划/记录模型
│   │   ├── routers/                # API 路由
│   │   │   ├── user.py             # 用户相关接口
│   │   │   └── medicine.py         # 药品/计划/记录接口
│   │   ├── schemas/                # Pydantic 数据校验
│   │   │   ├── user.py
│   │   │   └── medicine.py
│   │   ├── services/               # 业务逻辑层
│   │   │   ├── user_service.py
│   │   │   ├── medicine_service.py
│   │   │   └── reminder_service.py # 定时提醒服务
│   │   └── utils/
│   │       └── auth.py             # JWT & 微信登录
│   ├── requirements.txt
│   └── run.py                      # 启动脚本
│
├── miniprogram/                    # 微信小程序前端
│   ├── app.js / app.json / app.wxss  # 应用入口
│   ├── pages/
│   │   ├── index/                  # 🏠 今日用药概览(首页)
│   │   ├── medicine/               # 💊 药品管理
│   │   │   └── add/                # 添加/编辑药品
│   │   ├── schedule/               # 📅 用药计划
│   │   │   └── add/                # 添加/编辑计划
│   │   ├── history/                # 📋 用药记录
│   │   ├── family/                 # 👨‍👩‍👧 家人绑定
│   │   └── mine/                   # 👤 个人中心
│   ├── components/
│   │   ├── large-button/           # 大按钮(适老化)
│   │   ├── medicine-card/          # 药品卡片
│   │   └── reminder-popup/         # 服药确认弹窗
│   └── utils/
│       ├── api.js                  # API 请求封装
│       └── util.js                 # 工具函数
│
└── README.md
```

## 🚀 快速开始

### 后端

```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 修改配置
# 编辑 app/config.py，设置数据库连接和微信小程序 AppID/Secret

# 4. 创建数据库
# CREATE DATABASE smart_medicine_box CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 5. 启动服务
python run.py

# 服务启动在 http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 前端

1. 下载[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 在微信公众平台注册小程序，获取 AppID
3. 将 `miniprogram/project.config.json` 中的 `appid` 改为你的 AppID
4. 在微信开发者工具中导入 `miniprogram/` 目录
5. 在 `app.js` 中修改 `apiBaseUrl` 为你的后端地址

## 🔑 核心功能

### 👴 老年用户端
| 功能 | 说明 |
|------|------|
| **今日概览** | 大字体展示今日需服药品、已服/未服统计 |
| **一键服药** | 点击「我吃过了」即可记录，无需输入 |
| **药品管理** | 添加药品，设置库存、仓位 |
| **用药计划** | 设置早/中/晚/睡前具体的用药提醒时间 |
| **字体调节** | 标准/大号/特大 三档字体 |
| **家人绑定** | 子女绑定后可远程查看 |

### 👨‍👩‍👧 子女端
| 功能 | 说明 |
|------|------|
| **绑定老人** | 输入老人ID完成绑定 |
| **远程查看** | 实时查看老人今日用药依从率 |
| **异常预警** | 老人漏服时收到提醒 |

## 📊 数据库模型

```
users                   - 用户(openid, 个人信息, 紧急联系人)
medicines               - 药品(名称, 用量, 库存, 仓位)
medicine_schedules      - 用药计划(时段, 提醒时间, 用量)
medicine_records        - 用药记录(计划时间, 实际时间, 状态)
family_bindings         - 家人绑定(老人↔子女, 关系)
```

## 🔌 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/user/login | 微信登录 |
| GET | /api/user/profile | 获取个人信息 |
| PUT | /api/user/profile | 更新个人信息 |
| POST | /api/user/family/bind | 家人绑定 |
| GET | /api/user/family/elderly | 获取绑定的老人列表 |
| GET | /api/medicines | 药品列表 |
| POST | /api/medicines | 添加药品 |
| PUT | /api/medicines/{id} | 更新药品 |
| DELETE | /api/medicines/{id} | 删除药品 |
| GET | /api/schedules | 用药计划列表 |
| POST | /api/schedules | 创建用药计划 |
| GET | /api/records | 用药记录 |
| POST | /api/records | 记录用药 |
| GET | /api/today | 今日用药概览 |

## 🎨 适老化设计

- **大字体**: 默认大号字体，支持特大字体模式
- **大触控区域**: 按钮最小 88rpx 高度
- **高对比度**: 清晰的颜色区分（绿=已服/蓝=待服/红=未服）
- **简洁交互**: 一键服药，减少输入操作
- **图标辅助**: 使用 emoji 图标辅助文字理解
- **语音播报**: 支持 TTS 语音提醒（需接入插件）

## ⚙️ 配置说明

在 `backend/app/config.py` 中修改：

```python
# 数据库
DATABASE_URL = "mysql+pymysql://user:password@host:3306/smart_medicine_box"

# 微信小程序
WECHAT_APPID = "your-appid"
WECHAT_SECRET = "your-secret"

# JWT
SECRET_KEY = "change-this-to-random-string"
```

## 📝 TODO

- [ ] 微信订阅消息推送集成
- [ ] TTS 语音播报
- [ ] 智能药箱硬件对接（MQTT/BLE）
- [ ] 用药数据大屏分析
- [ ] 药品说明书OCR识别
- [ ] 医保药品目录查询

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
