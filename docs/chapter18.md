---
number headings: first-level 2, start-at 18
---

## 18 第 18 章 课程实验二：智能轮椅仿真

> 本章以智能轮椅为载体，在 ROS2 + Gazebo 仿真环境中实践机器人导航全栈技术：SLAM 建图、自主定位、路径规划与运动控制。这是对第 9-11 章理论知识的综合应用。

### 18.1 项目概述

#### 18.1.1 项目背景

智能轮椅是服务机器人领域的重要应用方向，面向老年人和行动不便群体提供自主导航、避障、语音交互等辅助功能。本实验通过仿真环境，让学生掌握从环境建模到自主导航的完整技术链。

#### 18.1.2 学习目标

**表 18-1** 学习目标
<!-- tab:ch18-1 学习目标 -->

| 目标 | 具体内容 | 涉及章节 |
|------|---------|----------|
| URDF 建模 | Gazebo 仿真环境搭建、轮椅 URDF 模型创建 | 第7章 仿真 |
| SLAM 建图 | SLAM Toolbox 建图流程与参数调优 | 第13章 SLAM |
| 自主导航 | Nav2 导航栈配置、多点巡航编程 | 第14章 导航 |
| 传感器仿真 | 激光雷达、IMU、里程计数据流 | 第9章 传感器 |

上表对学习目标中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

#### 18.1.3 系统架构

```bob
+-------------------------------------------------------------------+
|              "智能轮椅仿真系统架构"                                 |
+-------------------------------------------------------------------+
|                                                                   |
|  +---------------------+      +---------------------+            |
|  |   "Gazebo 仿真器"    |      |   "RViz2 可视化"     |            |
|  |   物理引擎           |      |   地图/路径/传感器   |            |
|  |   传感器仿真         |      |   目标点设置         |            |
|  +---------+-----------+      +---------+-----------+            |
|            |                            |                        |
|            v                            v                        |
|  +---------+----------------------------+-----------+            |
|  |                "ROS2 Humble"                      |            |
|  |  +------------+  +----------+  +--------------+  |            |
|  |  | SLAM       |  | Nav2     |  | TF2          |  |            |
|  |  | Toolbox    |  | Stack    |  | 坐标变换     |  |            |
|  |  +------------+  +----------+  +--------------+  |            |
|  |  +------------+  +----------+  +--------------+  |            |
|  |  | cmd_vel    |  | /scan    |  | /odom        |  |            |
|  |  | 速度指令   |  | 激光数据 |  | 里程计       |  |            |
|  |  +-----+------+  +----+-----+  +------+-------+  |            |
|  +--------+---+----------+-----------+----+----------+            |
|           |   |          |           |    |                       |
|           v   v          v           v    v                       |
|  +--------+---+----------+-----------+----+----------+            |
|  |          "轮椅 URDF 模型"                          |            |
|  |   差速驱动  |  2D 激光雷达  |  IMU  |  摄像头     |            |
|  +-----------------------------------------------------------+   |
+-------------------------------------------------------------------+
```


**图 18-1** 上图以框图形式描绘了系统架构的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch18-1 上图以框图形式描绘了系统架构的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

### 18.2 环境搭建

#### 18.2.1 ROS2 工作空间

```bash

# 创建工作空间
mkdir -p ~/wheelchair_ws/src
cd ~/wheelchair_ws/src

# 创建功能包
ros2 pkg create wheelchair_description --build-type ament_cmake
ros2 pkg create wheelchair_gazebo --build-type ament_cmake \
    --dependencies gazebo_ros_pkgs
ros2 pkg create wheelchair_navigation --build-type ament_cmake \
    --dependencies nav2_bringup slam_toolbox
```

#### 18.2.2 URDF 轮椅模型

