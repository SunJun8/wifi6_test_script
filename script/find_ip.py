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
import struct
import fcntl


def connect_wifi(port_name, ssid, passwd):
    try:
        # 打开串口
        ser = serial.Serial(port_name, baudrate=2000000, timeout=1)
        print(f"打开串口 {port_name} 成功")

        # 发送重启指令
        ser.write(b"reboot\n")
        # ser.setRTS(False)

        # 等待重启完成
        time.sleep(1)

        # 打开自动重连
        ser.write(b"wifi_sta_autoconnect_enable\n")

        time.sleep(0.2)

        # 发送字符串并读取数据
        if passwd == "":
            ser.write(b"wifi_sta_connect " + ssid.encode() + b"\n")
        else:
            ser.write(
                b"wifi_sta_connect " + ssid.encode() + b" " + passwd.encode() + b"\n"
            )

        # 关闭串口
        ser.close()

    except Exception as e:
        print(f"读取串口 {port_name} 失败：{e}")
        return []


def get_ip_address(ifname):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip_address = socket.inet_ntoa(
            fcntl.ioctl(
                sock.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack("256s", ifname[:15].encode("utf-8")),
            )[20:24]
        )
        return ip_address
    except Exception as e:
        print("获取IP地址失败:", e)
        return None


def read_ip_from_serial(port_name):
    try:
        # 打开串口
        ser = serial.Serial(port_name, baudrate=2000000, timeout=0.5)
        print(f"打开串口 {port_name} 成功")

        # 发送字符串并读取数据
        ser.write(b"wifi_sta_info\n")
        response = ser.read(500).decode("utf-8")

        # 使用正则表达式匹配IP地址
        ip_regex = r"IP\s+:\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        ip_addresses = re.findall(ip_regex, response)

        # 关闭串口
        ser.close()

        return ip_addresses

    except Exception as e:
        print(f"读取串口 {port_name} 失败：{e}")
        return []


def read_tsf_from_serial(port_name):
    try:
        # 打开串口
        ser = serial.Serial(port_name, baudrate=2000000, timeout=0.2)
        print(f"打开串口 {port_name} 成功")

        # 发送字符串并读取数据
        ser.write(b"get_tsf\n")
        response = ser.read(500).decode("utf-8")

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


def main(num_ports, num_cycles, target_ssid, target_passwd, remote_port):
    # 串口名称列表，可以根据你的实际情况修改
    serial_ports = []

    if remote_port == 0:
        target_port = 5010
    else:
        target_port = remote_port

    for i in range(num_ports):
        port = "/dev/ttyUSB" + str(i)
        serial_ports.append(port)
    print(serial_ports)

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
    else:
        all_ips = []

    if not all_ips:
        print("开始连接WiFi...")
        for port in serial_ports:
            connect_wifi(port, target_ssid, target_passwd)

        print("等待连接成功...5s")
        time.sleep(5)

        print("开始读取IP地址...")
        for port in serial_ports:
            ips = read_ip_from_serial(port)
            # 若读取ip不是192.168开头，则重新读取
            if ips[0].startswith("192.168"):
                print("读取到IP地址:", ips)
                ips = read_ip_from_serial(port)

            all_ips.extend(ips)

        print("匹配到的所有IP地址:", all_ips)

        # 保存 IP 地址到 ip.toml 文件中
        with open("ip.toml", "w") as f:
            toml.dump({"ips": all_ips}, f)

    time.sleep(2)

    # exit()

    all_tsf_values = []  # 用于存储所有测试的 TSF 值

    for cycle in range(1, num_cycles + 1):
        print(f"\n=== 第 {cycle} 次循环测试 ===")

        tsf_values = []

        for i in range(num_ports):
            send_udp_packet(all_ips, target_port, "Hello, world!")

        time.sleep(1)

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
    target_ssid = "bl_test_242"
    target_passwd = ""
    target_port = 5010

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "n:c:s:k:p:",
            [
                "num_ports=",
                "num_cycles=",
                "target_ssid=",
                "target_passwd=",
                "target_port=",
            ],
        )
    except getopt.GetoptError:
        print(
            "Usage: python script.py -n <num_ports> -c <num_cycles> -s <target_ssid> -k <target_passwd> -p <target_port>"
        )
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-n", "--num_ports"):
            num_ports = int(arg)
        elif opt in ("-c", "--num_cycles"):
            num_cycles = int(arg)
        elif opt in ("-s", "--target_ssid"):
            target_ssid = arg
        elif opt in ("-k", "--target_passwd"):
            target_passwd = arg
        elif opt in ("-p", "--target_port"):
            target_port = int(arg)

    if num_ports <= 0 or num_cycles <= 0:
        print(
            "Invalid arguments. Usage: python script.py -n <num_ports> -c <num_cycles> -s <target_ssid>"
        )
        sys.exit(2)

    main(num_ports, num_cycles, target_ssid, target_passwd, target_port)
