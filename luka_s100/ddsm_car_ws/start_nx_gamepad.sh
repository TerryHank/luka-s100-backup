#!/bin/bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /home/sunrise/luka_s100/ddsm_car_ws/install/setup.bash
export ROS_DOMAIN_ID=87 ROS_LOCALHOST_ONLY=1 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/sunrise/luka_s100/ddsm_car_ws/config/cyclonedds_offline.xml
exec ros2 launch ddsm_car_control ddsm_gamepad.launch.py params_file:=/home/sunrise/luka_s100/ddsm_car_ws/config/nx_gamepad.yaml