```xml
<?xml version="1.0"?>
<robot name="smart_wheelchair" xmlns:xacro="http://www.ros.org/wiki/xacro">

  <!-- 底盘 -->
  <link name="base_link">
    <visual>
      <geometry>
        <box size="0.6 0.5 0.3"/>
      </geometry>
      <material name="gray">
        <color rgba="0.5 0.5 0.5 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <box size="0.6 0.5 0.3"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="30.0"/>
      <inertia ixx="0.5" ixy="0" ixz="0" iyy="0.8" iyz="0" izz="0.6"/>
    </inertial>
  </link>

  <!-- 左驱动轮 -->
  <link name="left_wheel">
    <visual>
      <geometry>
        <cylinder radius="0.15" length="0.05"/>
      </geometry>
    </visual>
    <collision>
      <geometry>
        <cylinder radius="0.15" length="0.05"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="2.0"/>
      <inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.005"/>
    </inertial>
  </link>

  <joint name="left_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="left_wheel"/>
    <origin xyz="0 0.275 -0.05" rpy="-1.5708 0 0"/>
    <axis xyz="0 0 1"/>
  </joint>

  <!-- 激光雷达 -->
  <link name="lidar_link">
    <visual>
      <geometry>
        <cylinder radius="0.04" length="0.05"/>
      </geometry>
    </visual>
  </link>

  <joint name="lidar_joint" type="fixed">
    <parent link="base_link"/>
    <child link="lidar_link"/>
    <origin xyz="0.25 0 0.175"/>
  </joint>

  <!-- Gazebo 差速驱动插件 -->
  <gazebo>
    <plugin name="diff_drive" filename="libgazebo_ros_diff_drive.so">
      <ros>
        <namespace>/wheelchair</namespace>
      </ros>
      <left_joint>left_wheel_joint</left_joint>
      <right_joint>right_wheel_joint</right_joint>
      <wheel_separation>0.55</wheel_separation>
      <wheel_diameter>0.30</wheel_diameter>
      <max_wheel_torque>50</max_wheel_torque>
      <publish_odom>true</publish_odom>
      <publish_odom_tf>true</publish_odom_tf>
      <odometry_frame>odom</odometry_frame>
      <robot_base_frame>base_link</robot_base_frame>
    </plugin>
  </gazebo>

  <!-- Gazebo 激光雷达插件 -->
  <gazebo reference="lidar_link">
    <sensor type="ray" name="lidar">
      <pose>0 0 0 0 0 0</pose>
      <visualize>true</visualize>
      <update_rate>10</update_rate>
      <ray>
        <scan>
          <horizontal>
            <samples>360</samples>
            <resolution>1</resolution>
            <min_angle>-3.14159</min_angle>
            <max_angle>3.14159</max_angle>
          </horizontal>
        </scan>
        <range>
          <min>0.12</min>
          <max>10.0</max>
        </range>
      </ray>
      <plugin name="gazebo_ros_lidar" filename="libgazebo_ros_ray_sensor.so">
        <ros>
          <namespace>/wheelchair</namespace>
          <remapping>~/out:=scan</remapping>
        </ros>
        <output_type>sensor_msgs/LaserScan</output_type>
        <frame_name>lidar_link</frame_name>
      </plugin>
    </sensor>
  </gazebo>
</robot>
```

### 18.3 SLAM 建图实验

#### 18.3.1 SLAM 建图流程

```bob
  "键盘遥控"       "SLAM Toolbox"        "地图"
      |                  |                  |
      | cmd_vel          |                  |
      +─────────────────>| 扫描匹配         |
      |                  +─────────────>    |
      |                  | 位姿图优化       |
      |                  +─────────────>    |
      |                  | 回环检测         |
      |                  +─────────────>    |
      |                  |     栅格更新     |
      |                  +─────────────────>|
      |                  |                  |
      | 保存地图          |                  |
      +──────────────────+─────────────────>|
      |                  |    .pgm + .yaml  |
```


**图 18-2** 该框图展示了 SLAM 建图流程的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch18-2 该框图展示了 SLAM 建图流程的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

#### 18.3.2 操作命令

```bash
# 终端 1：启动 Gazebo 仿真

ros2 launch wheelchair_gazebo hospital_world.launch.py

# 终端 2：启动 SLAM Toolbox
ros2 launch wheelchair_navigation slam.launch.py

# 终端 3：键盘遥控建图
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
    --ros-args --remap cmd_vel:=/wheelchair/cmd_vel

# 终端 4：保存地图
ros2 run nav2_map_server map_saver_cli -f ~/maps/hospital
```

