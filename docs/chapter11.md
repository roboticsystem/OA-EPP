---
number headings: first-level 2, start-at 11
---

## 11 第 11 章 ROS 程序设计：从入门到 micro-ROS 嵌入式集成

本章系统介绍 ROS（Robot Operating System）的核心概念、ROS2 编程方法，以及如何通过 micro-ROS 将 STM32 等嵌入式系统无缝接入 ROS2 生态。面向具备嵌入式开发基础的研究生，强调理论与工程结合，从基础概念到完整机器人系统案例。

学习目标：

- 理解 ROS 的设计哲学与核心架构；
- 掌握 ROS2 节点、话题、服务、动作的编程方法；
- 能够搭建 ROS2 开发环境并完成基础编程任务；
- 理解 micro-ROS 的架构，能在 STM32 上实现 ROS2 节点；
- 具备设计和实现 ROS2 + micro-ROS 完整机器人系统的能力。

---

### 11.1 ROS 简介

#### 11.1.1 什么是 ROS

ROS（Robot Operating System）并非传统意义上的操作系统，而是一个面向机器人软件开发的开源框架。它提供了一套工具、库和约定，帮助开发者构建复杂的机器人应用程序。ROS 的核心价值在于：

- **代码复用**：标准化的通信接口使不同开发者的模块可以无缝集成；
- **分布式计算**：多个进程（节点）可运行在不同机器上，通过网络透明通信；
- **工具生态**：可视化（RViz2）、仿真（Gazebo）、数据记录（rosbag）等工具极大提升开发效率；
- **社区驱动**：全球数千个开源包覆盖导航、感知、操纵等机器人核心领域。

#### 11.1.2 ROS 的历史演进

**表 11-1** ROS 的历史演进
<!-- tab:ch11-1 ROS 的历史演进 -->

| 阶段 | 时间 | 关键事件 |
|------|------|----------|
| ROS1 诞生 | 2007 | Willow Garage 启动开发，基于 TCPROS 通信 |
| ROS1 成熟 | 2010-2020 | Indigo → Kinetic → Melodic → Noetic，广泛用于学术 |
| ROS2 启动 | 2015 | 为解决 ROS1 的实时性、安全性、多机器人支持等问题 |
| ROS2 稳定 | 2022 | Humble Hawksbill（LTS），成为推荐版本 |
| ROS2 最新 | 2024 | Jazzy Jalisco，持续改进 |

**ROS1 → ROS2 的核心改进：**

- 通信层从自定义 TCPROS 迁移到工业标准 DDS（Data Distribution Service）；
- 原生支持实时系统（RTOS）和嵌入式平台；
- 去中心化架构（移除 rosmaster）；
- 内置安全机制（SROS2，基于 DDS Security）；

- 支持多种编程语言（Python、C++、Rust 等）的客户端库。

#### 11.1.3 ROS 与本课程的关系

```bob
┌─────────────────────────────────────────────────────────────┐
│                    机器人系统课程知识体系                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  STM32   │  │ FreeRTOS │  │  传感器  │  │  电机驱动  │  │
│  │  底层    │  │  实时    │  │  采集    │  │    PID     │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘  │
│       │             │             │               │         │
│       └──────┬──────┴──────┬──────┘               │         │
│              │             │                      │         │
│         ┌────▼─────────────▼──────────────────────▼────┐    │
│         │         micro-ROS（嵌入式 ROS2 节点）        │    │
│         └────────────────────┬─────────────────────────┘    │
│                              │                              │
│                    ┌─────────▼──────────┐                   │
│                    │   ROS2 通信框架    │                   │
│                    └─────────┬──────────┘                   │
│                              │                              │
│       ┌──────────────────────┼───────────────────┐          │
│       │                      │                   │          │
│  ┌────▼─────┐  ┌─────────────▼──────┐  ┌────────▼───────┐  │
│  │   导航   │  │   感知与决策       │  │   可视化监控   │  │
│  │  Nav2    │  │  SLAM, 路径规划   │  │  RViz2, rqt    │  │
│  └──────────┘  └────────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```


**图 11-1** 上图以框图形式描绘了 ROS 与本课程的关系的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch11-1 上图以框图形式描绘了 ROS 与本课程的关系的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

本课程前 12 章建立的嵌入式开发能力（STM32、FreeRTOS、传感器、电机控制）是机器人底层基础。本章通过 ROS2 和 micro-ROS，将这些底层能力与上层机器人软件框架连接，完成从单片机到完整机器人系统的知识闭环。

---

### 11.2 ROS2 核心概念

#### 11.2.1 计算图（Computation Graph）

ROS2 的核心是一个分布式计算图，由以下元素构成：

**节点（Node）**：最小的计算单元，执行特定功能（如读取传感器、控制电机）。每个节点是独立进程，可独立启动和停止。

**话题（Topic）**：节点间的异步通信通道，采用发布-订阅（Pub-Sub）模式。发布者不知道谁在订阅，订阅者不知道谁在发布——这就是松耦合。

**服务（Service）**：同步的请求-响应通信。客户端发送请求，服务端返回结果。适用于需要确认的操作（如设置参数、触发动作）。

**动作（Action）**：长时间异步任务的通信模式。客户端发送目标，服务端返回反馈和最终结果。适用于导航、机械臂运动等耗时操作。

```bob
┌───────────────────────────────────────────────────────┐
│                 ROS2 通信模式对比                      │
├──────────┬────────────┬───────────┬───────────────────┤
│  模式    │  话题      │  服务     │  动作             │
├──────────┼────────────┼───────────┼───────────────────┤
│  模型    │  Pub-Sub   │  请求响应 │  目标-反馈-结果   │
│  同步    │  异步      │  同步     │  异步             │
│  方向    │  单向广播  │  双向点对 │  双向+反馈流      │
│  用例    │  传感器流  │  参数设置 │  导航, 抓取       │
└──────────┴────────────┴───────────┴───────────────────┘
```


**图 11-2** 该框图展示了计算图（Computation Graph）的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch11-2 该框图展示了计算图（Computation Graph）的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

#### 11.2.2 DDS 与 QoS

ROS2 的通信基于 DDS（Data Distribution Service）标准，这是一个工业级的发布-订阅中间件。DDS 带来的关键能力：

