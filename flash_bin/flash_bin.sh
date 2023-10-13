#!/bin/bash

# 统计 /dev/ttyUSB* 设备的个数
device_count=$(ls /dev/ttyUSB* | wc -l)

echo "Total number of /dev/ttyUSB devices: $device_count"

# 设置默认的 firmware 文件路径
default_firmware="~/work/iot-sdk/project/xiaomi_616_sdk/customer_app/bl616_signal_ota/build_out/bl616_demo_wifi.bin"

# 解析命令行参数
while getopts ":b:" opt; do
  case $opt in
    b)
      custom_firmware="$OPTARG"
      ;;
    \?)
      echo "无效选项: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "选项 -$OPTARG 需要参数." >&2
      exit 1
      ;;
  esac
done

# 如果 -b 参数没有提供，使用默认的 firmware 文件
if [ -z "$custom_firmware" ]; then
  firmware_arg="--firmware $default_firmware"
else
  firmware_arg="--firmware $custom_firmware"
fi

# 设置 Python 命令
python_command="python /home/jokeo/work/dev_cube/project/bouffalo_dev_cube/core/bflb_iot_tool.py --chipname bl616 --baudrate 2000000 --xtal 40M --pt /home/jokeo/work/dev_cube/project/bouffalo_dev_cube/chips/bl616/partition/partition_cfg_4M.toml $firmware_arg"

# 遍历 /dev/ttyUSB* 端口
for port in /dev/ttyUSB*; do
    echo "Executing command for port: $port"
    $python_command --port "$port"
done

