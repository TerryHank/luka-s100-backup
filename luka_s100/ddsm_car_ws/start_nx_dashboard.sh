#!/bin/bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /home/sunrise/luka_s100/ddsm_car_ws/install/setup.bash
export ROS_DOMAIN_ID=87 ROS_LOCALHOST_ONLY=1 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/sunrise/luka_s100/ddsm_car_ws/config/cyclonedds_offline.xml
export DDSM_WS=/home/sunrise/luka_s100/ddsm_car_ws LIGHT_DASHBOARD_PORT=8503 DASHBOARD_FLOOR_ID=floor_4
exec python3 /home/sunrise/luka_s100/ddsm_car_ws/tools/nx_dashboard.py