- **去中心化发现**：节点自动发现彼此，无需中央协调器；
- **QoS 策略**：精细控制通信质量（可靠性、持久性、历史深度等）；
- **跨平台**：支持多种 DDS 实现（Fast DDS、Cyclone DDS、Connext DDS）。


**表 11-2** 常用 QoS 配置：
<!-- tab:ch11-2 常用 QoS 配置： -->

| QoS 策略 | 可选值 | 说明 |
|----------|--------|------|
| Reliability | RELIABLE / BEST_EFFORT | 可靠传输 vs 尽力传输 |
| Durability | VOLATILE / TRANSIENT_LOCAL | 是否缓存最近消息 |
| History | KEEP_LAST(N) / KEEP_ALL | 保留最近N条 vs 全部 |
| Deadline | Duration | 消息最大间隔 |

上述参数配置是 DDS 与 QoS 的典型推荐值，实际工程中可根据硬件条件和性能需求进行适当调整。

#### 11.2.3 包与工作空间

**工作空间（Workspace）**：ROS2 项目的顶层目录，包含一个或多个包。使用 colcon 构建系统管理。

**包（Package）**：功能模块的最小单元。每个包包含：

- `package.xml`：包的元数据和依赖；
- `CMakeLists.txt`（C++）或 `setup.py`（Python）：构建配置；
- 源代码、Launch 文件、配置文件等。

工作空间结构：

```text
ros2_ws/
├── src/
│   ├── my_robot_pkg/
│   │   ├── package.xml
│   │   ├── setup.py
│   │   ├── my_robot_pkg/
│   │   │   ├── __init__.py
│   │   │   ├── publisher_node.py
│   │   │   └── subscriber_node.py
│   │   └── launch/
│   │       └── robot.launch.py
│   └── my_robot_msgs/
│       ├── package.xml
│       ├── CMakeLists.txt
│       ├── msg/
│       │   └── SensorData.msg
│       └── srv/
│           └── SetSpeed.srv
├── build/    ← colcon 构建输出
├── install/  ← 安装目录
└── log/      ← 构建日志
```

---

### 11.3 ROS2 开发环境搭建

#### 11.3.1 Ubuntu + ROS2 Humble 安装

ROS2 Humble Hawksbill 是当前推荐的长期支持版本，支持 Ubuntu 22.04 LTS。

```bash
# 设置 locale
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

# 添加 ROS2 仓库
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 安装 ROS2 桌面版
sudo apt update
sudo apt install ros-humble-desktop

# 环境配置
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc

# 安装 colcon 构建工具
sudo apt install python3-colcon-common-extensions
```

验证安装：

```bash
ros2 run demo_nodes_cpp talker    # 终端1
ros2 run demo_nodes_py listener   # 终端2
```

#### 11.3.2 Docker 化 ROS2 环境

对于不便直接安装的环境，可使用 Docker：

```yaml
# docker-compose.yml
version: '3'
services:
  ros2:
    image: osrf/ros:humble-desktop
    network_mode: host
    environment:
      - DISPLAY=${DISPLAY}
      - ROS_DOMAIN_ID=0
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix
      - ./ros2_ws:/root/ros2_ws
    command: bash
```

```bash
docker compose up -d
docker compose exec ros2 bash
```

---

### 11.4 ROS2 基础编程

#### 11.4.1 创建工作空间与包

```bash
# 创建工作空间
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# 创建 Python 包
ros2 pkg create --build-type ament_python my_robot_pkg \
  --dependencies rclpy std_msgs geometry_msgs

# 创建 C++ 包
ros2 pkg create --build-type ament_cmake my_robot_cpp \
  --dependencies rclcpp std_msgs

# 构建
cd ~/ros2_ws
colcon build
source install/setup.bash
```

#### 11.4.2 Publisher 与 Subscriber（Python）

**发布者节点**（`my_robot_pkg/publisher_node.py`）：

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class MinimalPublisher(Node):
    def __init__(self):
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(String, 'robot_status', 10)
        self.timer = self.create_timer(0.5, self.timer_callback)
        self.count = 0

    def timer_callback(self):
        msg = String()
        msg.data = f'Robot status: active, count={self.count}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.count += 1

def main(args=None):
    rclpy.init(args=args)
    node = MinimalPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

**订阅者节点**（`my_robot_pkg/subscriber_node.py`）：

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class MinimalSubscriber(Node):
    def __init__(self):
        super().__init__('minimal_subscriber')
        self.subscription = self.create_subscription(
            String, 'robot_status', self.listener_callback, 10)

    def listener_callback(self, msg):
        self.get_logger().info(f'Received: "{msg.data}"')

def main(args=None):
    rclpy.init(args=args)
    node = MinimalSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

#### 11.4.3 Publisher 与 Subscriber（C++）

```cpp
// publisher_node.cpp
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class MinimalPublisher : public rclcpp::Node {
public:
    MinimalPublisher() : Node("minimal_publisher"), count_(0) {
        publisher_ = this->create_publisher<std_msgs::msg::String>(
            "robot_status", 10);
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(500),
            std::bind(&MinimalPublisher::timer_callback, this));
    }

private:
    void timer_callback() {
        auto msg = std_msgs::msg::String();
        msg.data = "Robot status: active, count=" + std::to_string(count_++);
        publisher_->publish(msg);
        RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", msg.data.c_str());
    }
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    size_t count_;
};

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<MinimalPublisher>());
    rclcpp::shutdown();
    return 0;
}
```

#### 11.4.4 服务编程

自定义服务接口（`my_robot_msgs/srv/SetSpeed.srv`）：

```text
# Request
float64 target_speed
string direction
---
# Response
bool success
string message
```

服务端（Python）：

```python
from my_robot_msgs.srv import SetSpeed
import rclpy
from rclpy.node import Node

class SpeedService(Node):
    def __init__(self):
        super().__init__('speed_service')
        self.srv = self.create_service(SetSpeed, 'set_speed', self.callback)
        self.current_speed = 0.0

    def callback(self, request, response):
        self.current_speed = request.target_speed
        self.get_logger().info(
            f'Setting speed to {request.target_speed} ({request.direction})')
        response.success = True
        response.message = f'Speed set to {self.current_speed}'
        return response
```

#### 11.4.5 Launch 文件

Launch 文件用于同时启动多个节点：

```python
# launch/robot.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_robot_pkg',
            executable='publisher_node',
            name='status_publisher',
            parameters=[{'publish_rate': 10.0}],
        ),
        Node(
            package='my_robot_pkg',
            executable='subscriber_node',
            name='status_monitor',
        ),
    ])
```

