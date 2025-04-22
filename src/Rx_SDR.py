import time
import numpy as np
import os


def rx_from_sdr(sdr, data_queue, record_iq, iq_file_handle):
    # 接收20次数据（后续可扩展为持续接收）
    for r in range(20):
        x = sdr.rx()
        data_queue.put(x)
        # 若“记录IQ数据”被选中，则保存数据到文件
        if record_iq is not None:
            if iq_file_handle is None:
                # 根据当前SDR配置构建文件名：rx_lo_rx_rf_bandwidth_sample_rate_mmdd.float32
                rx_lo = sdr.rx_lo
                rx_rf_bandwidth = sdr.rx_rf_bandwidth
                sample_rate = sdr.sample_rate
                date_str = time.strftime("%m%d")
                file_name = f"{rx_lo}_{rx_rf_bandwidth}_{sample_rate}_{date_str}.float32"
                save_dir = "saved_data"
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                file_path = os.path.join(save_dir, file_name)
                iq_file_handle = open(file_path, "wb")
                print(f"开始保存IQ数据到文件：{file_path}")
            # 将x转换为complex64（对应float32的I/Q数据），并交错存储
            iq_data = x.astype(np.complex64)
            interleaved = np.empty(iq_data.size * 2, dtype=np.float32)
            interleaved[0::2] = np.real(iq_data)
            interleaved[1::2] = np.imag(iq_data)
            iq_file_handle.write(interleaved.tobytes())
    # 结束后关闭文件（若已打开）
    if iq_file_handle is not None:
        iq_file_handle.close()
        print("IQ数据保存完毕。")

    return
