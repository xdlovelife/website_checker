import subprocess
import sys
import os
import tkinter as tk
from tkinter import messagebox, Menu
from tkinter.ttk import Progressbar
import time
import requests
import threading
import re
from win10toast import ToastNotifier  # Import ToastNotifier for notifications

# 定义所需的第三方包列表
REQUIRED_PACKAGES = ["requests", "win10toast"]

# 全局变量，用于存储通知时间间隔
notification_interval = 60  # 每60秒（1分钟）显示一次通知

# 检查依赖项并启动主程序的函数
def check_dependencies_and_start():
    try:
        import requests
        from win10toast import ToastNotifier
        messagebox.showinfo("已安装", "您已安装所需的依赖项！")
        start_main_program()
    except ImportError:
        # 如果依赖项未安装，询问用户是否安装
        if messagebox.askyesno("未安装依赖", "程序需要安装所需的依赖项才能继续，是否现在安装？"):
            install_dependencies()
        else:
            sys.exit(1)  # 如果用户选择不安装依赖项，则退出程序

# 安装依赖项的函数
def install_dependencies():
    progress_window = tk.Toplevel()
    progress_window.title("安装依赖")

    progress_label = tk.Label(progress_window, text="正在安装依赖，请稍候...")
    progress_label.pack(padx=20, pady=10)

    progress_bar = Progressbar(progress_window, orient=tk.HORIZONTAL, length=200, mode='indeterminate')
    progress_bar.pack(padx=20, pady=10)
    progress_bar.start()

    try:
        for package in REQUIRED_PACKAGES:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

        progress_bar.stop()
        progress_window.destroy()  # 关闭进度窗口
        messagebox.showinfo("安装完成", "所有依赖项已成功安装！")
        start_main_program()  # 安装完成后启动主程序
    except Exception as e:
        progress_bar.stop()
        progress_window.destroy()  # 关闭进度窗口
        messagebox.showerror("安装失败", f"安装过程中出现错误：{e}")
        sys.exit(1)  # 如果安装失败，退出程序