运行：

```bash
ros2 launch my_robot_pkg robot.launch.py
```

---

### 11.5 ROS2 进阶实例：移动机器人控制

#### 11.5.1 Turtlesim 入门

Turtlesim 是 ROS2 内置的简单仿真器，适合学习基本概念：

```bash
# 终端1：启动仿真器
ros2 run turtlesim turtlesim_node

# 终端2：键盘控制
ros2 run turtlesim turtle_teleop_key

# 终端3：查看话题
ros2 topic list
ros2 topic echo /turtle1/cmd_vel
ros2 topic info /turtle1/pose
```

#### 11.5.2 运动控制：cmd_vel

机器人运动的标准接口是 `geometry_msgs/msg/Twist` 消息，通过 `cmd_vel` 话题发布：

```python
from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node

class SquareDriver(Node):
    """驱动机器人走正方形"""
    def __init__(self):
        super().__init__('square_driver')
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.control_loop)
        self.state = 'forward'
        self.elapsed = 0.0

    def control_loop(self):
        msg = Twist()
        self.elapsed += 0.1

        if self.state == 'forward':
            msg.linear.x = 0.5    # 前进 0.5 m/s
            if self.elapsed > 2.0:
                self.state = 'turn'
                self.elapsed = 0.0
        elif self.state == 'turn':
            msg.angular.z = 1.57  # 旋转 ~90°/s
            if self.elapsed > 1.0:
                self.state = 'forward'
                self.elapsed = 0.0

        self.publisher.publish(msg)
```

#### 11.5.3 TF2 坐标变换

TF2 是 ROS2 的坐标变换库，管理机器人各部件之间的空间关系：

```bob
┌─────────────────────────────────────────────┐
│            TF2 坐标变换树                   │
│                                             │
│              map                            │
│               │                             │
│          ┌────▼────┐                        │
│          │  odom   │                        │
│          └────┬────┘                        │
│               │                             │
│          ┌────▼──────────┐                  │
│          │  "base_link"  │                  │
│          └┬──────┬───────┘                  │
│           │      │                          │
│     ┌─────▼──┐ ┌─▼──────────┐              │
│     │"laser" │ │"camera_link"│              │
│     └────────┘ └─────────────┘              │
└─────────────────────────────────────────────┘
```


**图 11-3** 上图直观呈现了 TF2 坐标变换的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch11-3 上图直观呈现了 TF2 坐标变换的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

```python
import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

class OdomPublisher(Node):
    def __init__(self):
        super().__init__('odom_publisher')

        self.tf_broadcaster = TransformBroadcaster(self)
        self.timer = self.create_timer(0.02, self.publish_transform)  # 50 Hz

    def publish_transform(self):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        # 设置位移和旋转（根据里程计数据）
        t.transform.translation.x = 1.0
        t.transform.translation.y = 0.0
        t.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(t)
```

#### 11.5.4 导航栈（Nav2）简介

Nav2 是 ROS2 的标准导航框架，提供完整的自主导航能力：

```bob
┌───────────────────────────────────────────────────┐
│                Nav2 导航栈架构                     │
│                                                   │
│  ┌────────────┐    ┌──────────────┐               │
│  │  激光雷达  │───►│  地图构建    │               │
│  │  IMU      │    │ "SLAM/AMCL"  │               │
│  └────────────┘    └──────┬───────┘               │
│                           │                       │
│                    ┌──────▼───────┐                │
│  目标点 ─────────►│  路径规划    │                │
│                    │  Planner     │                │
│                    └──────┬───────┘                │
│                           │                       │
│                    ┌──────▼───────┐                │
│                    │  路径跟踪    │                │
│                    │  Controller  │                │
│                    └──────┬───────┘                │
│                           │                       │
│                    ┌──────▼───────┐                │
│                    │ "cmd_vel"    │                │
│                    │  运动控制    │                │
│                    └──────────────┘                │
└───────────────────────────────────────────────────┘
```


**图 11-4** 上图以框图形式描绘了导航栈（Nav2）简介的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch11-4 上图以框图形式描绘了导航栈（Nav2）简介的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

---

### 11.6 micro-ROS：嵌入式系统接入 ROS2

#### 11.6.1 为什么需要 micro-ROS


**表 11-3** 传统 ROS2 节点运行在 Linux 等完整操作系统上，资源需求较高（RAM > 256MB）。而机器人的底层控制器（如 STM32）通常只有几十 KB RAM。micro-ROS 填补了这一鸿沟：
<!-- tab:ch11-3 传统 ROS2 节点运行在 Linux 等完整操作系统上，资源需求较高（RAM > 256MB）。而机器人的底层控制器（如 STM32）通常只有几十 KB RAM。micro-ROS 填补了这一鸿沟： -->

| 特性 | ROS2（标准） | micro-ROS |
|------|-------------|-----------|
| 目标平台 | Linux, Windows, macOS | MCU (STM32, ESP32, NXP) |
| 最低 RAM | ~256 MB | ~10 KB |
| RTOS | 非必需 | FreeRTOS, Zephyr, NuttX |
| DDS 实现 | Fast DDS, Cyclone DDS | Micro XRCE-DDS |
| 通信方式 | UDP, TCP, 共享内存 | UART, USB, WiFi, ETH |

上表对为什么需要 micro-ROS 中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

#### 11.6.2 micro-ROS 架构

