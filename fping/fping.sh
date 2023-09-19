#!/bin/bash

# 生成存活的IP列表并保存到文件 online_ips.txt
fping -g 192.168.31.1/24 -a -q > online_ips.txt

# 统计存活IP的数量
num_alive_ips=$(wc -l < online_ips.txt)

echo "Number of Alive IPs: $num_alive_ips"

# 创建一个用于存储结果的文件
result_file="fping_results.txt"

# 清空或创建结果文件
> "$result_file"

# 创建变量以存储总丢包数和总发包数
total_loss=0
total_sent=0

# 循环遍历在线IP列表，执行fping并记录最后一行统计数据（并行执行，每次限制5个）
cat online_ips.txt | xargs -I {} -P 5 bash -c '
    ip="{}"
    echo "Pinging $ip..."
    fping_result=$(fping -c 100 -b 4000 -t 100 -p 1 "$ip" 2>&1 | tail -n 1)
    echo "$ip: $fping_result" >> "$0"
    loss_rate=$(echo "$fping_result" | grep -oP "\d+%\s+packet loss" | awk "{print \$1}")
    total_loss=$((total_loss + loss_rate))
    total_sent=$((total_sent + 100))
' "$result_file"

# 显示结果文件内容
cat "$result_file"
