#!/bin/bash

if [[ -z "${1:-}" || -z "${2:-}" ]]; then
	echo "usage: install_ros_rolling.sh <ros_distro_name> <apt_mirror_url>"
	exit 1
fi

ROS_DISTRO="$1"
MIRROR_URL="$2"

sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo apt install -y software-properties-common curl gnupg2

sudo sh -c "echo \"deb ${MIRROR_URL}/ros2/ubuntu \$(lsb_release -sc) main\" > /etc/apt/sources.list.d/ros2-latest.list"
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -

sudo apt update
sudo apt install -y ros-${ROS_DISTRO}-desktop-full
sudo apt install -y python3-colcon-common-extensions \
			python3-rosdep \
			python3-rosinstall-generator \
			python3-pip \
			build-essential
sudo apt install -y ros-dev-tools

sudo sh -c "echo \"source /opt/ros/${ROS_DISTRO}/setup.bash\" >> /root/.bashrc"
echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/orangepi/.bashrc

source /opt/ros/${ROS_DISTRO}/setup.bash
ros2 -h