```bob
┌────────────────────────────────────────────────────────────────────┐
│                     micro-ROS 系统架构                             │
│                                                                    │
│  ┌──────────────────────┐          ┌──────────────────────────┐    │
│  │     MCU 端           │          │        Linux 端          │    │
│  │  ┌────────────────┐  │          │  ┌────────────────────┐  │    │
│  │  │  用户应用       │  │          │  │   ROS2 节点        │  │    │
│  │  │ "Publisher/"    │  │          │  │  导航, 感知, 决策  │  │    │
│  │  │ "Subscriber"   │  │          │  └─────────┬──────────┘  │    │
│  │  └───────┬────────┘  │          │            │             │    │
│  │          │            │          │  ┌─────────▼──────────┐  │    │
│  │  ┌───────▼────────┐  │          │  │   micro-ROS Agent  │  │    │
│  │  │  micro-ROS     │  │   UART   │  │  "（DDS 网关）"     │  │    │
│  │  │  Client Library │  │◄────────►│  │  XRCE-DDS Agent   │  │    │
│  │  └───────┬────────┘  │   WiFi   │  └─────────┬──────────┘  │    │
│  │          │            │   USB    │            │             │    │
│  │  ┌───────▼────────┐  │          │  ┌─────────▼──────────┐  │    │
│  │  │  Micro XRCE-DDS│  │          │  │     Fast DDS       │  │    │
│  │  │  Client        │  │          │  │   "（标准 DDS）"   │  │    │
│  │  └───────┬────────┘  │          │  └────────────────────┘  │    │
│  │          │            │          │                          │    │
│  │  ┌───────▼────────┐  │          │                          │    │
│  │  │  FreeRTOS       │  │          │                          │    │
│  │  │  + HAL 驱动     │  │          │                          │    │
│  │  └────────────────┘  │          │                          │    │
│  └──────────────────────┘          └──────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
```


**图 11-5** 该框图展示了 micro-ROS 架构的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch11-5 该框图展示了 micro-ROS 架构的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

核心组件说明：

- **micro-ROS Client Library**：rcl（ROS Client Library）的轻量级实现，提供与标准 ROS2 兼容的 API；
- **Micro XRCE-DDS**：DDS 的极小资源实现，MCU 端运行 Client，Linux 端运行 Agent；
- **micro-ROS Agent**：运行在 Linux 端的网关程序，将 XRCE-DDS 消息转换为标准 DDS 消息，使 MCU 节点对 ROS2 网络可见。

#### 11.6.3 支持的 MCU 平台

**表 11-4** 支持的 MCU 平台
<!-- tab:ch11-4 支持的 MCU 平台 -->

| 平台 | 芯片示例 | 传输方式 | RTOS |
|------|----------|----------|------|
| STM32 | F4, F7, H7, L4 | UART, USB, ETH | FreeRTOS |
| ESP32 | ESP32, ESP32-S3 | WiFi, UART | FreeRTOS |
| NXP | i.MX RT | USB, ETH | Zephyr |
| Teensy | 4.0, 4.1 | USB | NuttX |
| Raspberry Pi Pico | RP2040 | USB, UART | FreeRTOS |

---

### 11.7 micro-ROS 实战：STM32 接入 ROS2

#### 11.7.1 开发环境准备

```bash
# 1. 确保已安装 ROS2 Humble
source /opt/ros/humble/setup.bash

# 2. 安装 micro-ROS 工具
mkdir -p ~/microros_ws/src
cd ~/microros_ws
git clone -b humble https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup
colcon build
source install/setup.bash

# 3. 创建 micro-ROS Agent
ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh
```

#### 11.7.2 STM32 CubeMX 项目配置

使用 `micro_ros_stm32cubemx_utils` 将 micro-ROS 集成到 CubeMX 项目中：

```bash
# 在 CubeMX 项目根目录下
git clone https://github.com/micro-ROS/micro_ros_stm32cubemx_utils.git
```

CubeMX 配置要点：

1. **串口配置**：启用 USART（如 USART2），波特率 115200，DMA 收发；
2. **FreeRTOS**：启用 CMSIS-RTOS V2，创建默认任务；
3. **堆大小**：micro-ROS 需要较大堆（建议 ≥ 30KB）；
4. **时钟**：确保系统时钟稳定（HSE + PLL → 72MHz 或更高）。

#### 11.7.3 micro-ROS Publisher 实现

在 STM32 上发布传感器数据到 ROS2：

```c
/* main.c - micro-ROS Publisher 示例 */
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <std_msgs/msg/int32.h>
#include <std_msgs/msg/float32.h>

// micro-ROS 对象
rcl_publisher_t publisher;
std_msgs__msg__Float32 msg;
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rcl_timer_t timer;

// 定时回调：每 100ms 发布一次传感器数据
void timer_callback(rcl_timer_t * timer, int64_t last_call_time) {
    (void)last_call_time;
    if (timer != NULL) {
        // 读取 ADC 传感器值（示例）
        msg.data = read_adc_voltage();  // 用户实现的 ADC 读取函数
        rcl_publish(&publisher, &msg, NULL);
    }
}

// FreeRTOS 任务：micro-ROS 主循环
void microros_task(void *argument) {
    // 1. 初始化传输层（UART）
    rmw_uros_set_custom_transport(
        true, (void *)&huart2,
        cubemx_transport_open,
        cubemx_transport_close,
        cubemx_transport_write,
        cubemx_transport_read);

    // 2. 等待 Agent 连接
    while (rmw_uros_ping_agent(1000, 3) != RMW_RET_OK) {
        // Agent 未连接，等待重试
    }

    // 3. 初始化 micro-ROS
    allocator = rcl_get_default_allocator();
    rclc_support_init(&support, 0, NULL, &allocator);
    rclc_node_init_default(&node, "stm32_sensor", "", &support);

    // 4. 创建 Publisher
    rclc_publisher_init_default(
        &publisher, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float32),
        "sensor_voltage");

    // 5. 创建定时器（100ms 周期）
    rclc_timer_init_default(&timer, &support,
        RCL_MS_TO_NS(100), timer_callback);

    // 6. 创建执行器并添加定时器
    rclc_executor_init(&executor, &support.context, 1, &allocator);
    rclc_executor_add_timer(&executor, &timer);

    // 7. 主循环
    while (1) {
        rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
        osDelay(10);
    }
}
```

#### 11.7.4 micro-ROS Subscriber 实现

从 ROS2 接收控制命令（如电机速度）：

```c
rcl_subscription_t subscriber;
geometry_msgs__msg__Twist cmd_vel_msg;

void cmd_vel_callback(const void * msgin) {
    const geometry_msgs__msg__Twist * msg =
        (const geometry_msgs__msg__Twist *)msgin;

    float linear_x = msg->linear.x;   // 前进速度
    float angular_z = msg->angular.z;  // 旋转速度

    // 差速驱动计算
    float left_speed  = linear_x - angular_z * WHEEL_BASE / 2.0f;
    float right_speed = linear_x + angular_z * WHEEL_BASE / 2.0f;

    // 设置电机 PWM（调用前几章的电机驱动函数）
    set_motor_speed(MOTOR_LEFT, left_speed);
    set_motor_speed(MOTOR_RIGHT, right_speed);
}

// 在 microros_task 中添加：
rclc_subscription_init_default(
    &subscriber, &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
    "cmd_vel");
rclc_executor_add_subscription(
    &executor, &subscriber, &cmd_vel_msg,
    &cmd_vel_callback, ON_NEW_DATA);
```

