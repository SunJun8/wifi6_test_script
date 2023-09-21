import os
import time

# check if ip.toml file exists in current directory
if not os.path.exists("ip.toml"):
    # if it doesn't exist, execute 'python get_local_ip.py ip.toml' to get current ip list
    os.system("python get_local_ip.py ip.toml")

# read ip list from ip.toml file
with open("ip.toml", "r") as f:
    ip_list = f.read().splitlines()

# execute standby.py for each ip in the list
delay = 30000
for ip in ip_list:
    os.system(f"python standby.py -i {ip} -p 50201 -m 0 -o 44333 -b 1 -d 5 -l {delay}")
    delay -= 500
    time.sleep(0.5)