# 启动主程序的函数
def start_main_program():
    # 存储网站URL的文件路径
    URL_FILE = "website_urls.txt"

    # 存储网站状态的字典
    website_statuses = {}
    # 存储网站URL和在列表框中的索引的映射
    website_index_map = {}
    listbox = None  # 全局变量，用于存储列表框对象的引用

    # 初始化Toast通知器
    global toaster
    toaster = ToastNotifier()

    # 加载已保存的网站URL的函数
    def load_website_urls():
        if os.path.exists(URL_FILE):
            with open(URL_FILE, "r") as f:
                return f.read().splitlines()
        else:
            return []

    # 将网站URL保存到文件的函数
    def save_website_urls():
        with open(URL_FILE, "w") as f:
            for url in website_statuses:
                f.write(url + "\n")

    # 加载已保存的网站URL并开始监控的函数
    def load_and_monitor_website_urls():
        nonlocal listbox
        nonlocal website_statuses

        # 加载现有的网站URL
        website_urls = load_website_urls()

        # 初始化每个网站的状态并开始监控
        for url in website_urls:
            if url not in website_statuses:
                website_statuses[url] = {"status": "监控中...", "running": True, "paused": False}  # 添加网站状态、运行状态和暂停状态
                index = listbox.size()  # 获取当前列表框大小作为索引
                listbox.insert(tk.END, f"{url} - 监控中...")  # 向列表框添加网站URL和状态
                website_index_map[url] = index  # 存储网站URL和索引的映射
                monitor_website(url)  # 开始监控网站

    # 添加网站URL的函数
    def add_website():
        nonlocal listbox
        url = url_entry.get().strip()
        if url != '':
            # 验证和修复URL格式
            if not re.match(r'^https?://', url):
                url = f'https://{url}'  # 如果URL不以http://或https://开头，则添加https://

            if url not in website_statuses:
                website_statuses[url] = {"status": "未知状态", "running": True, "paused": False}  # 初始化状态、运行状态和暂停状态
                index = listbox.size()  # 获取当前列表框大小作为索引
                listbox.insert(tk.END, f"{url} - 未知状态")  # 向列表框添加新的网站URL和状态
                website_index_map[url] = index  # 存储网站URL和索引的映射
                save_website_urls()  # 将更新后的网站URL列表保存到文件
                messagebox.showinfo("添加成功", f"已添加网站：{url}")
                url_entry.delete(0, tk.END)

                # 立即开始监控新添加的网站URL
                monitor_website(url)  # 直接调用monitor_website(url)开始监控新网站
            else:
                messagebox.showwarning("重复添加", f"网站已存在：{url}")
        else:
            messagebox.showerror("输入错误", "请输入有效的网站链接")

    # 删除选定的网站URL的函数
    def remove_website(event=None):
        nonlocal listbox
        selected_index = listbox.curselection()
        if selected_index:
            index = selected_index[0]
            url = listbox.get(index).split(' - ')[0]  # 从列表框条目中获取网站URL部分
            del website_statuses[url]  # 从状态字典中删除网站URL
            del website_index_map[url]  # 从映射字典中删除网站URL索引映射
            listbox.delete(index)
            save_website_urls()  # 将更新后的网站URL列表保存到文件
            messagebox.showinfo("删除成功", f"已删除网站：{url}")

    # 暂停监控选定的网站URL的函数
    def pause_website(event=None):
        nonlocal listbox
        selected_index = listbox.index(tk.ACTIVE)
        if selected_index != -1:
            url = listbox.get(selected_index).split(' - ')[0]  # 从列表框条目中获取网站URL部分
            if not website_statuses[url]["paused"]:
                website_statuses[url]["paused"] = True  # 设置暂停状态为True
                update_status_in_listbox()  # 更新列表框中的状态显示
                messagebox.showinfo("已暂停", f"已暂停监控网站：{url}")

    # 继续监控选定的网站URL的函数
    def resume_website(event=None):
        nonlocal listbox
        selected_index = listbox.index(tk.ACTIVE)
        if selected_index != -1:
            url = listbox.get(selected_index).split(' - ')[0]  # 从列表框条目中获取网站URL部分
            if website_statuses[url]["paused"]:
                website_statuses[url]["paused"] = False  # 设置暂停状态为False
                monitor_website(url)  # 重新开始监控网站
                update_status_in_listbox()  # 更新列表框中的状态显示
                messagebox.showinfo("已恢复监控", f"已恢复监控网站：{url}")

    # 检查网站状态的函数
    def check_website(url):
        try:
            response = requests.get(url, timeout=10)  # 设置超时时间为10秒
            # 检查响应状态码
            if response.status_code == 200:
                return True, "正常 ✅"
            else:
                return False, f"异常（状态码：{response.status_code}）"
        except requests.exceptions.RequestException as e:
            return False, f"无法访问 ({str(e)})"  # 输出异常信息

    # 更新列表框中的状态信息的函数
    def update_status_in_listbox():
        nonlocal listbox
        for url, status_info in website_statuses.items():
            index = website_index_map.get(url)
            if index is not None:
                current_text = listbox.get(index)
                if status_info["paused"]:
                    if not current_text.endswith(" - 暂停监控"):
                        listbox.delete(index)
                        listbox.insert(index, f"{url} - 暂停监控")
                elif not status_info["running"]:
                    if not current_text.endswith(" - 停止监控"):
                        listbox.delete(index)
                        listbox.insert(index, f"{url} - 停止监控")
                else:
                    if not current_text.endswith(f" - {status_info['status']}"):
                        listbox.delete(index)
                        listbox.insert(index, f"{url} - {status_info['status']}")

    # 监控单个网站URL状态的函数
    def monitor_website(url):
        def monitor_single_website():
            while True:
                if not website_statuses[url]["running"]:
                    time.sleep(1)
                    continue

                if website_statuses[url]["paused"]:
                    time.sleep(1)
                    continue

                current_status, status_text = check_website(url)
                previous_status = website_statuses[url]["status"]

                if current_status != previous_status:
                    website_statuses[url]["status"] = status_text
                    notify_status_change(url)  # 调用通知函数

                time.sleep(60)  # 每60秒检查一次

        threading.Thread(target=monitor_single_website).start()

    # 通知状态变化的函数
    def notify_status_change(url):
        # 构建通知的消息内容
        message = f"网站状态更新：{url} - {website_statuses[url]['status']}"

        toaster.show_toast("网站状态更新", message, duration=10)

    # 创建主窗口
    root = tk.Tk()
    root.title("网站状态监控")

    center_label_frame = tk.Frame(root)
    center_label_frame.pack()

    # 标签、输入框和按钮用于输入网站URL
    url_label = tk.Label(root, text="请输入需网站链接:")
    url_label.pack(pady=10)

    url_entry = tk.Entry(root, width=50)
    url_entry.pack(pady=5)

    add_button = tk.Button(root, text="添加网站", command=add_website)
    add_button.pack(pady=5)

    # remove_button = tk.Button(root, text="删除选中网站", command=remove_website)
    # remove_button.pack(pady=5)

    # 标签和列表框用于显示监控的网站URL及其状态
    list_label = tk.Label(root, text="继续监控的网站:")
    list_label.pack()

    listbox = tk.Listbox(root, width=70, height=10)
    listbox.pack(pady=5)

    # 初始化每个网站的状态为"未知状态"，并开始监控已保存的网站URL
    load_and_monitor_website_urls()

    # 调用函数更新列表框中的状态信息
    update_status_in_listbox()

    # 创建右键菜单
    def popup_menu(event):
        context_menu.post(event.x_root, event.y_root)

    context_menu = Menu(root, tearoff=0)
    context_menu.add_command(label="暂停监控", command=pause_website)
    context_menu.add_command(label="继续监控", command=resume_website)
    context_menu.add_separator()
    context_menu.add_command(label="删除选中网站", command=remove_website)

    # 绑定右击事件到列表框
    listbox.bind("<Button-3>", popup_menu)

    root.mainloop()

# 脚本的入口点
if __name__ == "__main__":
    check_dependencies_and_start()  # 检查依赖项并在安装完成后启动主程序