#### 11.7.5 运行与调试

```bash
# 终端1：启动 micro-ROS Agent（通过 UART）
ros2 run micro_ros_agent micro_ros_agent serial \
  --dev /dev/ttyUSB0 --baudrate 115200

# 终端2：查看 STM32 发布的话题
ros2 topic list
ros2 topic echo /sensor_voltage

# 终端3：向 STM32 发送控制命令
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5}, angular: {z: 0.0}}"
```

常见问题排查：

**表 11-5** 运行与调试
<!-- tab:ch11-5 运行与调试 -->

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| Agent 连接失败 | UART 配置错误 | 检查波特率、TX/RX 引脚 |
| 话题不可见 | Domain ID 不匹配 | 确保 Agent 和 ROS2 使用相同 Domain ID |
| 数据丢失 | QoS 不匹配 | 统一 Publisher 和 Subscriber 的 QoS 设置 |
| 内存不足 | 堆太小 | 增大 FreeRTOS 堆至 30KB+ |
| 时间同步 | MCU 时钟漂移 | 启用 micro-ROS 时间同步功能 |

---

### 11.8 综合案例：基于 ROS2 + micro-ROS 的机器人系统

#### 11.8.1 系统架构

```bob
┌──────────────────────────────────────────────────────────────────────┐
│                  ROS2 + micro-ROS 机器人系统架构                     │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                    Linux 上位机 (ROS2)                     │      │
│  │                                                            │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │      │
│  │  │ 导航节点 │  │ SLAM 节点│  │ 决策节点 │  │ RViz2     │  │      │
│  │  │  Nav2    │  │ Cartogra │  │ 行为树   │  │ 可视化    │  │      │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────────┘  │      │
│  │       │             │             │                        │      │
│  │       └──────┬──────┴─────────────┘                        │      │
│  │              │                                             │      │
│  │  ┌───────────▼──────────────┐                              │      │
│  │  │   micro-ROS Agent       │                              │      │
│  │  │  "XRCE-DDS ←→ FastDDS"  │                              │      │
│  │  └───────────┬──────────────┘                              │      │
│  └──────────────┼─────────────────────────────────────────────┘      │
│                 │ UART                                               │
│  ┌──────────────▼─────────────────────────────────────────────┐      │
│  │               STM32 底盘控制器 (micro-ROS)                 │      │
│  │                                                            │      │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │      │
│  │  │  编码器读取  │  │  电机 PWM    │  │  IMU 数据采集    │  │      │
│  │  │  里程计计算  │  │  PID 控制    │  │  姿态解算        │  │      │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │      │
│  │         │                 │                    │            │      │
│  │  ┌──────▼─────────────────▼────────────────────▼─────────┐  │      │
│  │  │              FreeRTOS + HAL 驱动                       │  │      │
│  │  └───────────────────────────────────────────────────────┘  │      │
│  └─────────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────┘
```


**图 11-6** 上图直观呈现了系统架构的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch11-6 上图直观呈现了系统架构的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

#### 11.8.2 话题通信设计

**表 11-6** 话题通信设计
<!-- tab:ch11-6 话题通信设计 -->

| 话题名称 | 消息类型 | 方向 | 频率 | 说明 |
|---------|---------|------|------|------|
| `/cmd_vel` | `geometry_msgs/Twist` | Linux → STM32 | 10 Hz | 运动控制指令 |
| `/odom` | `nav_msgs/Odometry` | STM32 → Linux | 50 Hz | 里程计数据 |
| `/imu` | `sensor_msgs/Imu` | STM32 → Linux | 100 Hz | IMU 原始数据 |
| `/battery` | `std_msgs/Float32` | STM32 → Linux | 1 Hz | 电池电压 |
| `/motor_status` | 自定义 | STM32 → Linux | 10 Hz | 电机状态反馈 |

通过上表的对比可以看出，不同方案在话题名称、消息类型、方向等等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

#### 11.8.3 STM32 底盘节点核心代码

```c
/* chassis_node.c - 底盘控制 micro-ROS 节点 */

#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <geometry_msgs/msg/twist.h>
#include <nav_msgs/msg/odometry.h>
#include <sensor_msgs/msg/imu.h>

// 全局对象
rcl_subscription_t cmd_vel_sub;
rcl_publisher_t odom_pub;
rcl_publisher_t imu_pub;
geometry_msgs__msg__Twist cmd_vel_msg;
nav_msgs__msg__Odometry odom_msg;
sensor_msgs__msg__Imu imu_msg;

// 接收速度命令 → 差速控制
void cmd_vel_callback(const void * msgin) {
    const geometry_msgs__msg__Twist * twist = msgin;
    chassis_set_velocity(twist->linear.x, twist->angular.z);
}

// 50Hz：读取编码器 → 计算里程计 → 发布 odom
void odom_timer_callback(rcl_timer_t * timer, int64_t last_call) {
    (void)last_call;
    encoder_update();  // 读取编码器脉冲

    odom_msg.header.stamp = get_ros_time();
    odom_msg.pose.pose.position.x = odometry.x;
    odom_msg.pose.pose.position.y = odometry.y;
    odom_msg.twist.twist.linear.x = odometry.vx;
    odom_msg.twist.twist.angular.z = odometry.wz;

    rcl_publish(&odom_pub, &odom_msg, NULL);
}

// 100Hz：读取 IMU → 发布
void imu_timer_callback(rcl_timer_t * timer, int64_t last_call) {
    (void)last_call;
    imu_read(&imu_data);  // 读取 MPU6050/ICM20948

    imu_msg.header.stamp = get_ros_time();
    imu_msg.angular_velocity.x = imu_data.gyro_x;
    imu_msg.angular_velocity.y = imu_data.gyro_y;
    imu_msg.angular_velocity.z = imu_data.gyro_z;
    imu_msg.linear_acceleration.x = imu_data.accel_x;
    imu_msg.linear_acceleration.y = imu_data.accel_y;
    imu_msg.linear_acceleration.z = imu_data.accel_z;

    rcl_publish(&imu_pub, &imu_msg, NULL);
}

void microros_chassis_task(void *arg) {
    // 初始化传输层
    rmw_uros_set_custom_transport(true, (void *)&huart2,
        cubemx_transport_open, cubemx_transport_close,
        cubemx_transport_write, cubemx_transport_read);

    // 等待 Agent
    while (rmw_uros_ping_agent(1000, 3) != RMW_RET_OK) {
        osDelay(100);
    }

    // 初始化节点
    allocator = rcl_get_default_allocator();
    rclc_support_init(&support, 0, NULL, &allocator);
    rclc_node_init_default(&node, "chassis_controller", "", &support);

    // 创建 Subscriber 和 Publisher
    rclc_subscription_init_default(&cmd_vel_sub, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist), "cmd_vel");
    rclc_publisher_init_default(&odom_pub, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(nav_msgs, msg, Odometry), "odom");
    rclc_publisher_init_default(&imu_pub, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Imu), "imu");

    // 创建定时器
    rcl_timer_t odom_timer, imu_timer;
    rclc_timer_init_default(&odom_timer, &support, RCL_MS_TO_NS(20), odom_timer_callback);
    rclc_timer_init_default(&imu_timer, &support, RCL_MS_TO_NS(10), imu_timer_callback);

    // 执行器
    rclc_executor_t executor;
    rclc_executor_init(&executor, &support.context, 3, &allocator);
    rclc_executor_add_subscription(&executor, &cmd_vel_sub,
        &cmd_vel_msg, &cmd_vel_callback, ON_NEW_DATA);
    rclc_executor_add_timer(&executor, &odom_timer);
    rclc_executor_add_timer(&executor, &imu_timer);

    while (1) {
        rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
        osDelay(1);
    }
}
```

