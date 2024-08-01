import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import time
import requests
import threading
import re
import os
from ttkthemes import ThemedTk
import ctypes
import sys

class WebsiteMonitorApp:
    def __init__(self):
        self.URL_FILE = "website_urls.txt"
        self.website_statuses = {}
        self.website_index_map = {}
        self.notification_interval = 60

        # 获取打包后的可执行文件路径
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件路径
            self.application_path = os.path.dirname(sys.executable)
        else:
            # 正常运行的 Python 脚本路径
            self.application_path = os.path.dirname(__file__)

        self.root = ThemedTk(theme="arc")  # 使用ThemedTk来创建根窗口，并设置主题
        self.root.geometry("250x350")  # 设置窗口大小
        self.root.title("网站状态监控")  # 设置窗口标题
        self.root.configure(bg='white')  # 设置窗口的背景色为白色
        self.root.attributes('-alpha', 0.9)  # 设置窗口的透明度为90%

        # 设置窗口图标
        icon_path = os.path.join(self.application_path, 'xdlovelife.ico')
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # PyInstaller 打包后的情况
            icon_path = os.path.join(sys._MEIPASS, 'xdlovelife.ico')
        self.root.iconbitmap(icon_path)

        self.style = ttk.Style(self.root)
        self.style.configure("Custom.TFrame", background="white")  # 设置Frame的背景色为白色
        self.style.configure("Custom.TEntry", background="white", foreground="black")  # 设置Entry的背景色为白色，前景色为黑色
        self.style.configure("Custom.TListbox", background="white", foreground="black", selectbackground="gray40", selectforeground="white")  # 设置Listbox的背景色为白色，前景色为黑色，选择背景色为灰色40，选择前景色为白色

        self.create_widgets()
        self.load_and_monitor_website_urls()
        self.create_menu()
        self.root.mainloop()

    def create_widgets(self):
        self.url_label = ttk.Label(self.root, text="请输入需要监控的网站链接:", background='white', foreground='black')
        self.url_label.pack(pady=10)

        self.url_entry = ttk.Entry(self.root, width=50, style="Custom.TEntry")
        self.url_entry.pack(pady=5)

        self.add_button = ttk.Button(self.root, text="添加网站", command=self.add_website)
        self.add_button.pack(pady=5)

        self.list_label = ttk.Label(self.root, text="继续监控的网站:", background='white', foreground='black')
        self.list_label.pack()

        self.listbox = tk.Listbox(self.root, width=70, height=10, bg="white", fg="black", selectbackground="gray40", selectforeground="white", exportselection=False, font=("Helvetica", 10))
        self.listbox.pack(pady=5)

        self.center_label_frame = ttk.Frame(self.root, style="Custom.TFrame")
        self.center_label_frame.pack(pady=10)

        # 创建右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="暂停监控", command=self.pause_website)
        self.context_menu.add_command(label="继续监控", command=self.resume_website)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除选中网址", command=self.remove_website)
        self.context_menu.add_command(label="更改监控频率", command=self.change_monitoring_frequency)

        # 绑定右键事件到列表框
        self.listbox.bind("<Button-3>", self.popup_menu)

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        theme_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="主题", menu=theme_menu)
        theme_menu.add_command(label="winnative", command=lambda: self.change_theme("winnative"))
        theme_menu.add_command(label="clam", command=lambda: self.change_theme("clam"))
        theme_menu.add_command(label="alt", command=lambda: self.change_theme("alt"))
        theme_menu.add_command(label="default", command=lambda: self.change_theme("default"))
        theme_menu.add_command(label="classic", command=lambda: self.change_theme("classic"))
        theme_menu.add_command(label="vista", command=lambda: self.change_theme("vista"))
        theme_menu.add_command(label="xpnative", command=lambda: self.change_theme("xpnative"))
        theme_menu.add_command(label="mac", command=lambda: self.change_theme("mac"))  # 添加mac主题选项

        about_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="关于", menu=about_menu)
        about_menu.add_command(label="联系方式", command=self.show_contact_info)

    def change_theme(self, theme_name):
        self.root.set_theme(theme_name)

    def load_and_monitor_website_urls(self):
        website_urls = self.load_website_urls()
        for url in website_urls:
            if url not in self.website_statuses:
                self.website_statuses[url] = {"status": "监控中...", "running": True, "paused": False}
                index = self.listbox.size()
                self.listbox.insert(tk.END, f"{url} - 监控中...")
                self.website_index_map[url] = index
                self.monitor_website(url)

    def load_website_urls(self):
        if os.path.exists(self.URL_FILE):
            with open(self.URL_FILE, "r") as f:
                return f.read().splitlines()
        else:
            return []

    def save_website_urls(self):
        with open(self.URL_FILE, "w") as f:
            for url in self.website_statuses:
                f.write(url + "\n")

    def add_website(self):
        url = self.url_entry.get().strip()
        if url != '':
            if not re.match(r'^https?://', url):
                url = f'https://{url}'

            if url not in self.website_statuses:
                self.website_statuses[url] = {"status": "未知状态", "running": True, "paused": False}
                index = self.listbox.size()
                self.listbox.insert(tk.END, f"{url} - 未知状态")
                self.website_index_map[url] = index
                self.save_website_urls()
                self.notify_status_change(url)  # 添加网站时弹出消息框
                self.url_entry.delete(0, tk.END)
                self.monitor_website(url)
            else:
                messagebox.showwarning("重复添加", f"网站已存在：{url}")
        else:
            messagebox.showerror("输入错误", "请输入有效的网站链接")

    def remove_website(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            index = selected_index[0]
            url = self.listbox.get(index).split(' - ')[0]
            del self.website_statuses[url]
            del self.website_index_map[url]
            self.listbox.delete(index)
            self.save_website_urls()
            messagebox.showinfo("删除成功", f"已删除网站：{url}")

    def pause_website(self):
        selected_index = self.listbox.index(tk.ACTIVE)
        if selected_index != -1:
            url = self.listbox.get(selected_index).split(' - ')[0]
            if not self.website_statuses[url]["paused"]:
                self.website_statuses[url]["paused"] = True
                self.update_status_in_listbox()
                messagebox.showinfo("已暂停", f"已暂停监控网站：{url}")

    def resume_website(self):
        selected_index = self.listbox.index(tk.ACTIVE)
        if selected_index != -1:
            url = self.listbox.get(selected_index).split(' - ')[0]
            if self.website_statuses[url]["paused"]:
                self.website_statuses[url]["paused"] = False
                self.monitor_website(url)
                self.update_status_in_listbox()
                messagebox.showinfo("已恢复监控", f"已恢复监控网站：{url}")

    def check_website(self, url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return True, "正常 ✅"
            else:
                return False, f"异常（状态码：{response.status_code}）"
        except requests.exceptions.RequestException as e:
            return False, f"无法访问 ({str(e)})"

    def update_status_in_listbox(self):
        for url, status_info in self.website_statuses.items():
            index = self.website_index_map.get(url)
            if index is not None:
                current_text = self.listbox.get(index)
                if status_info["paused"]:
                    if not current_text.endswith(" - 暂停监控"):
                        self.listbox.delete(index)
                        self.listbox.insert(index, f"{url} - 暂停监控")
                elif not status_info["running"]:
                    if not current_text.endswith(" - 停止监控"):
                        self.listbox.delete(index)
                        self.listbox.insert(index, f"{url} - 停止监控")
                else:
                    if not current_text.endswith(f" - {status_info['status']}"):
                        self.listbox.delete(index)
                        self.listbox.insert(index, f"{url} - {status_info['status']}")

    def monitor_website(self, url):
        def monitor_single_website():
            while True:
                if not self.website_statuses[url]["running"]:
                    time.sleep(1)
                    continue

                if self.website_statuses[url]["paused"]:
                    time.sleep(1)
                    continue

                current_status, status_text = self.check_website(url)
                previous_status = self.website_statuses[url]["status"]

                if current_status != previous_status:
                    self.website_statuses[url]["status"] = status_text
                    self.notify_status_change(url)
                    self.update_status_in_listbox()

                time.sleep(self.notification_interval)

        threading.Thread(target=monitor_single_website, daemon=True).start()

    def notify_status_change(self, url):
        top = tk.Toplevel(self.root)
        top.overrideredirect(True)  # 隐藏窗口边框和标题栏
        top.configure(bg='white')

        width = 300
        height = 100
        corner_radius = 20
        border_width = 2
        content_box = 10

        # 设置窗口的几何形状，带有圆角边框
        top.geometry(f"{width}x{height}+{self.get_window_x_position(width)}+{self.get_window_y_position(height)}")
        top.attributes('-alpha', 0.8)  # 设置透明度为80%

        # 创建画布，并绘制带有圆角边框的窗口形状
        canvas = tk.Canvas(top, width=width, height=height, bg='white', highlightthickness=0)
        canvas.pack()

        # 绘制带有圆角边框的矩形（边框）
        canvas.create_polygon(
            corner_radius, 0,
            width - corner_radius, 0,
            width, corner_radius,
            width, height - corner_radius,
            width - corner_radius, height,
            corner_radius, height,
            0, height - corner_radius,
            0, corner_radius,
            fill='white', outline='white'
        )

        # 绘制带有圆角边框的矩形（内容框）
        content_box = canvas.create_polygon(
            corner_radius + border_width, border_width,
            width - corner_radius - border_width, border_width,
            width - border_width, corner_radius + border_width,
            width - border_width, height - corner_radius - border_width,
            width - corner_radius - border_width, height - border_width,
            corner_radius + border_width, height - border_width,
            border_width, height - corner_radius - border_width,
            border_width, corner_radius + border_width,
            fill='white', outline='white'
        )

        # 标签和消息文本与内容框的内边距
        message = f"网站状态更新：{url} - 正常"
        label = tk.Label(top, text=message, bg='white', fg='black', padx=15, pady=10, wraplength=260)
        label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # 恢复透明度和关闭窗口的函数
        def restore_alpha():
            top.attributes('-alpha', 0.8)  # 恢复默认透明度
            top.destroy()

        # 定时器，5秒后恢复默认透明度并关闭窗口
        top.after(10000, restore_alpha)

    def popup_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def change_monitoring_frequency(self):
        selected_index = self.listbox.index(tk.ACTIVE)
        if selected_index != -1:
            url = self.listbox.get(selected_index).split(' - ')[0]
            new_interval = simpledialog.askinteger("更改监控频率", "请输入新的监控频率（秒）:", initialvalue=self.notification_interval)
            if new_interval:
                self.website_statuses[url]["running"] = False
                time.sleep(1)
                self.notification_interval = new_interval
                self.website_statuses[url]["running"] = True
                messagebox.showinfo("成功", f"监控频率已更改为 {new_interval} 秒")

    def show_contact_info(self):
        contact_info = "如有问题请联系 @xdlovelife 📨\n\nTwitter: https://twitter.com/xdlovelife\nGithub: https://github.com/xdlovelife"
        messagebox.showinfo("联系方式", contact_info)

    def get_window_x_position(self, width):
        screen_width = self.root.winfo_screenwidth()
        return screen_width - width - 30  # 向左偏移30像素

    def get_window_y_position(self, height):
        screen_height = self.root.winfo_screenheight()
        taskbar_height = ctypes.windll.user32.GetSystemMetrics(2)  # 获取任务栏高度
        return screen_height - taskbar_height - height - 20  # 位于任务栏顶部20像素左偏移的位置

if __name__ == "__main__":
    app = WebsiteMonitorApp()
