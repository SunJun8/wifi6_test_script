import subprocess
import threading
import time


# 多线程执行fping操作
def ping_ip(ip, result_file):
    try:
        result = subprocess.check_output(f"fping -q -c 1 -b 50 -t 100 -p 1 {ip}", shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        result = f"{e.output}"

    with open(result_file, 'a') as file:
        file.write(result)


# 局域网段和文件名
ip_range = "192.168.31.1/24"
output_file = "ip_list.txt"

# 创建结果文件
timestamp = time.strftime("%Y%m%d%H%M%S")
result_file = f"result_{timestamp}.txt"

# 生成存活的IP列表并保存到文件 online_ips.txt
subprocess.run(["fping", "-agq", ip_range], stdout=open(output_file, "w"))

# 统计存活IP的数量
with open(output_file, "r") as file:
    online_ips = file.readlines()
num_alive_ips = len(online_ips)

print(f"Number of Alive IPs: {num_alive_ips}")

# 读取扫描结果文件，获取IP列表
with open(output_file, 'r') as file:
    ip_list = file.read().splitlines()

# 创建线程来执行ping操作
threads = []

for ip in ip_list:
    thread = threading.Thread(target=ping_ip, args=(ip, result_file))
    threads.append(thread)
    thread.start()

# 等待所有线程完成
for thread in threads:
    thread.join()

print("扫描和ping操作完成，结果已保存到fping_results.txt文件中")