#### 11.8.4 上位机 ROS2 启动配置

```python
# launch/robot_system.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # micro-ROS Agent
        Node(
            package='micro_ros_agent',
            executable='micro_ros_agent',
            arguments=['serial', '--dev', '/dev/ttyUSB0', '-b', '115200'],
            name='micro_ros_agent',
        ),
        # 导航
        Node(
            package='nav2_bringup',
            executable='bringup_launch.py',
            name='nav2',
        ),
        # 可视化
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', 'config/robot.rviz'],
        ),
    ])
```

#### 11.8.5 ros2_control：标准化硬件抽象与控制框架

`ros2_control` 是 ROS2 的标准硬件抽象和控制器管理框架，为从 STM32 底层到上层控制算法之间提供**统一接口**。它是打通嵌入式驱动与高层控制（PID、MPC、Nav2）的关键桥梁。

**为什么需要 ros2_control**：

在没有 ros2_control 时，每个机器人项目都需要自己编写控制循环、硬件通信和话题接口——代码难以复用。ros2_control 将这些抽象为标准化框架：

```bob
┌─────────────────────────────────────────────────────────────┐
│              ros2_control 架构                               │
│                                                             │
│  ┌──── 用户空间（可切换） ───────────────────────────────┐  │
│  │                                                       │  │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────┐ │  │
│  │  │ DiffDrive     │  │ JointTrajectory│  │ Cartesian │ │  │
│  │  │ Controller    │  │ Controller    │  │ Controller│ │  │
│  │  └───────┬───────┘  └───────┬───────┘  └─────┬─────┘ │  │
│  └──────────┼──────────────────┼────────────────┼────────┘  │
│             │ command/state    │                │            │
│  ┌──────────▼──────────────────▼────────────────▼────────┐  │
│  │              Controller Manager                       │  │
│  │       (加载/卸载/切换控制器，管理控制循环)             │  │
│  └──────────────────────┬────────────────────────────────┘  │
│                         │ Hardware Interface                │
│  ┌──────────────────────▼────────────────────────────────┐  │
│  │            Hardware Components                        │  │
│  │  ┌────────────────┐  ┌──────────────┐  ┌───────────┐ │  │
│  │  │ SystemInterface│  │ SensorIntf   │  │ ActuatorI │ │  │
│  │  │ (差速底盘)     │  │ (IMU/编码器) │  │ (单电机)  │ │  │
│  │  └────────────────┘  └──────────────┘  └───────────┘ │  │
│  └──────────────────────┬────────────────────────────────┘  │
│                         │ Serial/CAN/SPI/micro-ROS          │
│  ┌──────────────────────▼────────────────────────────────┐  │
│  │                  物理硬件                              │  │
│  │  STM32 + 电机驱动 + 编码器 + IMU                      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```


**图 11-7** 上图以框图形式描绘了 ros2_control：标准化硬件抽象与控制框架的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch11-7 上图以框图形式描绘了 ros2_control：标准化硬件抽象与控制框架的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

**核心概念**：

**表 11-7** 
<!-- tab:ch11-7  -->

| 组件 | 职责 | 类比 |
|------|------|------|
| **Controller Manager** | 加载/管理控制器，驱动控制循环 | 操作系统的进程调度器 |
| **Controller** | 实现具体控制算法（差速/关节轨迹/力矩） | 应用层程序 |
| **Hardware Interface** | 抽象底层硬件的 read/write 接口 | 设备驱动 |
| **State Interface** | 硬件公开的只读数据（位置/速度/力） | 传感器输入 |
| **Command Interface** | 硬件接收的控制指令（速度/位置/力矩） | 执行器输出 |

**URDF 中声明 ros2_control 硬件接口**：

```xml
<!-- robot.urdf.xacro 中的 ros2_control 标签 -->
<ros2_control name="DiffDriveSystem" type="system">
  <hardware>
    <!-- 指定硬件接口插件 -->
    <plugin>my_robot_hardware/DiffDriveHardware</plugin>
    <param name="serial_port">/dev/ttyUSB0</param>
    <param name="baud_rate">115200</param>
  </hardware>
  
  <!-- 左轮关节 -->
  <joint name="left_wheel_joint">
    <command_interface name="velocity">
      <param name="min">-10.0</param>
      <param name="max">10.0</param>
    </command_interface>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
  </joint>
  
  <!-- 右轮关节 -->
  <joint name="right_wheel_joint">
    <command_interface name="velocity">
      <param name="min">-10.0</param>
      <param name="max">10.0</param>
    </command_interface>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
  </joint>
</ros2_control>
```

**实现自定义 Hardware Interface（差速底盘）**：