#### 18.3.3 SLAM 参数调优

**表 18-2** SLAM 参数调优
<!-- tab:ch18-2 SLAM 参数调优 -->

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `resolution` | 0.05 | 地图分辨率（m/pixel），越小越精细但内存越大 |
| `max_laser_range` | 8.0 | 超出此距离的激光点被丢弃 |
| `minimum_travel_distance` | 0.3 | 触发新匹配的最小位移（m） |
| `minimum_travel_heading` | 0.3 | 触发新匹配的最小旋转（rad） |
| `do_loop_closing` | true | 启用回环检测以修正累积误差 |

上述参数配置是 SLAM 参数调优的典型推荐值，实际工程中可根据硬件条件和性能需求进行适当调整。

#### 18.3.3b 参数配置文件

```yaml
# slam_toolbox 参数
slam_toolbox:
  ros__parameters:
    solver_plugin: solver_plugins::CeresSolver
    ceres_linear_solver: SPARSE_NORMAL_CHOLESKY
    ceres_preconditioner: SCHUR_JACOBI

    # 关键调优参数
    resolution: 0.05              # 地图分辨率（米/像素）
    max_laser_range: 8.0          # 激光最大有效距离
    minimum_travel_distance: 0.3  # 最小移动距离触发扫描匹配
    minimum_travel_heading: 0.3   # 最小旋转角度触发匹配

    # 回环检测
    do_loop_closing: true
    loop_match_minimum_chain_size: 10
    loop_match_maximum_variance_coarse: 3.0
```

### 18.4 Nav2 导航实验

#### 18.4.1 Nav2 导航栈架构

```bob
  ┌─────────────────────────────────────────────────────────┐
  │                   "Nav2 导航栈"                         │
  ├───────────────┬──────────────┬──────────────────────────┤
  │  "BT Navigator" │  行为树调度  │  恢复行为 + 重规划       │
  ├───────────────┼──────────────┼──────────────────────────┤
  │  "Planner"     │  NavFn (A*)  │  全局路径 → /plan        │
  ├───────────────┼──────────────┼──────────────────────────┤
  │  "Controller"  │  DWB (DWA)   │  局部速度 → /cmd_vel     │
  ├───────────────┼──────────────┼──────────────────────────┤
  │  "Costmap"     │  全局 + 局部 │  膨胀层 + 障碍物层       │
  ├───────────────┼──────────────┼──────────────────────────┤
  │  "AMCL"        │  粒子滤波    │  /scan + /odom → 定位    │
  └───────────────┴──────────────┴──────────────────────────┘
```


**图 18-3** 上图直观呈现了 Nav2 导航栈架构的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch18-3 上图直观呈现了 Nav2 导航栈架构的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

#### 18.4.2 导航参数配置

```yaml
# Nav2 参数文件
bt_navigator:
  ros__parameters:
    global_frame: map
    robot_base_frame: base_link
    default_bt_xml_filename: "navigate_w_replanning_and_recovery.xml"

controller_server:
  ros__parameters:
    controller_frequency: 20.0
    FollowPath:
      plugin: "dwb_core::DWBLocalPlanner"
      max_vel_x: 0.5           # 轮椅最大前进速度
      min_vel_x: -0.2          # 允许小幅后退
      max_vel_theta: 0.8       # 最大旋转速度
      min_speed_xy: 0.0
      max_speed_xy: 0.5
      acc_lim_x: 1.0           # 加速度限制（舒适性）
      decel_lim_x: -1.5
      acc_lim_theta: 1.5

planner_server:
  ros__parameters:
    GridBased:
      plugin: "nav2_navfn_planner/NavfnPlanner"
      tolerance: 0.5
      use_astar: true

local_costmap:
  local_costmap:
    ros__parameters:
      update_frequency: 5.0
      publish_frequency: 2.0
      rolling_window: true
      width: 3
      height: 3
      resolution: 0.05
      inflation_radius: 0.55    # 轮椅半径 + 安全余量
      cost_scaling_factor: 3.0

global_costmap:
  global_costmap:
    ros__parameters:
      update_frequency: 1.0
      publish_frequency: 1.0
      resolution: 0.05
      inflation_radius: 0.55
```

