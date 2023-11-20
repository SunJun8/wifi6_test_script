import serial
import re
import socket
import asyncio
import time
import os
import toml
import csv
import sys
import getopt

def read_tsf_from_serial(port_name):
    try:
        # 打开串口
        ser = serial.Serial(port_name, baudrate=2000000, timeout=0.2)
        print(f"打开串口 {port_name} 成功")

        # 发送字符串并读取数据
        ser.write(b"get_tsf\n")
        response = ser.read(200).decode("utf-8")

        # 使用正则表达式匹配数字
        match = re.search(r"TSF is (\d+\.\d+) s", response)

        if match:
            tsf_value = float(match.group(1))
            print(tsf_value)
        else:
            print("未找到 TSF 值")

        # 关闭串口
        ser.close()

        return tsf_value

    except Exception as e:
        print(f"读取串口 {port_name} 失败：{e}")
        return []


async def send_to_multiple_ips(ip_addresses, port, message):
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: asyncio.DatagramProtocol(), remote_addr=None, family=socket.AF_INET
    )

    try:
        for ip in ip_addresses:
            transport.sendto(message.encode(), (ip, port))
    finally:
        transport.close()


def send_udp_packet(ip_addresses, port, message):
    # 使用异步编程模型发送数据
    asyncio.run(send_to_multiple_ips(ip_addresses, port, message))


def main(num_ports, num_cycles, remote_port):
    # 串口名称列表，可以根据你的实际情况修改
    serial_ports = []

    if remote_port == 0:
        target_port = 5010
    else:
        target_port = remote_port

    for i in range(num_ports):
        port = "/dev/ttyUSB" + str(i)
        serial_ports.append(port)

    # 检查是否存在 ip.toml 文件
    if os.path.exists("ip.toml"):
        # 读取 ip.toml 文件中保存的 IP 地址
        with open("ip.toml", "r") as f:
            ip_data = toml.load(f)
        saved_ips = ip_data.get("ips", [])
        # 检查保存的 IP 地址是否符合要测试的串口数量
        if len(saved_ips) == len(serial_ports):
            all_ips = saved_ips
        else:
            all_ips = []
            print("ip.toml 文件中保存的 IP 地址数量与要测试的串口数量不一致")
            sys.exit(2)
    else:
        all_ips = []

    if not all_ips:
        print("ip.toml 文件不存在, 先运行get_ip.py或connect_wifi.py获取IP地址")
        sys.exit(2)

    all_tsf_values = []  # 用于存储所有测试的 TSF 值

    for cycle in range(1, num_cycles + 1):
        print(f"\n=== 第 {cycle} 次循环测试 ===")

        tsf_values = []
        if target_port == 5011:
            target_port = 5010

        send_udp_packet(all_ips, target_port, "Hello, world!")

        if target_port == 5010:
            target_port = 5011

        time.sleep(0.5)

        send_udp_packet(all_ips, target_port, "Hello, world!")

        time.sleep(0.5)

        print("开始读取TSF值...")
        for i in range(num_ports):
            tsf_value = read_tsf_from_serial(serial_ports[i])
            if tsf_value is not None:
                tsf_values.append(tsf_value)

        tsf_values.sort()
        all_tsf_values.append(tsf_values)

    # Save all TSF values to the CSV file
    with open("tsf_all_cycles.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Cycle"] + list(range(1, num_ports + 1)))  # 写入表头
        for cycle, tsf_values in enumerate(all_tsf_values, start=1):
            writer.writerow([cycle] + tsf_values)


if __name__ == "__main__":
    num_ports = 0
    num_cycles = 0
    target_port = 5010

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "n:c:p:",
            [
                "num_ports=",
                "num_cycles=",
                "target_port=",
            ],
        )
    except getopt.GetoptError:
        print(
            "Usage: python script.py -n <num_ports> -c <num_cycles> -p <target_port>"
        )
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-n", "--num_ports"):
            num_ports = int(arg)
        elif opt in ("-c", "--num_cycles"):
            num_cycles = int(arg)
        elif opt in ("-p", "--target_port"):
            target_port = int(arg)

    if num_ports <= 0 or num_cycles <= 0:
        print(
            "Invalid arguments. Usage: python script.py -n <num_ports> -c <num_cycles> -p <target_port>"
        )
        sys.exit(2)

    main(num_ports, num_cycles, target_port)
