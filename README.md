# NISA 迎新系统

## 📖 项目简介

NISA 迎新系统是一个基于 FastAPI 和 MongoDB 的现代化迎新管理平台，为新生提供互动式的迎新体验。系统包含关卡打卡、积分管理、抽奖兑奖等核心功能，支持多角色权限管理。

### 主要特性

- 🎯 **关卡管理**：支持创建、编辑和删除迎新关卡，新生完成关卡可获得积分
- 👥 **用户管理**：完善的用户系统，支持学生、管理员、超级管理员等多种角色
- 🎁 **奖品管理**：奖品的创建、编辑、库存管理及兑换记录
- 🎲 **抽奖系统**：积分抽奖功能，支持概率配置和奖品管理
- 📊 **数据统计**：实时展示用户数据、关卡完成情况、奖品兑换记录等
- 🔐 **权限控制**：基于角色的访问控制（RBAC），确保数据安全
- 📱 **响应式设计**：支持多种设备访问，界面友好

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代化的 Python Web 框架
- **Motor** - MongoDB 异步驱动
- **Pydantic** - 数据验证和序列化
- **Uvicorn** - ASGI 服务器

### 数据库
- **MongoDB** - NoSQL 数据库

### 前端
- HTML5 + CSS3 + JavaScript
- Font Awesome 图标库

## 📋 系统要求

- Python 3.8+
- MongoDB 4.0+
- Windows/Linux/macOS

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/coperlm/WelcomeSystem.git
cd WelcomeSystem
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置系统

复制配置模板文件并修改配置：

```bash
cp config_templet.ini config.ini
```

编辑 `config.ini` 文件，配置以下内容：

```ini
[MongoDB]
connectionstring = mongodb://username:password@ip:27017/?authSource=welcomesystem
databasename = welcomesystem

[NFC]
url = http://127.0.0.1:80/

[System]
salt = your_secure_salt_here

[DefaultAdmin]
stuid = super_admin
password = your_secure_password
role = super_admin

[Lottery]
points = 1
```

### 4. 启动应用

```bash
python app.py
```

应用将在 `http://localhost:8000` 启动。

### 5. 访问系统

- **主页**：http://localhost:8000
- **登录页面**：http://localhost:8000/login
- **管理后台**：http://localhost:8000/admin（需要管理员权限）

默认管理员账号（首次启动后请立即修改）：
- 用户名：`super_admin`
- 密码：`super_admin123456`

## 📁 项目结构

```
迎新系统/
├── app.py                      # 主应用入口
├── config.ini                  # 配置文件（需自行创建）
├── config_templet.ini         # 配置模板
├── requirements.txt           # Python 依赖
├── README.md                  # 项目说明文档
│
├── api/                       # API 接口层
│   ├── dependencies/          # 依赖注入（认证、权限等）
│   │   └── auth.py           # 认证依赖
│   └── routes/               # 路由模块
│       ├── auth.py           # 认证相关路由
│       ├── levels.py         # 关卡管理路由
│       ├── members.py        # 成员管理路由
│       └── prizes.py         # 奖品管理路由
│
├── Core/                      # 核心业务逻辑层
│   ├── Common/               # 公共模块
│   │   ├── Config.py         # 配置管理
│   │   └── SystemSettings.py # 系统设置
│   ├── MongoDB/              # 数据库连接
│   │   └── MongoDB.py        # MongoDB 操作封装
│   ├── User/                 # 用户模块
│   │   ├── User.py           # 用户管理
│   │   ├── Permission.py     # 权限管理
│   │   └── Session.py        # 会话管理
│   ├── Level/                # 关卡模块
│   │   └── Level.py          # 关卡管理
│   └── Prize/                # 奖品模块
│       └── Prize.py          # 奖品管理
│
├── config/                    # 应用配置
│   └── app_config.py         # FastAPI 应用配置
│
├── Pages/                     # 前端页面
│   ├── Common/               # 公共资源
│   │   ├── css/             # 公共样式
│   │   ├── js/              # 公共脚本
│   │   └── libs/            # 第三方库
│   ├── Login/                # 登录注册页面
│   ├── Info/                 # 个人信息页面
│   ├── LevelIntroduction/   # 关卡介绍页面
│   ├── LevelManagement/     # 关卡管理页面
│   ├── MemberManagement/    # 成员管理页面
│   ├── PrizeManagement/     # 奖品管理页面
│   ├── ModifyPoint/         # 积分修改页面
│   └── Lottery/             # 抽奖页面
│
└── Assest/                    # 静态资源
    └── Prize/                # 奖品图片
```

## 🔑 核心功能说明

### 用户角色

系统支持三种用户角色：

1. **普通用户（student）**
   - 查看和完成关卡
   - 查看个人积分
   - 参与抽奖活动
   - 查看中奖记录

2. **管理员（admin）**
   - 普通用户的所有权限
   - 管理关卡（创建、编辑、删除）
   - 管理奖品
   - 查看用户数据
   - 修改用户积分

