"""把小车送进 Gazebo 的 launch。

阶段 5 更新：支持加载自定义世界（默认 room.world —— 四面墙 + 一个箱子）。

为什么需要它：
  Gazebo 默认的空世界里，2D 雷达水平扫一圈**什么都打不到**（全是 inf）。
  原因不是"地面太平"，而是**水平射线与地面平行、几何上没有交点**。
  要看到有效回波，必须在**射线的同一高度**上放物体 —— 这就是墙和箱子。
  （同时这为阶段 6 建图提供了带边界的环境。）

用法：
  ros2 launch xuegecar_sim_bringup gazebo.launch.py                    # 默认 room.world + GUI
  ros2 launch xuegecar_sim_bringup gazebo.launch.py gui:=false         # 无头
  ros2 launch xuegecar_sim_bringup gazebo.launch.py world:=/path/x.world   # 指定世界
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    declare_gui = DeclareLaunchArgument(
        'gui',
        default_value='true',
        description='是否启动 Gazebo 图形界面（无头验证时设为 false）',
    )
    gui = LaunchConfiguration('gui')

    bringup_share = get_package_share_directory('xuegecar_sim_bringup')
    desc_share = get_package_share_directory('xuegecar_sim_description')

    default_world = os.path.join(bringup_share, 'worlds', 'room.world')
    declare_world = DeclareLaunchArgument(
        'world',
        default_value=default_world,
        description='要加载的 Gazebo 世界文件（默认 room.world）',
    )
    world = LaunchConfiguration('world')

    # ---- 1. 用 xacro 展开参数化描述 ----
    xacro_file = os.path.join(desc_share, 'urdf', 'xuegecar_sim.urdf.xacro')
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str,
    )

    # ---- 2. 启动 Gazebo（带自定义世界）----
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('gazebo_ros'),
                'launch',
                'gazebo.launch.py',
            )
        ),
        launch_arguments={
            'verbose': 'true',
            'gui': gui,
            'world': world,
        }.items(),
    )

    # ---- 3. robot_state_publisher ----
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
    )

    # ---- 4. spawn_entity ----
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'xuegecar_sim',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.05',
        ],
        output='screen',
    )

    spawn_delayed = TimerAction(period=6.0, actions=[spawn_entity])

    return LaunchDescription([
        declare_gui,
        declare_world,
        gazebo,
        robot_state_publisher,
        spawn_delayed,
    ])
