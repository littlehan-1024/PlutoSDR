def config_sdr(sdr, params):
    # 仅在设备地址存在时进行配置
    if not params.get("device_address"):
        print("设备地址为空，配置中止。")
        return
    try:
        sdr.rx_rf_bandwidth = int(params.get("rx_rf_bandwidth"))
        sdr.sample_rate = int(params.get("sample_rate"))
        sdr.rx_lo = int(params.get("rx_lo"))
        sdr.tx_lo = int(params.get("tx_lo"))
        # 将字符串形式的布尔值转换为布尔型
        tx_cyclic_buffer_val = params.get("tx_cyclic_buffer", "True")
        if isinstance(tx_cyclic_buffer_val, str):
            sdr.tx_cyclic_buffer = bool(tx_cyclic_buffer_val.lower() == "true")
        else:
            sdr.tx_cyclic_buffer = bool(tx_cyclic_buffer_val)
        sdr.tx_hardwaregain_chan0 = int(params.get("tx_hardwaregain_chan0"))
        sdr.gain_control_mode_chan0 = params.get("gain_control_mode_chan0")
        # 对通道参数，假定用户输入为逗号分隔的整数字符串
        rx_channels = params.get("rx_enabled_channels")
        tx_channels = params.get("tx_enabled_channels")
        sdr.rx_enabled_channels = [int(ch.strip()) for ch in rx_channels.split(",") if ch.strip().isdigit()]
        sdr.tx_enabled_channels = [int(ch.strip()) for ch in tx_channels.split(",") if ch.strip().isdigit()]
        print("SDR配置成功, RX LO: %s" % sdr.rx_lo)
    except Exception as e:
        print("配置SDR时出错:", e)
    return