3. **超级管理员（super_admin）**
   - 管理员的所有权限
   - 用户权限管理
   - 系统配置管理
   - 数据统计和导出

### API 端点

#### 认证相关
- `POST /api/login` - 用户登录
- `POST /api/register` - 用户注册
- `POST /api/logout` - 用户登出
- `GET /api/check-auth` - 检查认证状态

#### 用户管理
- `GET /api/members` - 获取用户列表
- `GET /api/members/{stuId}` - 获取用户详情
- `PUT /api/members/{stuId}/points` - 修改用户积分
- `PUT /api/members/{stuId}/role` - 修改用户角色

#### 关卡管理
- `GET /api/levels` - 获取关卡列表
- `POST /api/levels` - 创建关卡
- `PUT /api/levels/{level_id}` - 更新关卡
- `DELETE /api/levels/{level_id}` - 删除关卡
- `POST /api/levels/complete` - 完成关卡（获得积分）

#### 奖品管理
- `GET /api/prizes` - 获取奖品列表
- `POST /api/prizes` - 创建奖品
- `PUT /api/prizes/{prize_id}` - 更新奖品
- `DELETE /api/prizes/{prize_id}` - 删除奖品
- `POST /api/lottery` - 抽奖
- `POST /api/prizes/redeem` - 兑换奖品

## 🔧 配置说明

### MongoDB 配置

```ini
[MongoDB]
connectionstring = mongodb://username:password@host:port/?authSource=database
databasename = welcomesystem
```

- `connectionstring`：MongoDB 连接字符串
- `databasename`：数据库名称

### 系统配置

```ini
[System]
salt = your_secure_salt_here
```

- `salt`：密码加密盐值，请设置为随机字符串

### 默认管理员

```ini
[DefaultAdmin]
stuid = super_admin
password = your_secure_password
role = super_admin
```

首次启动时会自动创建该管理员账户。

### 抽奖配置

```ini
[Lottery]
points = 1
```

- `points`：每次抽奖消耗的积分数

## 📊 数据库设计

### 用户集合（user）

```javascript
{
  "_id": ObjectId,
  "stuId": String,           // 学号
  "name": String,            // 姓名
  "password": String,        // 密码（哈希）
  "role": String,            // 角色：student/admin/super_admin
  "points": Number,          // 积分
  "completedLevels": Array,  // 已完成关卡ID列表
  "creatTime": Date          // 创建时间
}
```

### 关卡集合（level）

```javascript
{
  "_id": ObjectId,
  "name": String,            // 关卡名称
  "description": String,     // 关卡描述
  "points": Number,          // 完成后获得的积分
  "location": String,        // 关卡位置
  "isActive": Boolean        // 是否启用
}
```

### 奖品集合（prize）

```javascript
{
  "_id": ObjectId,
  "name": String,            // 奖品名称
  "description": String,     // 奖品描述
  "imageUrl": String,        // 奖品图片
  "total": Number,           // 总数量
  "remaining": Number,       // 剩余数量
  "probability": Number,     // 中奖概率
  "drawn_count": Number,     // 已抽中数量
  "redeemed_count": Number,  // 已兑换数量
  "created_at": Date,        // 创建时间
  "updated_at": Date         // 更新时间
}
```

## 🔒 安全建议

1. **修改默认密码**：首次部署后立即修改默认管理员密码
2. **使用强密码**：确保配置文件中的密码足够复杂
3. **保护配置文件**：`config.ini` 不应提交到版本控制系统
4. **HTTPS 部署**：生产环境建议使用 HTTPS
5. **定期备份**：定期备份 MongoDB 数据库
6. **更新依赖**：及时更新依赖包以修复安全漏洞

## 🐛 故障排除

### 无法连接到 MongoDB

- 检查 MongoDB 服务是否启动
- 确认 `config.ini` 中的连接字符串是否正确
- 检查网络连接和防火墙设置

### 登录失败

- 确认用户名和密码是否正确
- 检查数据库中是否存在该用户
- 查看日志文件了解详细错误信息

### 静态文件无法加载

- 确认 `Pages` 目录结构完整
- 检查文件路径是否正确
- 清除浏览器缓存后重试

## 📝 开发说明

### 添加新的 API 端点

1. 在 `api/routes/` 目录下创建或修改路由文件
2. 在 `config/app_config.py` 中注册新路由
3. 如需认证，使用 `api/dependencies/auth.py` 中的装饰器

### 扩展核心功能

1. 在 `Core/` 目录下创建新模块
2. 实现业务逻辑类
3. 在相应的路由中调用

### 前端页面开发

1. 在 `Pages/` 目录下创建功能目录
2. 遵循现有的目录结构（html/、css/、js/）
3. 使用公共资源（`Pages/Common/`）保持风格一致

## 📄 许可证

本项目仅供学习和研究使用。

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至项目维护者

---

**注意**：本系统为迎新活动设计，请根据实际需求进行定制和部署。
