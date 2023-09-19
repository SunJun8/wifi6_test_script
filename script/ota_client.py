import sys
import socket
import getopt
import serial
import time
import re


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
        time.sleep(10)

        print("文件发送完成, ip:", server_ip)

    except ConnectionRefusedError:
        print("无法连接到服务器.")
    finally:
        # 关闭socket连接
        client_socket.close()

def start_ota_server(port_name):
    try:
        # 打开串口
        ser = serial.Serial(port_name, baudrate=2000000, timeout=1)
        print(f"打开串口 {port_name} 成功, 启动OTA Server")

        # 发送重启指令
        ser.write(b'ota_tcp_server\n')

        # 等待重启完成
        time.sleep(1)

        # 关闭串口
        ser.close()

    except Exception as e:
        print(f"打开串口 {port_name} 失败：{e}")


def read_ip_from_serial(port_name):
    try:
        # 打开串口
        ser = serial.Serial(port_name, baudrate=2000000, timeout=1)
        print(f"打开串口 {port_name} 成功")

        # 发送字符串并读取数据
        ser.write(b'wifi_sta_info\n')
        response = ser.read(500).decode('utf-8')

        # 使用正则表达式匹配IP地址
        ip_regex = r'IP\s+:\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        ip_addresses = re.findall(ip_regex, response)

        # 关闭串口
        ser.close()

        return ip_addresses

    except Exception as e:
        print(f"读取串口 {port_name} 失败：{e}")
        return []


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
    print(serial_ports)

    # 或者IP地址列表
    all_ips = []
    print("开始读取IP地址...")
    for uart_port in serial_ports:
        ips = read_ip_from_serial(uart_port)
        all_ips.extend(ips)
    print("匹配到的所有IP地址:", all_ips)

    # 启动TCP OTA Server
    for port in serial_ports:
        start_ota_server(port)

    # 发送文件到所有IP地址
    if file_path and server_port:
        for ip in all_ips:
            print(f"正在发送文件到 {ip}...")
            send_file_to_tcp_server(file_path, ip, server_port)
    else:
        print("请提供文件名、服务器IP和目标端口.")
        print("Usage: python script.py -f <file_path> -p <server_port> -n <num_ports>")
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
