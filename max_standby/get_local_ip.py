import subprocess
import sys


def get_gateway_ip():
    # 获取当前网关的IP地址
    result = subprocess.run(
        ["ip", "route", "show", "0.0.0.0/0"], stdout=subprocess.PIPE
    )
    output = result.stdout.decode("utf-8").strip().split()
    return output[2]


def get_local_ips(gateway_ip):
    # 获取当前局域网段内所有存在的IP地址，排除网关IP
    local_ips = []
    # 使用传入的gateway_ip构造fping命令中的IP地址范围
    ip_range = f"{gateway_ip}/24"
    print(f"IP range: {ip_range}")
    result = subprocess.run(["fping", "-agq", ip_range], stdout=subprocess.PIPE)
    output = result.stdout.decode("utf-8").strip().split("\n")
    for line in output:
        ip = line.split()[0]
        if ip != gateway_ip:  # 排除网关IP地址
            local_ips.append(ip)
    return local_ips


def save_to_file(filename, ips):
    # 将IP地址保存到指定文件中
    with open(filename, "w") as file:
        for ip in ips:
            file.write(f"{ip}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    gateway_ip = get_gateway_ip()
    print(f"Gateway IP: {gateway_ip}")
    local_ips = get_local_ips(gateway_ip)  # 传递网关IP地址给get_local_ips函数
    num_ips = len(local_ips)  # 排除当前网关的IP地址后的IP个数
    print(f"Number of local IPs except gateway: {num_ips}")
    save_to_file(filename, local_ips)
    print(f"IP addresses saved to {filename}")


if __name__ == "__main__":
    main()
