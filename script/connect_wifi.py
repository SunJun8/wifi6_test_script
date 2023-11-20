import serial
import re
import time
import toml
import sys
import getopt
import os

def connect_wifi(port_name, ssid, passwd):
    try:
        # 打开串口
        ser = serial.Serial(port_name, baudrate=2000000, timeout=0.5)
        # print(f"打开串口 {port_name} 成功")

        # 发送重启指令
        # ser.write(b"reboot\n")

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

def set_wifi_mode(port_name, mode):
    try:
        # 打开串口
        ser = serial.Serial(port_name, baudrate=2000000, timeout=0.5)
        print(f"打开串口 {port_name} 成功, 设置WiFi模式 {mode}")

        ser.write(b"wifi_sta_disconnect\n")
        time.sleep(0.2)

        # 发送set_mode指令
        # ser.write(b'wifi_set_mode ' + str(mode).encode() + b'\n')

        # 等待set_mode完成
        time.sleep(0.1)

        # 打开自动重连
        ser.write(b"wifi_sta_autoconnect_enable\n")

        time.sleep(0.1)

        # 关闭串口
        ser.close()

    except Exception as e:
        print(f"打开串口 {port_name} 失败：{e}")

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

def main(num_ports, target_ssid, target_passwd, mode):
    # 串口名称列表，可以根据你的实际情况修改
    serial_ports = []

    for i in range(num_ports):
        port = "/dev/ttyUSB" + str(i)
        serial_ports.append(port)
    print(serial_ports)

    if os.path.exists("ip.toml"):
        print("存在 ip.toml 文件, 如果需要重新获取 IP 地址，请删除 ip.toml 文件")
        sys.exit(2)

    all_ips = []

    for port in serial_ports:
        set_wifi_mode(port, mode)

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
            if not ips[0].startswith("192.168"):
                print("读取IP地址失败，重新读取...")
                ips = read_ip_from_serial(port)

            print("读取到IP地址:", ips)
            all_ips.extend(ips)

        print("匹配到的设备个数:", len(all_ips))
        print("匹配到的所有IP地址:", all_ips)

        # 保存 IP 地址到 ip.toml 文件中
        with open("ip.toml", "w") as f:
            toml.dump({"ips": all_ips}, f)

if __name__ == "__main__":
    num_ports = 0
    target_ssid = "bl_test_242"
    mode = 0
    target_passwd = ""

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "n:m:s:k:",
            [
                "num_ports=",
                "mode=",
                "target_ssid=",
                "target_passwd=",
            ],
        )
    except getopt.GetoptError:
        print(
            "Usage: python script.py -n <num_ports> -m <mode> -s <target_ssid> -k <target_passwd>"
        )
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-n", "--num_ports"):
            num_ports = int(arg)
        elif opt in ("-s", "--target_ssid"):
            target_ssid = arg
        elif opt in ("-k", "--target_passwd"):
            target_passwd = arg
        elif opt in ("-p", "--target_port"):
            target_port = int(arg)
        elif opt in ("-m", "--mode"):
            mode = int(arg)

    if num_ports <= 0:
        print(
            "Invalid arguments. Usage: python script.py -n <num_ports> -m <mode> -s <target_ssid> -k <target_passwd>"
        )
        sys.exit(2)

    main(num_ports, target_ssid, target_passwd, mode)
