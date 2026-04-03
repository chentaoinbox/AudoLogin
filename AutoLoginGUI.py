import tkinter as tk
from tkinter import ttk
import threading
import base64
import os
import json
import datetime
import sys
import time
import AutoLogin
from AutoLogin import AutoLogin  # 请确保 AutoLogin 类在 AutoLogin.py 中

class LoginGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("上海大学校园网自动登录")
        self.root.geometry("500x420")
        self.root.configure(bg='white')
        self.root.resizable(False, False)

        # 确定程序所在路径（支持 PyInstaller 打包）
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)          # exe 所在目录
            self.resource_path = sys._MEIPASS                         # 资源解压目录（_internal）
        else:
            self.base_path = os.path.dirname(__file__)                # 脚本所在目录
            self.resource_path = self.base_path                       # 未打包时资源就在脚本目录

        # 配置文件夹和配置文件
        self.config_dir = os.path.join(self.base_path, 'config')
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self.log_dir = os.path.join(self.base_path, 'log')
        self.log_file = os.path.join(self.log_dir, 'auth.log')
        icon_path = os.path.join(self.resource_path,"image", 'logo.png')
        self.ensure_dirs()
        self.is_logging_in = False
        self.scheduled_id = None
        self.schedule_enabled = False
        self.last_auto_run_minute = None
        self.auth = None

        if os.path.exists(icon_path):
            self.icon = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, self.icon)

        # 样式：白色背景，深色文字
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TLabel', background='white', foreground='#333333', font=('微软雅黑', 10))
        self.style.configure('TEntry', fieldbackground='white', foreground='#333333', font=('微软雅黑', 10))
        self.style.configure('TButton', background='white', foreground='#333333', font=('微软雅黑', 10))
        self.style.configure('TCheckbutton', background='white', foreground='#333333', font=('微软雅黑', 10))
        self.style.map('TButton', background=[('active', '#f0f0f0')])
        self.style.configure('TFrame', background='white')
        # 主容器
        main_frame = ttk.Frame(self.root,style='TFrame')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # 标题
        ttk.Label(main_frame, text="上海大学校园网自动登录", font=('微软雅黑', 18, 'bold')).pack(pady=(0, 20))

        # 用户名
        user_frame = ttk.Frame(main_frame)
        user_frame.pack(fill='x', pady=5)
        ttk.Label(user_frame, text="用户名:", width=8, anchor='e').pack(side='left', padx=(0, 10))
        self.username_entry = ttk.Entry(user_frame, width=30)
        self.username_entry.pack(side='left', fill='x', expand=True)

        # 密码
        pwd_frame = ttk.Frame(main_frame)
        pwd_frame.pack(fill='x', pady=5)
        ttk.Label(pwd_frame, text="密码:", width=8, anchor='e').pack(side='left', padx=(0, 10))
        self.password_entry = ttk.Entry(pwd_frame, width=30, show="*")
        self.password_entry.pack(side='left', fill='x', expand=True)

        # 记住密码
        self.remember_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="记住密码", variable=self.remember_var,
                        command=self.on_remember_toggle).pack(pady=5, anchor='center')

        # 定时运行区域（居中）
        timer_frame = ttk.Frame(main_frame)
        timer_frame.pack(pady=5, fill='x')

        # 内部居中容器
        inner_frame = ttk.Frame(timer_frame)
        inner_frame.pack(anchor='center')

        self.schedule_var = tk.BooleanVar()
        ttk.Checkbutton(inner_frame, text="定时运行", variable=self.schedule_var,
                        command=self.on_schedule_toggle).pack(side='left')

        self.interval_var = tk.StringVar(value="30")
        self.interval_entry = ttk.Entry(inner_frame, width=6, textvariable=self.interval_var, state='normal')
        self.interval_entry.pack(side='left', padx=(10, 5))

        ttk.Label(inner_frame, text="分钟").pack(side='left')
        self.next_run_label = ttk.Label(inner_frame, text="", foreground='#666666')
        self.next_run_label.pack(side='left', padx=(10, 0))

        # 登录按钮
        self.login_btn = ttk.Button(main_frame, text="登 录", command=self.start_login, width=20)
        self.login_btn.pack(pady=15)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground='blue')
        self.status_label.pack(pady=5)

        # 加载配置
        self.load_config()
        self._update_auth_instance()

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def ensure_dirs(self):
        for d in [self.config_dir, self.log_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

    def load_config(self):
        default_config = {
            'username': '',
            'password': '',
            'remember': False,
            'schedule_enabled': False,
            'schedule_interval': 30
        }
        config = default_config.copy()
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    config.update(loaded)
            except:
                pass

        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        if config['username']:
            self.username_entry.insert(0, config['username'])
        if config['password']:
            try:
                pwd = base64.b64decode(config['password']).decode()
                self.password_entry.insert(0, pwd)
            except:
                pass
        self.remember_var.set(config['remember'])
        self.schedule_var.set(config.get('schedule_enabled', False))
        self.interval_var.set(str(config.get('schedule_interval', 30)))

        if self.schedule_var.get():
            self.enable_schedule()
        else:
            self.disable_schedule()

    def save_config(self):
        config = {
            'username': self.username_entry.get().strip(),
            'password': '',
            'remember': self.remember_var.get(),
            'schedule_enabled': self.schedule_var.get(),
            'schedule_interval': int(self.interval_var.get() or 30)
        }
        if self.remember_var.get() and config['username'] and self.password_entry.get():
            config['password'] = base64.b64encode(self.password_entry.get().encode()).decode()
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _update_auth_instance(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if username and password:
            try:
                self.auth = AutoLogin(username, password, log_file=self.log_file)
            except Exception as e:
                self.auth = None
                self.update_status(f"创建认证实例失败: {str(e)}", False)
        else:
            self.auth = None

    def on_remember_toggle(self):
        self.save_config()
        self._update_auth_instance()

    def on_schedule_toggle(self):
        if self.schedule_var.get():
            self.enable_schedule()
        else:
            self.disable_schedule()
        self.save_config()

    def enable_schedule(self):
        self.schedule_enabled = True
        self.interval_entry.config(state='normal')
        self.schedule_login()

    def disable_schedule(self):
        self.schedule_enabled = False
        if self.scheduled_id:
            self.root.after_cancel(self.scheduled_id)
            self.scheduled_id = None
        self.next_run_label.config(text="")

    def schedule_login(self):
        if not self.schedule_enabled:
            return
        try:
            minutes = float(self.interval_var.get())
            if minutes <= 0:
                raise ValueError
            interval_ms = int(minutes * 60 * 1000)
        except:
            interval_ms = 30 * 60 * 1000

        # 先取消旧任务，避免重复排程导致短时间内多次自动触发
        if self.scheduled_id:
            self.root.after_cancel(self.scheduled_id)
            self.scheduled_id = None

        # 对齐到“绝对时间刻度”，尽量在 xx:xx:00.000 这类边界触发
        now_ms = time.time_ns() // 1_000_000
        next_run_ms = ((now_ms // interval_ms) + 1) * interval_ms
        delay_ms = max(1, next_run_ms - now_ms)
        next_time = datetime.datetime.fromtimestamp(next_run_ms / 1000)
        self.next_run_label.config(text=f"下次运行: {next_time.strftime('%H:%M:%S')}")
        self.scheduled_id = self.root.after(delay_ms, self.scheduled_login_callback)

    def scheduled_login_callback(self):
        if not self.schedule_enabled:
            return
        self.scheduled_id = None

        # 防止在同一分钟内重复自动启动
        minute_key = datetime.datetime.now().strftime('%Y%m%d%H%M')
        if self.last_auto_run_minute == minute_key:
            self.schedule_login()
            return
        self.last_auto_run_minute = minute_key

        self.start_login()
        self.schedule_login()

    def on_closing(self):
        self.disable_schedule()
        self.save_config()
        self.root.destroy()

    def start_login(self):
        if self.is_logging_in:
            self.update_status("登录任务正在执行中，请稍后重试", False)
            return
        if not self.auth:
            self._update_auth_instance()
            if not self.auth:
                self.update_status("请检查用户名和密码是否正确", False)
                return
        self.login_btn.config(state=tk.DISABLED)
        self.update_status("正在认证，请稍候...", None)
        self.is_logging_in = True
        threading.Thread(target=self.do_login, daemon=True).start()

    def do_login(self):
        try:
            success, message = self.auth.login()
            if success:
                self.update_status(f"认证成功：{message}", True)
                self.save_config()
                self._update_auth_instance()
                self.root.after(0, lambda: self.login_btn.config(state=tk.NORMAL))
            else:
                # 检查是否为指定的错误信息
                if "WEB认证设备未注册" in message and "请确认SAM+/portal/设备上的参数配置是否一致" in message:
                    self.update_status(f"第一次认证失败：{message}，2秒后重试...", False)
                    time.sleep(2)
                    self.update_status("正在重试...", None)
                    try:
                        retry_success, retry_message = self.auth.login()
                        if retry_success:
                            self.update_status(f"重试认证成功：{retry_message}", True)
                            self.save_config()
                            self._update_auth_instance()
                        else:
                            self.update_status(f"重试认证失败：{retry_message}", False)
                    except Exception as e:
                        self.update_status(f"重试时发生异常：{str(e)}", False)
                    finally:
                        self.root.after(0, lambda: self.login_btn.config(state=tk.NORMAL))
                else:
                    # 其他错误不重试
                    self.update_status(f"认证失败：{message}", False)
                    self.root.after(0, lambda: self.login_btn.config(state=tk.NORMAL))
        except Exception as e:
            self.update_status(f"发生异常：{str(e)}", False)
            self.root.after(0, lambda: self.login_btn.config(state=tk.NORMAL))
        finally:
            self.is_logging_in = False

    def update_status(self, message, success):
        def _update():
            self.status_var.set(message)
            if success is True:
                self.status_label.configure(foreground='green')
            elif success is False:
                self.status_label.configure(foreground='red')
            else:
                self.status_label.configure(foreground='blue')
        self.root.after(0, _update)

    def run(self):
        self.do_login()
        self.root.mainloop()

if __name__ == "__main__":
    app = LoginGUI()
    app.run()