**表 18-3** 
<!-- tab:ch18-3  -->

| 参数类别 | 关键参数 | 轮椅推荐值 | 理由 |
|----------|---------|------------|------|
| 速度限制 | `max_vel_x` | 0.5 m/s | 室内安全速度上限 |
| 加速度 | `acc_lim_x` | 1.0 m/s² | 乘客舒适性考虑 |
| 减速度 | `decel_lim_x` | -1.5 m/s² | 紧急制动能力 |
| 旋转速度 | `max_vel_theta` | 0.8 rad/s | 避免乘客眩晕 |
| 膨胀半径 | `inflation_radius` | 0.55 m | 轮椅半径 0.38m + 安全余量 |
| 代价缩放 | `cost_scaling_factor` | 3.0 | 平衡安全与通过性 |

#### 18.4.3 导航启动

```bash
# 启动导航栈
ros2 launch wheelchair_navigation navigation.launch.py \
    map:=$HOME/maps/hospital.yaml

# Python 脚本：自动巡航
```

```python
#!/usr/bin/env python3
"""智能轮椅自动巡航脚本"""
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import rclpy

def main():
    rclpy.init()
    navigator = BasicNavigator()

    # 设置初始位姿
    initial_pose = PoseStamped()
    initial_pose.header.frame_id = 'map'
    initial_pose.pose.position.x = 0.0
    initial_pose.pose.position.y = 0.0
    initial_pose.pose.orientation.w = 1.0
    navigator.setInitialPose(initial_pose)
    navigator.waitUntilNav2Active()

    # 定义巡航点（医院场景）
    waypoints = [
        create_pose(5.0, 0.0, 0.0),    # 走廊末端
        create_pose(5.0, 3.0, 1.57),   # 病房门口
        create_pose(0.0, 3.0, 3.14),   # 护士站
        create_pose(0.0, 0.0, -1.57),  # 返回起点
    ]

    # 执行多点导航
    navigator.followWaypoints(waypoints)
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback:
            print(f'到达第 {feedback.current_waypoint + 1}/{len(waypoints)} 个目标点')

    print('巡航完成！')
    navigator.lifecycleShutdown()

def create_pose(x, y, yaw):
    import math
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.z = math.sin(yaw / 2)
    pose.pose.orientation.w = math.cos(yaw / 2)
    return pose

if __name__ == '__main__':
    main()
```

### 18.5 实验拓展：多楼层导航

#### 18.5.1 多楼层导航流程

```bob
  "当前楼层"               "电梯"              "目标楼层"
      |                     |                    |
      | 导航到电梯口         |                    |
      +────────────────────>|                    |
      |                     | 进入电梯            |
      |                     +───>                 |
      |  切换地图文件        |                    |
      +─ ─ ─ ─ ─ ─ ─ ─ ─ ─>|                    |
      |                     | 到达目标楼层        |
      |                     +───────────────────> |
      |                     |  设置初始位姿       |
      |                     +───────────────────> |
      |                     |     AMCL 重定位     |
      |                     |<───────────────────+|
      |                     |  继续导航           |
      |                     +───────────────────> |
```


**图 18-4** 上图以框图形式描绘了多楼层导航流程的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch18-4 上图以框图形式描绘了多楼层导航流程的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

#### 18.5.2 多楼层地图管理

在实际医院场景中，轮椅需要在多个楼层之间导航。可通过地图切换机制实现：

