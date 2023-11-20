import sys
import socket
import getopt
import serial
import time
import re
import os
import toml


def send_file_to_tcp_server(file_path, server_ip, server_port):
    with open(file_path, 'rb') as file:
        file_data = file.read()

    # 创建TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到服务器
        client_socket.connect((server_ip, server_port))

        # 发送文件内容
        client_socket.sendall(file_data)

        # 等待服务器确认接收完成
        time.sleep(1)

        print("文件发送完成, ip:", server_ip)

    except ConnectionRefusedError:
        print("无法连接到服务器. ip:", server_ip)
    finally:
        # 关闭socket连接
        client_socket.close()

def start_ota_server(port_name):
    try:
        # 打开串口
        ser = serial.Serial(port_name, baudrate=2000000, timeout=0.5)
        print(f"打开串口 {port_name} 成功, 启动OTA Server")

        # 发送OTA Server指令
        ser.write(b'ota_tcp_server\n')

        # 等待OTA Server启动完成
        time.sleep(0.1)

        # 关闭串口
        ser.close()

    except Exception as e:
        print(f"打开串口 {port_name} 失败：{e}")

def main(argv):
    file_path = ""
    server_ip = ""
    server_port = 0
    serial_num = 0
    serial_ports = []

    try:
        opts, args = getopt.getopt(argv, "f:i:p:n:", ["file=", "ip=", "port=", "serial="])
    except getopt.GetoptError:
        print("Usage: python script.py -f <file_path> -i <server_ip> -p <server_port> -n <num_ports>")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-f", "--file"):
            file_path = arg
        elif opt in ("-i", "--ip"):
            server_ip = arg
        elif opt in ("-p", "--port"):
            server_port = int(arg)
        elif opt in ("-n", "--serial"):
            serial_num = int(arg)

    for i in range(serial_num):
        uart_port = "/dev/ttyUSB" + str(i)
        serial_ports.append(uart_port)

    print("串口个数:", len(serial_ports))

    # 或者IP地址列表
    all_ips = []

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

    print("匹配到的设备个数:", len(all_ips))
    print("匹配到的所有IP地址:", all_ips)

    # 启动TCP OTA Server
    for port in serial_ports:
        start_ota_server(port)

    time.sleep(2)

    # 发送文件到所有IP地址
    if file_path and server_port:
        import threading
        threads = []

        for ip in all_ips:
            print(f"正在发送文件到 {ip}...")
            # send_file_to_tcp_server(file_path, ip, server_port)
            thread = threading.Thread(target=send_file_to_tcp_server, args=(file_path, ip, server_port))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    else:
        print("请提供文件名、服务器IP和目标端口.")
        print("Usage: python script.py -f <file_path> -p <server_port> -n <num_ports>")
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
