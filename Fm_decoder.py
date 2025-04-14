import numpy as np
import scipy.signal as signal
# import sounddevice as sd
import matplotlib.pyplot as plt
import time


def generate_fm_signal(fs=44100, duration=5, f_carrier=5000, f_mod=300, deviation=500):
    """ 生成随机音频信号并进行 FM 调制 """
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    audio_signal = np.random.uniform(-1, 1, len(t))  # 生成随机音频信号
    integral_audio = np.cumsum(audio_signal) / fs  # 计算音频信号的积分
    fm_signal = np.cos(2 * np.pi * f_carrier * t + 2 * np.pi * deviation * integral_audio)
    return t, fm_signal, audio_signal

def pll_fm_demodulate(fm_signal, fs, f_carrier):
    """ 使用锁相环 (PLL) 进行 FM 信号解调 """
    dt = 1 / fs
    N = len(fm_signal)

    # 初始化 PLL 变量
    phase_est = 0
    freq_est = f_carrier
    demodulated = np.zeros(N)
    phase_error = 0
    loop_filter = 0
    loop_gain = 0.01
    integrator = 0
    integrator_gain = 0.1

    for i in range(1, N):
        ref_signal = np.cos(phase_est)  # 生成本地参考信号
        phase_error = fm_signal[i] * ref_signal  # 相位误差计算
        loop_filter = loop_filter + loop_gain * phase_error  # 低通滤波器
        freq_est = f_carrier + loop_filter  # 频率估计
        phase_est = phase_est + 2 * np.pi * freq_est * dt  # 相位更新
        integrator = integrator + integrator_gain * phase_error  # 误差积分
        demodulated[i] = integrator  # 输出解调信号

    return demodulated

def noncoherent_fm_demodulate(fm_signal, fs):
    """ 非相干 FM 解调（基于相位差分法）"""
    analytic_signal = signal.hilbert(fm_signal)  # 计算解析信号
    phase = np.unwrap(np.angle(analytic_signal))  # 计算相位并展开
    demodulated = np.diff(phase) * fs / (2 * np.pi)  # 相位微分得到频偏
    demodulated = np.insert(demodulated, 0, demodulated[0])  # 维持长度一致
    return demodulated

def fm_decoder():
    fs = 44100  # 采样率
    duration = 5  # 信号时长（秒）
    f_carrier = 5000  # 载波频率

    # 生成 FM 信号
    t, fm_signal, original_audio = generate_fm_signal(fs, duration, f_carrier)

    # 进行 PLL 相干解调
    start_time = time.time()
    pll_demodulated_audio = pll_fm_demodulate(fm_signal, fs, f_carrier)
    pll_time = time.time() - start_time

    # 进行非相干解调
    start_time = time.time()
    noncoherent_demodulated_audio = noncoherent_fm_demodulate(fm_signal, fs)
    noncoherent_time = time.time() - start_time

    # 归一化音频信号，防止失真
    pll_demodulated_audio /= np.max(np.abs(pll_demodulated_audio))
    noncoherent_demodulated_audio /= np.max(np.abs(noncoherent_demodulated_audio))

    # 输出解调时间
    print(f"PLL 相干解调时间: {pll_time:.6f} 秒")
    print(f"非相干解调时间: {noncoherent_time:.6f} 秒")

    # 绘制信号对比
    plt.figure(figsize=(10, 8))
    plt.subplot(4, 1, 1)
    plt.plot(t, original_audio, label='Original Audio Signal')
    plt.legend()

    plt.subplot(4, 1, 2)
    plt.plot(t, fm_signal, label='FM Signal')
    plt.legend()

    plt.subplot(4, 1, 3)
    plt.plot(t, pll_demodulated_audio, label='PLL Demodulated Audio (Coherent)')
    plt.legend()

    plt.subplot(4, 1, 4)
    plt.plot(t, noncoherent_demodulated_audio, label='Noncoherent Demodulated Audio')
    plt.legend()

    plt.xlabel('Time [s]')
    plt.show()

