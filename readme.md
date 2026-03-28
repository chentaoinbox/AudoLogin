# 上海大学校园网自动登录工具

一个基于 Python 的校园网 Portal 自动认证工具，包含：

- 命令行登录核心（AutoLogin.py）
- 图形界面客户端（AutoLoginGUI.py）
- 可选定时认证、失败重试、日志记录与配置持久化

适用于需要避免校园网掉线后手动重复登录的场景。

## 功能特性

- 自动完成 Portal 跳转链路并抓取登录参数
- 支持页面接口返回的 RSA 参数进行密码加密
- 登录前自动检测在线状态，已在线则不重复认证
- 图形界面支持账号密码输入与一键登录
- 支持“记住密码”（本地 Base64 存储）
- 支持按分钟定时执行认证
- 对指定错误信息自动等待 2 秒后重试一次
- 记录认证日志到本地文件

## 项目结构

```text
Autologin/
├─ AutoLogin.py            # 登录核心逻辑（HTTP 请求、参数解析、加密、提交认证）
├─ AutoLoginGUI.py         # Tkinter 图形界面
├─ config/
│  └─ config.json          # 本地配置（账号、密码、定时设置等）
├─ log/
│  └─ auth.log             # 运行日志
├─ image/
│  └─ logo.png             # 窗口图标（可选）
└─ readme.md
```

## 运行环境

- Windows（当前项目主要面向 Windows 使用）
- Python 3.8 及以上（推荐 3.10+）

## 安装依赖

项目使用到的第三方库：

- requests
- chardet

安装命令：

```bash
pip install requests chardet
```

说明：tkinter、json、threading 等为 Python 标准库，通常无需额外安装。

## 快速开始

### 方式一：图形界面（推荐）

```bash
python AutoLoginGUI.py
```

首次打开后：

1. 输入用户名和密码
2. 可选勾选记住密码
3. 可选开启定时运行并设置间隔（分钟）
4. 点击登录

### 方式二：命令行调用核心类

可直接运行：

```bash
python AutoLogin.py
```

也可在其他脚本中调用：

```python
from AutoLogin import AutoLogin

auth = AutoLogin(username="你的学号", password="你的密码", log_file="log/auth.log")
success, message = auth.login()
print(success, message)
```

## 配置文件说明

配置文件路径：config/config.json

主要字段：

- username：用户名
- password：Base64 编码后的密码（仅编码，不是强加密）
- remember：是否记住密码
- schedule_enabled：是否启用定时运行
- schedule_interval：定时间隔（分钟）

示例：

```json
{
	"username": "99720000",
	"password": "Q1QmMDAMMTAwOGN0QHNOdS5jb2g=",
	"remember": true,
	"schedule_enabled": true,
	"schedule_interval": 20
}
```

## 日志说明

- 日志文件默认输出到：log/auth.log
- GUI 界面会显示认证状态（进行中、成功、失败）
- 核心模块内部日志级别：文件记录 DEBUG，控制台仅显示 WARNING 及以上

## 打包说明（可选）

代码中已兼容 PyInstaller 的资源路径判断（sys.frozen 与 _MEIPASS）。

可参考如下命令打包：

```bash
pyinstaller -F -w AutoLoginGUI.py --add-data "image;image"
```

如果打包后不显示图标，请确认 image/logo.png 是否被正确打包到资源目录。

## 常见问题

1. 登录失败，提示网络或页面获取异常

- 先确认当前网络环境可访问校园网 Portal
- 检查 base_url 是否与实际认证网关一致（默认是 http://10.10.9.9）

2. 勾选记住密码但下次没有自动填充

- 检查 config/config.json 是否成功写入
- 检查程序运行目录是否有写权限

3. 定时运行没有触发

- 确认已勾选定时运行，且间隔为大于 0 的数字
- 程序窗口不能被强制结束，需保持运行

## 安全提示

- 本项目的“记住密码”采用 Base64 编码存储，不等同于加密。
- 请勿在共享电脑上启用记住密码，或自行替换为更安全的本地加密方案。

## 免责声明

本项目仅用于个人学习与合法合规的校园网络认证自动化，不得用于任何未授权用途。