```python
class MultiFloorNavigator:
    def __init__(self, navigator):
        self.navigator = navigator
        self.maps = {
            1: 'hospital_floor1.yaml',
            2: 'hospital_floor2.yaml',
            3: 'hospital_floor3.yaml',
        }
        self.current_floor = 1

    def switch_floor(self, target_floor):
        """切换楼层地图"""
        if target_floor == self.current_floor:
            return

        # 导航到电梯口
        elevator_pose = self.get_elevator_pose(self.current_floor)
        self.navigator.goToPose(elevator_pose)
        self.navigator.waitUntilTaskComplete()

        # 切换地图
        self.navigator.changeMap(self.maps[target_floor])
        self.current_floor = target_floor

        # 设置电梯出口位姿
        exit_pose = self.get_elevator_exit_pose(target_floor)
        self.navigator.setInitialPose(exit_pose)
```

### 18.6 本章小结


**表 18-4** 本章通过智能轮椅仿真项目，实践了机器人导航的完整技术栈：
<!-- tab:ch18-4 本章通过智能轮椅仿真项目，实践了机器人导航的完整技术栈： -->

| 实验环节 | 对应章节 | 关键技术 |
|----------|---------|---------|
| URDF 建模 | 第9章 ROS | 机器人描述、坐标系、TF |
| Gazebo 仿真 | 第7章 仿真 | 物理引擎、传感器仿真 |
| SLAM 建图 | 第10章 SLAM | SLAM Toolbox、激光匹配 |
| Nav2 导航 | 第11章 导航 | A*、DWA、代价地图、AMCL |
| 多点巡航 | 第12章 多机器人 | 任务编排、状态管理 |

上表对本章小结中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

### 18.7 本章测验

<div id="exam-meta" data-exam-id="chapter14" data-exam-title="第 18 章 智能轮椅仿真实验 测验" style="display:none"></div>

<!-- mkdocs-quiz intro -->

<quiz>
1) 在 Gazebo 仿真中，URDF 模型中 `<inertial>` 标签的主要作用是？
- [ ] 定义模型的外观颜色
- [x] 定义质量和惯性矩，用于物理引擎计算动力学
- [ ] 定义碰撞检测形状
- [ ] 定义关节运动范围

物理引擎需要质量和惯性矩参数来计算重力、摩擦力和碰撞响应，缺少这些参数会导致仿真行为异常。
</quiz>

<quiz>
2) SLAM Toolbox 中 `minimum_travel_distance` 参数的作用是？
- [ ] 设置激光雷达的最大探测距离
- [ ] 限制机器人的最大移动速度
- [x] 设置触发新一次扫描匹配所需的最小移动距离
- [ ] 定义回环检测的搜索范围

该参数避免机器人静止或小幅移动时频繁触发扫描匹配，减少计算开销并提高建图质量。
</quiz>

<quiz>
3) Nav2 中 `inflation_radius` 参数设为 0.55m 的依据是？
- [ ] 激光雷达的最小探测距离
- [ ] 地图分辨率的倍数
- [x] 机器人物理半径加上安全余量
- [ ] DWA 算法的速度采样范围

膨胀半径应大于机器人的物理半径，确保规划的路径与障碍物保持安全距离。轮椅尺寸约 0.6×0.5m，半径约 0.38m，加上余量约 0.55m。
</quiz>

<quiz>
4) 使用 `BasicNavigator.followWaypoints()` 进行多点导航时，机器人依次经过所有目标点的行为称为？
- [ ] 路径跟踪（Path Tracking）
- [x] 航点跟随（Waypoint Following）
- [ ] 纯追踪（Pure Pursuit）
- [ ] 势场导航（Potential Field Navigation）

航点跟随是依次访问预定义目标点的导航模式，Nav2 提供了内置支持，适合巡检、配送等任务。
</quiz>

<quiz>
5) 在多楼层导航场景中，切换楼层时需要做哪两个关键操作？
- [ ] 重新建图和调整 PID 参数
- [ ] 更换 URDF 模型和重启 Gazebo
- [x] 切换地图文件和重新设置初始位姿
- [ ] 重启 Nav2 和清空代价地图

切换楼层需要加载目标楼层地图并在电梯出口设置初始位姿，让 AMCL 从新位置开始定位。
</quiz>

<!-- mkdocs-quiz results -->
