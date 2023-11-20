import serial
import re
import toml
import sys
import getopt


def read_ip_from_serial(port_name):
    try:
        # 打开串口
        ser = serial.Serial(port_name, baudrate=2000000, timeout=0.5)
        # print(f"打开串口 {port_name} 成功")

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

def main(num_ports):
    # 串口名称列表，可以根据你的实际情况修改
    serial_ports = []

    for i in range(num_ports):
        port = "/dev/ttyUSB" + str(i)
        serial_ports.append(port)

    print("串口个数:", len(serial_ports))

    all_ips = []

    print("开始读取IP地址...")
    for port in serial_ports:
        ips = read_ip_from_serial(port)
        # 若读取ip不是192.168开头，则重新读取

        # 检查列表是否为空
        if not ips:
            print("读取IP为空，重新读取...")
            ips = read_ip_from_serial(port)

        if not ips[0].startswith("192.168"):
            print("读取IP地址失败，重新读取...")
            ips = read_ip_from_serial(port)

        print("port:   ip: ", port, ips)
        all_ips.extend(ips)

    print("匹配到的设备个数:", len(all_ips))
    print("匹配到的所有IP地址:", all_ips)

    # 保存 IP 地址到 ip.toml 文件中
    with open("ip.toml", "w") as f:
        toml.dump({"ips": all_ips}, f)

if __name__ == "__main__":
    num_ports = 0

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "n:",
            [
                "num_ports=",
            ],
        )
    except getopt.GetoptError:
        print(
            "Usage: python script.py -n <num_ports>"
        )
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-n", "--num_ports"):
            num_ports = int(arg)

    if num_ports <= 0:
        print(
            "Invalid arguments. Usage: python script.py -n <num_ports>"
        )
        sys.exit(2)

    main(num_ports)
