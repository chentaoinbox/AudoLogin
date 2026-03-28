# 上海大学校园网自动登录工具

一个基于 Python 的校园网 Portal 自动认证程序，提供命令行核心与图形界面两种使用方式，适合在网络掉线后自动重连认证。

## 主要功能

- 自动完成 Portal 跳转链路并提取登录参数
- 支持按页面返回的公钥参数进行密码加密提交
- 登录前自动检测在线状态，已在线时不重复认证
- GUI 支持账号输入、状态显示与一键登录
- 支持记住密码、定时认证和本地日志记录
- 针对特定认证错误自动等待 2 秒后重试一次

## 项目结构

```text
Autologin/
├─ AutoLogin.py            # 认证核心逻辑（请求、参数解析、加密、登录）
├─ AutoLoginGUI.py         # Tkinter 图形界面
├─ config/
│  └─ config.json          # 本地配置文件（首次保存配置后生成/更新）
├─ image/
│  └─ logo.png             # GUI 图标（可选）
├─ log/
│  └─ auth.log             # 运行日志（按需生成）
├─ LICENSE
└─ README.md
```

## 环境要求

- Windows
- Python 3.8 及以上（推荐 3.10+）

## 安装依赖

```bash
pip install requests chardet
```

说明：tkinter、threading、json 等为标准库，通常无需额外安装。

## 快速开始

### 图形界面方式（推荐）

```bash
python AutoLoginGUI.py
```

首次使用建议步骤：

1. 输入用户名和密码
2. 按需勾选记住密码
3. 按需开启定时运行并设置间隔（分钟）
4. 点击登录

### 命令行方式

直接运行示例脚本：

```bash
python AutoLogin.py
```

在其他脚本中调用：

```python
from AutoLogin import AutoLogin

auth = AutoLogin(
		username="你的学号",
		password="你的密码",
		base_url="http://10.10.9.9",
		log_file="log/auth.log"
)
success, message = auth.login()
print(success, message)
```

## 配置文件说明

路径：config/config.json

字段说明：

- username：用户名
- password：Base64 编码后的密码（仅编码，不是强加密）
- remember：是否记住密码
- schedule_enabled：是否启用定时运行
- schedule_interval：定时间隔（分钟）

示例：

```json
{
	"username": "your_student_id",
	"password": "base64_password_here",
	"remember": false,
	"schedule_enabled": true,
	"schedule_interval": 30
}
```

## 日志与运行行为

- GUI 启动时会自动触发一次认证
- 日志默认写入 log/auth.log
- GUI 状态栏会显示认证中、成功、失败
- 认证核心文件日志记录 DEBUG，控制台默认仅显示 WARNING 及以上

## 打包为 EXE（可选）

项目已兼容 PyInstaller 资源路径判断（frozen 与 _MEIPASS）。

```bash
pyinstaller -F -w AutoLoginGUI.py --add-data "image;image"
```

如打包后未显示图标，请确认 image/logo.png 已正确打包。

## 常见问题

1. 登录失败或页面获取异常

- 确认当前网络环境可访问校园网 Portal
- 确认认证网关地址是否正确（默认 base_url 为 http://10.10.9.9）

2. 勾选记住密码后未自动填充

- 确认 config/config.json 写入成功
- 确认程序目录具备写权限

3. 定时运行未触发

- 确认已启用定时运行，且间隔大于 0
- 程序需保持运行，不可直接结束进程

## 安全提示

- 记住密码使用 Base64 编码，不属于安全加密存储
- 共享设备不建议启用记住密码
- 如有安全要求，建议自行接入系统凭据管理或本地加密方案

## 许可证

本项目许可证见 LICENSE。

## 免责声明

本项目仅用于个人学习与合法合规的校园网络认证自动化，请勿用于任何未授权用途。
