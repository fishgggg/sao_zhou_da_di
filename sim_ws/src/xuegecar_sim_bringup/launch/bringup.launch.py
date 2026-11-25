"""一条命令起全套：底盘（仿真/假底盘/实车）+ 任务状态机（阶段 9.1-9.3）。

核心命题：**状态机不关心速度从哪来**。
它只认四个接口：/odom、/scan（进）、/cmd_vel_motor（出）、/cmd_vel_teleop（进）。
换底盘 = 换 launch 的一个开关，mission_control 一行不改。

用法：
  # 仿真（默认）
  ros2 launch xuegecar_sim_bringup bringup.launch.py
  ros2 launch xuegecar_sim_bringup bringup.launch.py initial_state:=TELEOP grace_period:=25.0

  # 不开 Gazebo，用假底盘（验证抽象层 / 没装 Gazebo 时调试状态机）
  ros2 launch xuegecar_sim_bringup bringup.launch.py sim:=false initial_state:=TELEOP grace_period:=3.0

  # 实车
  #   把 sim:=false 时起的 fake_chassis 换成真实的底盘驱动节点即可（接口相同）

参数：
  sim            true=Gazebo 仿真；false=假底盘（只做数学积分，不穿墙校验，不可用于导航）
  gui            仿真的 GUI 开关
  world          仿真世界文件
  initial_state  状态机启动状态（IDLE/TELEOP/MAPPING/LOCALIZING/NAVIGATING）
  grace_period   看门狗启动宽限（sim:=false 时启动快，3 秒足够）
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    bringup_share = get_package_share_directory('xuegecar_sim_bringup')
    desc_share = get_package_share_directory('xuegecar_sim_description')
    default_world = os.path.join(bringup_share, 'worlds', 'room.world')

    declare_sim = DeclareLaunchArgument(
        'sim', default_value='true',
        description='true=Gazebo 仿真；false=假底盘（验证抽象层）')
    declare_gui = DeclareLaunchArgument('gui', default_value='true')
    declare_world = DeclareLaunchArgument('world', default_value=default_world)
    declare_initial_state = DeclareLaunchArgument(
        'initial_state', default_value='IDLE',
        description='状态机启动状态（IDLE/TELEOP/MAPPING/LOCALIZING/NAVIGATING）')
    declare_grace = DeclareLaunchArgument(
        'grace_period', default_value='5.0',
        description='看门狗启动宽限（秒）；initial_state 非 IDLE 时建议 ≥25')
    declare_ns = DeclareLaunchArgument(
        'namespace', default_value='',
        description='节点与话题的命名空间（多车隔离，如 car1）。'
                    '注意：TF frame 和 Gazebo 实体不受它影响')

    sim = LaunchConfiguration('sim')
    gui = LaunchConfiguration('gui')
    world = LaunchConfiguration('world')
    initial_state = LaunchConfiguration('initial_state')
    grace_period = LaunchConfiguration('grace_period')
    ns = LaunchConfiguration('namespace')

    # ---- 仿真分支：复用 gazebo.launch.py（它包含 RSP + gzserver + spawn）----
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', 'gazebo.launch.py')),
        launch_arguments={'gui': gui, 'world': world}.items(),
        condition=IfCondition(sim),
    )

    # ---- 非仿真分支：自己起 RSP（gazebo.launch.py 把 RSP 和 Gazebo 绑在一起了）+ 假底盘 ----
    xacro_file = os.path.join(desc_share, 'urdf', 'xuegecar_sim.urdf.xacro')
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        namespace=ns,
        output='screen',
        parameters=[{'robot_description': robot_description, 'use_sim_time': False}],
        condition=UnlessCondition(sim),
    )

    chassis = Node(
        package='xuegecar_sim_mission',
        executable='fake_chassis',
        name='fake_chassis',
        namespace=ns,
        output='screen',
        condition=UnlessCondition(sim),
    )

    # ---- 状态机：两种模式都起，接口完全相同 ----
    mission = Node(
        package='xuegecar_sim_mission',
        executable='mission_control',
        name='mission_control',
        namespace=ns,
        output='screen',
        parameters=[{
            'initial_state': initial_state,
            'grace_period': ParameterValue(grace_period, value_type=float),
        }],
    )

    return LaunchDescription([
        declare_sim, declare_gui, declare_world, declare_initial_state,
        declare_grace, declare_ns,
        gazebo, rsp, chassis, mission,
    ])
