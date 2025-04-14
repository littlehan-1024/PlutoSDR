import matplotlib.pyplot as plt
import time
from scipy import signal
import threading
import queue
import sys
import numpy as np


import Start_GUI
import Rx_SDR
import Tx_SDR
import Fm_decoder

# 全局变量，用于保存SDR实例和配置状态
sdr = None
config_ready_event = threading.Event()
iq_file_handle = None  # 用于保存实时接收到的IQ数据
record_iq = None       # 将在GUI中创建的复选框变量

# off-line debug mode下手动配置sdr类
class ad9364:
   """AD9364 Transceiver"""

   def __init__(self):
       self._complex_data = True
       self._rx_channel_names = ["voltage0", "voltage1"]
       self._tx_channel_names = ["voltage0", "voltage1"]
       self._control_device_name = "ad9361-phy"
       self._rx_data_device_name = "cf-ad9361-lpc"
       self._tx_data_device_name = "cf-ad9361-dds-core-lpc"
       self._device_name = ""
       self.rx_rf_bandwidth = None
       self.sample_rate = None
       self.rx_lo = None
       self.tx_lo = None
       self.tx_cyclic_buffer = None
       self.tx_hardwaregain_chan0 = None
       self.gain_control_mode_chan0 = None
       self.rx_enabled_channels = []
       self.tx_enabled_channels = []

def update_sdr_config(updated_sdr, updated_record_iq):
    """ 从 Start_GUI 传递配置后的 SDR 和 record_iq 变量 """
    global sdr, record_iq
    sdr = updated_sdr
    record_iq = updated_record_iq

def plot_data(data_queue):
    plt.ion()  # 开启交互模式
    while True:
        if not data_queue.empty():
            x = data_queue.get()
            global sdr
            if sdr is None:
                continue
            f, Pxx_den = signal.periodogram(x, sdr.sample_rate)
            plt.clf()
            plt.semilogy(f, Pxx_den)
            plt.ylim([1e-7, 1e2])
            plt.xlabel("Frequency [Hz]")
            plt.ylabel("PSD [V**2/Hz]")
            plt.draw()
            plt.pause(0.05)
        time.sleep(0.1)

def gen_qpsk_iq_file():
    # 参数设置
    fs = 6.4e6  # 采样率 6.4 MHz
    bw = 300e3  # 带宽 300 kHz
    duration = 10  # 采样时长 10s
    num_samples = int(fs * duration)  # 总采样点数

    # 生成 QPSK 信号
    symbols = np.array([1 + 1j, 1 - 1j, -1 + 1j, -1 - 1j])  # QPSK 符号集合
    bits = np.random.randint(0, 4, num_samples)  # 生成随机符号索引
    iq_signal = symbols[bits]  # 映射到 IQ 符号

    # 归一化并转换为 float32 格式
    iq_signal = iq_signal / np.sqrt(2)  # 归一化到单位功率
    iq_interleaved = np.column_stack((iq_signal.real, iq_signal.imag)).ravel().astype(np.float32)  # 交织 I/Q 数据

    # 保存到文件
    file_path = "./Resource/6400kHz_300kHz_10s.float32"
    iq_interleaved.tofile(file_path)

    print(f"文件已保存：{file_path}")


if __name__ == '__main__':
    # 创建用于在线程间传递数据的队列
    data_queue = queue.Queue()
    # ChatGPT 创建本地QPSK 12bits Fs=6.4e6 BW=300e3 IQ file
    gen_thread = threading.Thread(target=gen_qpsk_iq_file,daemon=True)
    gen_thread.start()
    # ChatGPT 本地调试FM相干解调器
    fm_tread = threading.Thread(target=Fm_decoder.fm_decoder,daemon=True)
    fm_tread.start()
    # 启动GUI线程（独立运行，不干扰主线程及其他子线程）
    gui_thread = threading.Thread(target=Start_GUI.start_gui, args=(config_ready_event, update_sdr_config), daemon=True)
    gui_thread.start()

    # 主线程等待GUI中完成SDR配置
    print("等待用户在GUI中配置SDR设备...")
    config_ready_event.wait()
    print("配置已完成，启动其他子线程。")

    # 启动TX发送线程
    tx_thread = threading.Thread(target=Tx_SDR.prepare_and_send_tx_iq_data, args=(sdr,))
    tx_thread.start()

    # 启动RX接收线程
    rx_thread = threading.Thread(target=Rx_SDR.rx_from_sdr, args=(sdr, data_queue, record_iq, iq_file_handle,))
    rx_thread.start()

    # 启动实时绘图线程
    plot_thread = threading.Thread(target=plot_data, args=(data_queue,))
    plot_thread.start()

    # 监控 GUI 线程状态
    while gui_thread.is_alive():
        gui_thread.join(timeout=0.5)  # 每 0.5 秒检查一次 GUI 线程状态

    print("GUI 线程已退出，主程序即将退出...")
    sys.exit(1)  # 返回值 1，表示 GUI 线程已退出
    # 等待TX和RX线程结束（绘图线程为无限循环，根据需要调整终止方式）
    tx_thread.join()
    rx_thread.join()
    plot_thread.join()

