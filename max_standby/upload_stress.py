import os
import time
import socket
import pandas as pd

# check if ip.toml file exists in current directory
if not os.path.exists("ip.toml"):
    # if it doesn't exist, execute 'python get_local_ip.py ip.toml' to get current ip list
    os.system("python get_local_ip.py ip.toml")

# read ip list from ip.toml file
with open("ip.toml", "r") as f:
    ip_list = f.read().splitlines()

# calculate initial delay based on number of IPs in ip_list
num_ips = len(ip_list)
delay_step = 100
initial_delay = num_ips * delay_step   # 100ms per IP
duration = 30   # 30 seconds

# set initial delay
delay = initial_delay
for ip in ip_list:
    os.system(f"python standby.py -i {ip} -p 50201 -m 0 -o 44333 -b 4 -d {duration} -l {delay}")
    delay -= delay_step
    time.sleep(delay_step / 1000)


# 设置UDP服务器地址和端口
UDP_IP = "0.0.0.0"  # 监听所有网络接口
UDP_PORT = 44333

# 创建UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# 初始化字典用于跟踪不同源IP的数据量
source_ip_data = {}
total_bytes_received = 0  # 用于计算总带宽的字节数
final_bytes_received = 0  # 用于计算总带宽的字节数

# 创建一个DataFrame用于存储带宽数据
columns = ["Time (s)"]  # 第一列是时间
df = pd.DataFrame(columns=columns)

start_time = time.time()
current_time = start_time
tick = start_time

while True:
    try:
        # 接收UDP数据包
        data, addr = sock.recvfrom(1472)
        # 获取源IP地址
        source_ip = addr[0]
        # 计算接收的字节数
        received_bytes = len(data)

        # 更新源IP的数据量
        if source_ip in source_ip_data:
            source_ip_data[source_ip] += received_bytes
        else:
            source_ip_data[source_ip] = received_bytes

        # 累积总字节数
        total_bytes_received += received_bytes
        final_bytes_received += received_bytes

        # 计算时间差，以秒为单位
        elapsed_time = current_time - start_time

        # 每隔一秒记录数据到DataFrame
        if elapsed_time >= 1:
            # 计算总带宽
            total_bandwidth_mbps = (total_bytes_received * 8) / (elapsed_time * 1000000)  # Mbps
            print(f"Received bandwidth: {total_bandwidth_mbps:.2f} Mbps {time.time() - tick:.2f} s")

            # 记录时间
            new_row = {"Time (s)": elapsed_time}

            # 记录每个源IP的带宽
            for ip, bytes_received in source_ip_data.items():
                bandwidth_mbps = round((bytes_received * 8) / 1000000, 2)  # Mbps
                column_name = f"{ip}"
                new_row[column_name] = bandwidth_mbps

            # 将新行添加到DataFrame
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # 清空数据，准备下一秒的统计
            source_ip_data = {}
            start_time = current_time
            total_bytes_received = 0

        # 更新当前时间
        current_time = time.time()

    except KeyboardInterrupt:
        # 捕获Ctrl+C，停止服务器并退出
        print("Server stopped.")

        # 计算最终总带宽
        final_elapsed_time = duration
        final_total_bandwidth_mbps = (final_bytes_received * 8) / (final_elapsed_time * 1000000)  # Mbps
        print(f"Final bandwidth: {final_total_bandwidth_mbps:.2f} Mbps")

        df.to_csv("bandwidth_data.csv", index=False)  # 保存数据到CSV文件

        sock.close()
        break
