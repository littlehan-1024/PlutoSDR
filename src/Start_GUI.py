import numpy as np
import os
import adi
import tkinter as tk
from tkinter import ttk, filedialog
import sys
import matplotlib.pyplot as plt
from scipy import signal

import main
import config


def start_gui(config_ready_event, update_callback):
    global record_iq
    root = tk.Tk()
    root.title("SDR 配置界面")

    # 设置窗口自适应大小
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # 创建菜单栏
    menu_bar = tk.Menu(root)

    # “实时回放”菜单
    real_time_menu = tk.Menu(menu_bar, tearoff=0)
    real_time_menu.add_command(label="实时回放", command=lambda: root.deiconify())

    # “离线回放”菜单
    offline_menu = tk.Menu(menu_bar, tearoff=0)
    offline_menu.add_command(label="离线回放", command=offline_replay_window)

    # “退出”菜单
    def exit_program():
        print("退出程序...")
        sys.exit(1)  # 直接终止整个 Python 进程

    exit_menu = tk.Menu(menu_bar, tearoff=0)
    exit_menu.add_command(label="退出", command=exit_program)

    menu_bar.add_cascade(label="实时回放", menu=real_time_menu)
    menu_bar.add_cascade(label="离线回放", menu=offline_menu)
    menu_bar.add_cascade(label="退出", menu=exit_menu)

    root.config(menu=menu_bar)

    main_frame = ttk.Frame(root, padding="10")
    main_frame.grid(sticky=(tk.N, tk.S, tk.E, tk.W))
    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)

    # SDR类型下拉菜单
    ttk.Label(main_frame, text="SDR 类型:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    sdr_type_var = tk.StringVar(value="adi.Pluto")
    sdr_type_dropdown = ttk.OptionMenu(main_frame, sdr_type_var, "adi.Pluto", "adi.Pluto", "adi.ad9364")
    sdr_type_dropdown.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

    # 设备地址输入
    ttk.Label(main_frame, text="设备地址:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    device_address_entry = ttk.Entry(main_frame, width=30)
    device_address_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
    device_address_entry.insert(0,'ip:192.168.2.1')

    # "Debug 模式" 复选框
    debug_mode_var = tk.BooleanVar(value=False)  # 默认关闭
    debug_checkbox = ttk.Checkbutton(main_frame, text="Debug 模式", variable=debug_mode_var)
    debug_checkbox.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

    # “记录IQ数据”复选框
    record_iq = tk.BooleanVar(value=False)
    record_chk = ttk.Checkbutton(main_frame, text="记录IQ数据", variable=record_iq)
    record_chk.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)

    # 参数配置输入框
    labels = ["rx_rf_bandwidth", "sample_rate", "rx_lo", "tx_lo", "tx_cyclic_buffer",
              "tx_hardwaregain_chan0", "gain_control_mode_chan0", "rx_enabled_channels", "tx_enabled_channels"]
    default_values = ["2000000", "521000", "101700000", "2400000000", "True", "-30", "slow_attack", "0", "0"]

    entries = {}
    start_row = 4
    for idx, (label_text, default) in enumerate(zip(labels, default_values)):
        row_num = start_row + idx
        ttk.Label(main_frame, text=label_text + ":").grid(row=row_num, column=0, sticky=tk.W, padx=5, pady=5)
        entry = ttk.Entry(main_frame, width=30)
        entry.insert(0, default)
        entry.grid(row=row_num, column=1, sticky=tk.W, padx=5, pady=5)
        entries[label_text] = entry

    button_row = start_row + len(labels)
    # 状态信息标签
    status_label = ttk.Label(main_frame, text="")
    status_label.grid(row=button_row + 1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

    def apply_config():
        device_address = device_address_entry.get().strip()
        if device_address == "":
            status_label.config(text="设备地址为空，请输入有效地址。")
            return

        global sdr
        sdr_type = sdr_type_var.get()
        debug_mode = debug_mode_var.get()  # 获取 Debug 模式状态

        try:
            if debug_mode:  # 进入 Debug 模式
                print("Debug 模式启用，使用 main.ad9364() 进行调试。")
                sdr = main.ad9364()
            else:  # 运行模式
                if device_address.startswith("usb:"):
                    if sdr_type == "adi.Pluto":
                        sdr = adi.Pluto(device_address)
                    elif sdr_type == "adi.ad9364":
                        sdr = adi.ad9364(device_address)
                    else:
                        status_label.config(text="未知的SDR类型。")
                        return
                else :
                    if sdr_type == "adi.Pluto":
                        sdr = adi.Pluto(device_address)
                    elif sdr_type == "adi.ad9364":
                        sdr = adi.ad9364(device_address)
                    else:
                        status_label.config(text="未知的SDR类型。")
                        return
        except Exception as e:
            status_label.config(text=f"创建SDR实例失败: {e}")
            print(f"创建SDR实例失败: {e}")
            return

        # 收集所有参数
        params = {"device_address": device_address}
        for key, entry in entries.items():
            params[key] = entry.get().strip()

        # 输出配置参数到终端
        print("当前配置参数：")
        for key, value in params.items():
            print(f"  {key}: {value}")

        # 配置SDR
        config.config_sdr(sdr, params)
        status_label.config(text="SDR配置成功。")

        # 调用回调函数，将 `sdr` 和 `record_iq` 传回 `main.py`
        update_callback(sdr, record_iq.get())

        # 标记配置已完成，允许其他线程启动
        config_ready_event.set()

    def clear_config():
        device_address_entry.delete(0, tk.END)
        for entry in entries.values():
            entry.delete(0, tk.END)
        status_label.config(text="所有配置已清空。")

    # “配置SDR”按钮
    configure_button = ttk.Button(main_frame, text="配置SDR", command=apply_config)
    configure_button.grid(row=button_row, column=0, pady=10)

    clear_button = ttk.Button(main_frame, text="清空配置", command=clear_config)
    clear_button.grid(row=button_row, column=1, pady=10)

    root.mainloop()

    # 监测配置事件，自动关闭 GUI
    def check_event():
        if config_ready_event.is_set():
            print("SDR 配置完成，退出 GUI 线程...")
            root.quit()  # 关闭 tkinter
        else:
            root.after(100, check_event)  # 每 100ms 检查一次

    root.after(100, check_event)  # 触发定时检查
    root.mainloop()

def offline_replay_window():
    # 新建离线回放窗口
    replay_win = tk.Toplevel()
    replay_win.title("离线回放")
    replay_win.columnconfigure(0, weight=1)
    replay_win.rowconfigure(0, weight=1)

    frm = ttk.Frame(replay_win, padding="10")
    frm.grid(sticky=(tk.N, tk.S, tk.E, tk.W))
    frm.columnconfigure(1, weight=1)

    ttk.Label(frm, text="选择IQ数据文件:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    file_entry = ttk.Entry(frm, width=40)
    file_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

    def browse_file():
        fname = filedialog.askopenfilename(initialdir="saved_data",
                                           title="选择IQ数据文件",
                                           filetypes=[("Float32 files", "*.float32"), ("All files", "*.*")])
        if fname:
            file_entry.delete(0, tk.END)
            file_entry.insert(0, fname)

    browse_btn = ttk.Button(frm, text="浏览", command=browse_file)
    browse_btn.grid(row=0, column=2, padx=5, pady=5)

    # 可选：离线回放窗口中增加采样率输入（若需要使用实际采样率），否则尝试从文件名解析
    ttk.Label(frm, text="采样率 (Hz):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
    fs_entry = ttk.Entry(frm, width=20)
    fs_entry.insert(0, "6.4e6")
    fs_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

    def playback():
        file_path = file_entry.get().strip()
        if not os.path.isfile(file_path):
            tk.messagebox.showerror("错误", "请选择有效的IQ数据文件！")
            return
        try:
            playback_file(file_path, fs_entry.get().strip())
        except Exception as e:
            tk.messagebox.showerror("错误", f"回放失败：{e}")

    play_btn = ttk.Button(frm, text="回放", command=playback)
    play_btn.grid(row=2, column=0, columnspan=3, pady=10)

def playback_file(file_path, fs_str):
    # 读取文件中的IQ数据（float32），并重构为复数数组
    data = np.fromfile(file_path, dtype=np.float32)
    if data.size % 2 != 0:
        raise ValueError("文件数据格式错误，数据个数不是偶数")
    iq = data.reshape(-1, 2)
    iq = iq[:, 0] + 1j * iq[:, 1]

    # 尝试从文件名解析采样率，如失败则使用fs_str
    fs = float(fs_str)
    # base = os.path.basename(file_path)
    # parts = base.split('_')
    # if len(parts) >= 3:
    #     try:
    #         fs = float(parts[2])
    #     except:
    #         fs = None
    # if fs is None:
    #     fs = float(fs_str)

    # 计算频谱图：转换为dBm（注意加上一个极小值防止log(0)）
    f, Pxx_den = signal.periodogram(iq, fs)
    Pxx_dBm = 10 * np.log10(Pxx_den + 1e-12)

    # 计算瀑布图（频谱图随时间变化）
    f2, t2, Sxx = signal.spectrogram(iq, fs)
    Sxx_dB = 10 * np.log10(Sxx + 1e-12)

    # 绘图：四个子图：频谱图、瀑布图、I路波形、Q路波形
    fig, axs = plt.subplots(2, 3, figsize=(12, 8))
    # 频谱图
    axs[0, 0].plot(f, Pxx_dBm)
    axs[0, 0].set_xlabel("Frequency (Hz)")
    axs[0, 0].set_ylabel("Power (dBm)")
    axs[0, 0].set_title("Spectrum")
    # 瀑布图
    im = axs[0, 1].imshow(Sxx_dB, aspect='auto', origin='lower',
                          extent=[t2.min(), t2.max(), f2.min(), f2.max()])
    axs[0, 1].set_xlabel("Time (s)")
    axs[0, 1].set_ylabel("Frequency (Hz)")
    axs[0, 1].set_title("Raindrop")
    fig.colorbar(im, ax=axs[0, 1])
    # I路波形
    axs[1, 0].plot(np.real(iq))
    axs[1, 0].set_xlabel("Sample")
    axs[1, 0].set_ylabel("Amplitude")
    axs[1, 0].set_title("In-Phase")
    # Q路波形
    axs[1, 1].plot(np.imag(iq))
    axs[1, 1].set_xlabel("Sample")
    axs[1, 1].set_ylabel("Amplitude")
    axs[1, 1].set_title("Q-Phase")
    # timedomain波形
    axs[0, 2].plot(iq)
    axs[0, 2].set_xlabel("Frequence")
    axs[0, 2].set_ylabel("Amplitude")
    axs[0, 2].set_title("timedomain")

    plt.tight_layout()
    plt.show()