```cpp
// diff_drive_hardware.hpp
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"

class DiffDriveHardware : public hardware_interface::SystemInterface {
public:
    // 初始化：解析 URDF 参数，打开串口
    CallbackReturn on_init(
        const hardware_interface::HardwareInfo & info) override
    {
        if (hardware_interface::SystemInterface::on_init(info) 
            != CallbackReturn::SUCCESS) {
            return CallbackReturn::ERROR;
        }
        
        // 从 URDF 参数获取串口配置
        serial_port_ = info_.hardware_parameters["serial_port"];
        baud_rate_ = std::stoi(
            info_.hardware_parameters["baud_rate"]);
        
        // 初始化状态和命令向量
        hw_positions_.resize(2, 0.0);   // 左右轮位置
        hw_velocities_.resize(2, 0.0);  // 左右轮速度
        hw_commands_.resize(2, 0.0);    // 左右轮速度命令
        
        return CallbackReturn::SUCCESS;
    }

    // 导出状态接口
    std::vector<hardware_interface::StateInterface>
    export_state_interfaces() override {
        std::vector<hardware_interface::StateInterface> interfaces;
        interfaces.emplace_back("left_wheel_joint", "position",
                                &hw_positions_[0]);
        interfaces.emplace_back("left_wheel_joint", "velocity",
                                &hw_velocities_[0]);
        interfaces.emplace_back("right_wheel_joint", "position",
                                &hw_positions_[1]);
        interfaces.emplace_back("right_wheel_joint", "velocity",
                                &hw_velocities_[1]);
        return interfaces;
    }

    // 导出命令接口
    std::vector<hardware_interface::CommandInterface>
    export_command_interfaces() override {
        std::vector<hardware_interface::CommandInterface> interfaces;
        interfaces.emplace_back("left_wheel_joint", "velocity",
                                &hw_commands_[0]);
        interfaces.emplace_back("right_wheel_joint", "velocity",
                                &hw_commands_[1]);
        return interfaces;
    }

    // 读取硬件状态（每个控制周期调用）
    return_type read(const rclcpp::Time &,
                     const rclcpp::Duration &) override {
        // 从串口/micro-ROS 读取编码器数据
        // serial_.read(encoder_data);
        // hw_positions_[0] = encoder_to_rad(left_ticks);
        // hw_velocities_[0] = compute_velocity(left_ticks, dt);
        return return_type::OK;
    }

    // 写入控制命令（每个控制周期调用）
    return_type write(const rclcpp::Time &,
                      const rclcpp::Duration &) override {
        // 将速度命令发送到 STM32
        // serial_.write(format_command(
        //     hw_commands_[0], hw_commands_[1]));
        return return_type::OK;
    }

private:
    std::string serial_port_;
    int baud_rate_;
    std::vector<double> hw_positions_;
    std::vector<double> hw_velocities_;
    std::vector<double> hw_commands_;
};

// 注册为插件
#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(DiffDriveHardware,
                       hardware_interface::SystemInterface)
```

**ros2_control 与 micro-ROS 的桥接方案**：

```bob
┌────────────────────────────────────────────────────────┐
│      ros2_control ↔ micro-ROS 桥接架构                 │
│                                                        │
│  ┌────────────────────────────────────────────┐        │
│  │  ROS2 上位机                               │        │
│  │                                            │        │
│  │  Controller Manager                        │        │
│  │       │                                    │        │
│  │  DiffDrive Controller                      │        │
│  │       │                                    │        │
│  │  Hardware Interface                        │        │
│  │       │                                    │        │
│  │  方案A: 串口协议          方案B: Topic桥接 │        │
│  │  ┌──────────────┐   ┌──────────────────┐   │        │
│  │  │ Serial R/W   │   │ Sub: /wheel_fb   │   │        │
│  │  │ 自定义帧协议 │   │ Pub: /wheel_cmd  │   │        │
│  │  └──────┬───────┘   └────────┬─────────┘   │        │
│  └─────────┼────────────────────┼─────────────┘        │
│            │ UART               │ micro-ROS Agent       │
│  ┌─────────▼────────────────────▼─────────────┐        │
│  │  STM32 (micro-ROS / FreeRTOS)              │        │
│  │  编码器 → 里程计 → 发布 /wheel_fb          │        │
│  │  订阅 /wheel_cmd → PID → PWM → 电机       │        │
│  └────────────────────────────────────────────┘        │
└────────────────────────────────────────────────────────┘
```


**图 11-8** 该框图展示了 ros2_control：标准化硬件抽象与控制框架的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch11-8 该框图展示了 ros2_control：标准化硬件抽象与控制框架的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

- **方案 A（串口协议）**：Hardware Interface 直接通过串口与 STM32 通信，延迟低、控制紧密，但需要自定义帧协议

- **方案 B（Topic 桥接）**：Hardware Interface 通过 ROS2 Topic 与 micro-ROS 通信，灵活但多一层抽象

**ros2_control 配置（YAML）**：

```yaml
# ros2_controllers.yaml
controller_manager:
  ros__parameters:
    update_rate: 50  # Hz，控制循环频率

    diff_drive_controller:
      type: diff_drive_controller/DiffDriveController

    joint_state_broadcaster:
      type: joint_state_broadcaster/JointStateBroadcaster

diff_drive_controller:
  ros__parameters:
    left_wheel_names: ["left_wheel_joint"]
    right_wheel_names: ["right_wheel_joint"]
    wheel_separation: 0.26       # 轮距 (m)
    wheel_radius: 0.033          # 轮半径 (m)
    
    # 速度限制
    linear.x.max_velocity: 0.5
    linear.x.min_velocity: -0.5
    angular.z.max_velocity: 2.0
    
    # 里程计
    odom_frame_id: odom
    base_frame_id: base_link
    publish_rate: 50.0
    
    # TF 发布
    enable_odom_tf: true
```

**启动 ros2_control**：

```python
# launch/robot_control.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    robot_description = ParameterValue(
        Command(['xacro ', 'urdf/robot.urdf.xacro']),
        value_type=str)

    return LaunchDescription([
        # Robot State Publisher（发布 URDF + TF）
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}]),

        # Controller Manager（加载硬件接口和控制器）
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            parameters=['config/ros2_controllers.yaml',
                        {'robot_description': robot_description}]),

        # 启动控制器
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['diff_drive_controller']),
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster']),
    ])
```

