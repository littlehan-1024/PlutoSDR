import numpy as np


def prepare_and_send_tx_iq_data(sdr):
    fs = int(sdr.sample_rate)
    N = 1024
    fc = 1e6  # 1 MHz
    ts = 1 / float(fs)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * 2 ** 14
    q = np.sin(2 * np.pi * t * fc) * 2 ** 14
    iq = i + 1j * q
    sdr.tx(iq)
