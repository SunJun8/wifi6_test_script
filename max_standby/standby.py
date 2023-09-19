import socket
import struct
import getopt
import sys


def send_command(module_ip, module_port, cmd_type, cmd_mode, cmd_time, cmd_len, cmd_port, cmd_band):
    print(f"Sending command to {module_ip}:{module_port} mode: {cmd_mode} time: {cmd_time} len: {cmd_len} port: {cmd_port} band: {cmd_band}")

    # 创建UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 构造命令数据包
    header = 0xa55a
    command = struct.pack(">HBBIBHHI", header, cmd_type, cmd_mode, cmd_time, cmd_len, cmd_port, cmd_len, cmd_band)

    try:
        # 发送命令到模组
        sock.sendto(command, (module_ip, module_port))
        print("Command sent successfully.")
    except Exception as e:
        print(f"Error sending command: {str(e)}")

    # 关闭socket
    sock.close()


def main(argv):
    module_ip = "192.168.31.183"
    module_port = 5011
    cmd_type = 0  # 0: udp, 1: tcp
    cmd_mode = 1  # 0: server, 1: client
    cmd_time = 10  # 0: forever, >0: time in seconds
    cmd_len = 0  # optional, 0: max length
    cmd_port = 5005  # 0: error, >0: iperf port
    cmd_band = 1  # 0: not, set: bandwidth in Mbits/sec

    try:
        opts, args = getopt.getopt(argv, "i:p:t:m:d:l:o:b:", ["ip=", "port=", "type=", "mode=", "time=", "len=", "port=", "band="])
    except getopt.GetoptError:
        print("Usage: send_command.py -i <module_ip> -p <module_port> -t <cmd_type> -m <cmd_mode> -d <cmd_time> -l <cmd_len> -o <cmd_port> -b <cmd_band>")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-i", "--ip"):
            module_ip = arg
        elif opt in ("-p", "--port"):
            module_port = int(arg)
        elif opt in ("-t", "--type"):
            cmd_type = int(arg)
        elif opt in ("-m", "--mode"):
            cmd_mode = int(arg)
        elif opt in ("-d", "--time"):
            cmd_time = int(arg)
        elif opt in ("-l", "--len"):
            cmd_len = int(arg)
        elif opt in ("-o", "--port"):
            cmd_port = int(arg)
        elif opt in ("-b", "--band"):
            cmd_band = int(arg)

    if not module_ip or module_port <= 0:
        print("Invalid command line options.")
        sys.exit(2)


    # 调用发送命令函数
    send_command(module_ip, module_port, cmd_type, cmd_mode, cmd_time, cmd_len, cmd_port, cmd_band)


if __name__ == "__main__":
    main(sys.argv[1:])