**ros2_control 与课程知识体系的关系**：

**表 11-8** 
<!-- tab:ch11-8  -->

| 课程章节 | ros2_control 中的对应 |
|---------|----------------------|
| 第6章 电机驱动 | Hardware Interface 的 `write()` 实现 |
| 第8章 PID 控制 | Controller 插件（如 pid_controller） |
| 第9章 传感器融合 | Hardware Interface 的 `read()` + State Interface |
| 第11章 micro-ROS | Hardware Interface 的底层通信层 |
| 第14章 Nav2 | DiffDriveController 接收 cmd_vel |

---

### 11.9 本章小结与拓展资源

#### 11.9.1 关键知识点回顾

本章从 ROS2 基础概念出发，逐步深入到 micro-ROS 嵌入式集成和 ros2_control 硬件抽象框架，建立了从 MCU 到完整机器人系统的技术路径：

1. **ROS2 核心概念**：节点、话题、服务、动作构成分布式计算图，DDS 提供工业级通信；
2. **ROS2 编程**：Python 和 C++ 双语言 Publisher/Subscriber/Service 编程范式；
3. **机器人控制**：cmd_vel 运动控制、TF2 坐标变换、Nav2 导航栈；
4. **micro-ROS**：通过 XRCE-DDS 和 Agent，使 STM32 等 MCU 成为 ROS2 网络的一等公民；
5. **ros2_control**：标准化硬件抽象框架，通过 Controller Manager 和 Hardware Interface 统一管理控制器与硬件；
6. **系统集成**：底盘控制（micro-ROS）+ 硬件抽象（ros2_control）+ 上位机感知决策（ROS2）的完整架构。

#### 11.9.2 推荐学习资源

**表 11-9** 推荐学习资源
<!-- tab:ch11-9 推荐学习资源 -->

| 资源 | 说明 |
|------|------|
| [ROS2 官方文档](https://docs.ros.org/en/humble/) | 权威参考，含完整 API 文档和教程 |
| [micro-ROS 官网](https://micro.ros.org/) | micro-ROS 项目主页，含快速入门指南 |
| [Navigation2](https://navigation.ros.org/) | Nav2 导航栈文档 |
| [The Construct](https://www.theconstructsim.com/) | 在线 ROS2 学习平台，含仿真环境 |
| [micro-ROS STM32 示例](https://github.com/micro-ROS/micro_ros_stm32cubemx_utils) | STM32 集成工具和示例代码 |
| 《Programming Robots with ROS2》 | O'Reilly 出版，ROS2 编程权威指南 |

上表对推荐学习资源的核心信息进行了结构化整理，读者可根据需要快速查阅相关内容。

#### 11.9.3 课后练习

1. **基础练习**：在 ROS2 中创建一个 Python 包，实现温度传感器的 Publisher 和数据记录的 Subscriber。
2. **进阶练习**：使用 Turtlesim 实现一个自定义的控制节点，让海龟沿圆形轨迹运动，同时记录其轨迹。
3. **综合练习**：在 STM32 上使用 micro-ROS 实现一个节点，通过 ADC 读取电位器值并发布为 `std_msgs/Float32` 话题。在 Linux 端编写一个 Subscriber 节点接收并打印数据。
4. **挑战练习**：设计一个完整的 micro-ROS + ROS2 系统，STM32 作为底盘控制器（接收 cmd_vel，发布里程计），Linux 端运行键盘遥控节点。实现从键盘输入到电机转动的完整数据通路。


---

### 11.10 本章测验

<div id="exam-meta" data-exam-id="chapter11" data-exam-title="第十一章 ROS 程序设计测验" style="display:none"></div>

<!-- mkdocs-quiz intro -->

<quiz>
1) ROS2 中 Topic 和 Service 的核心区别是什么？
- [x] Topic 是异步发布-订阅，Service 是同步请求-响应
- [ ] Topic 只能传输字符串，Service 可以传输任意类型
- [ ] Service 的性能优于 Topic
- [ ] Topic 必须使用 TCP，Service 使用 UDP

Topic 基于发布-订阅模式，是一对多的异步通信，适合持续数据流（如传感器数据）。Service 是一对一的同步请求-响应，适合偶发的查询或命令操作。两者底层都走 DDS 协议。
</quiz>

<quiz>
2) micro-ROS 在 STM32 上运行时，以下哪项描述是正确的？
- [x] micro-ROS Agent 运行在 Linux 端，充当 MCU 与 ROS2 网络的桥梁
- [ ] micro-ROS 直接运行完整的 DDS 栈，不需要 Agent
- [ ] micro-ROS 只支持 Topic，不支持 Service 和 Action
- [ ] micro-ROS 需要在 MCU 上运行 Linux 操作系统

micro-ROS 使用精简的 Micro XRCE-DDS 客户端运行在 MCU（可运行在 FreeRTOS 或裸机上），通过串口/UDP 与 Linux 端的 micro-ROS Agent 通信，Agent 再桥接到标准 DDS 网络。它支持 Topic、Service 和 Parameter 等核心功能。
</quiz>

<quiz>
3) ROS2 中 QoS（Quality of Service）策略的 Reliability 参数有哪两种选项？
- [x] RELIABLE（可靠传输）和 BEST_EFFORT（尽力传输）
- [ ] SYNCHRONOUS 和 ASYNCHRONOUS
- [ ] TCP 模式和 UDP 模式
- [ ] HIGH_PRIORITY 和 LOW_PRIORITY

RELIABLE 保证消息到达（类似 TCP 重传机制），适合命令和配置；BEST_EFFORT 不保证到达但延迟低，适合高频传感器数据。发布者和订阅者的 QoS 需兼容才能正常通信。
</quiz>

<quiz>
4) TF2 坐标变换系统中，以下哪些说法是正确的？
- [x] TF2 维护一棵以 map 或 odom 为根节点的坐标变换树
- [ ] 任意两个坐标系之间可以存在多条变换路径
- [x] Static TF 用于固定不变的变换关系（如 base_link→laser）
- [ ] TF2 只支持二维坐标变换

TF2 要求坐标变换关系构成严格的树结构（任意两帧间只有唯一路径），不允许回路。Static TF 适合刚性安装的传感器外参。TF2 使用四元数表示三维旋转，是完整的 6-DOF 坐标变换系统。
</quiz>

<!-- mkdocs-quiz results -->

---
