---
number headings: first-level 2, start-at 19
---

## 19 第 19 章 课程实验三：多 AGV 调度系统

> 本章以仓储物流场景为背景，在 ROS2 仿真环境中实践多机器人协同调度技术。这是对第 12 章多机器人理论的工程验证，涵盖任务分配、冲突消解、交通管理与系统监控。

### 19.1 项目概述

#### 19.1.1 项目背景

自动导引车（AGV, Automated Guided Vehicle）在现代仓储物流中扮演核心角色。多 AGV 系统需要解决任务分配、路径规划、冲突避免三大核心问题。本实验通过仿真环境搭建一套完整的多 AGV 调度系统。

#### 19.1.2 学习目标

- 理解多 AGV 调度系统架构
- 实现任务分配算法（匈牙利算法/拍卖算法）
- 实现多机器人冲突消解策略
- 使用 ROS2 管理多个机器人实例

#### 19.1.3 系统架构

```bob
+-------------------------------------------------------------------+
|               "多 AGV 调度系统架构"                                 |
+-------------------------------------------------------------------+
|                                                                   |
|  +-----------------------------------------------------------+   |
|  |                   "调度中心（中央服务器）"                    |   |
|  |  +-------------+  +-----------+  +---------------------+  |   |
|  |  | "任务管理器" |  | "路径规划" |  | "交通管理器"         |  |   |
|  |  |  任务队列   |  |  全局地图  |  |  冲突检测与消解     |  |   |
|  |  |  优先级排序 |  |  A* / CBS  |  |  路口互斥锁        |  |   |
|  |  +------+------+  +-----+-----+  +----------+----------+  |   |
|  +---------|---------------|-------------------|--------------+   |
|            |               |                   |                  |
|     "任务分配"        "路径下发"          "通行令牌"               |
|            |               |                   |                  |
|  +---------v---------------v-------------------v--------------+   |
|  |                   "ROS2 通信层（DDS）"                       |   |
|  +----+----------+----------+----------+----------+-----------+   |
|       |          |          |          |          |               |
|  +----v----+ +---v----+ +--v-----+ +--v-----+ +--v-----+        |
|  | "AGV 1" | | "AGV 2"| | "AGV 3"| | "AGV 4"| | "AGV 5"|        |
|  | Nav2    | | Nav2   | | Nav2   | | Nav2   | | Nav2   |        |
|  | 局部避障| | 局部避障| | 局部避障| | 局部避障| | 局部避障|        |
|  +---------+ +--------+ +--------+ +--------+ +--------+        |
+-------------------------------------------------------------------+
```


**图 19-1** 该框图展示了系统架构的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch19-1 该框图展示了系统架构的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

### 19.2 多机器人仿真环境

#### 19.2.1 Launch 文件：多 AGV 启动

```python
"""多 AGV 启动文件"""
from launch import LaunchDescription
from launch.actions import GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import PushRosNamespace
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_dir = get_package_share_directory('agv_simulation')
    nav2_launch = os.path.join(pkg_dir, 'launch', 'single_agv_nav.launch.py')

    agv_configs = [
        {'name': 'agv1', 'x': 0.0, 'y': 0.0, 'yaw': 0.0},
        {'name': 'agv2', 'x': 2.0, 'y': 0.0, 'yaw': 0.0},
        {'name': 'agv3', 'x': 4.0, 'y': 0.0, 'yaw': 0.0},
        {'name': 'agv4', 'x': 0.0, 'y': 3.0, 'yaw': 0.0},
        {'name': 'agv5', 'x': 2.0, 'y': 3.0, 'yaw': 0.0},
    ]

    actions = []
    for cfg in agv_configs:
        group = GroupAction([
            PushRosNamespace(cfg['name']),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(nav2_launch),
                launch_arguments={
                    'namespace': cfg['name'],
                    'x_pose': str(cfg['x']),
                    'y_pose': str(cfg['y']),
                    'yaw': str(cfg['yaw']),
                }.items()
            )
        ])
        actions.append(group)

    return LaunchDescription(actions)
```

#### 19.2.2 仓库地图场景

```bob
+-------+-------+-------+-------+-------+-------+
|       |       |       |       |       |       |
| "货架" | "货架" | "货架" | "货架" | "货架" | "货架" |
| "A1"  | "A2"  | "A3"  | "B1"  | "B2"  | "B3"  |
|       |       |       |       |       |       |
+---+---+---+---+---+---+---+---+---+---+---+---+
    |           |           |           |
    | "通道 1"  | "通道 2"  | "通道 3"  |
    |           |           |           |
+---+---+---+---+---+---+---+---+---+---+---+---+
|       |       |       |       |       |       |
| "货架" | "货架" | "货架" | "货架" | "货架" | "货架" |
| "C1"  | "C2"  | "C3"  | "D1"  | "D2"  | "D3"  |
|       |       |       |       |       |       |
+-------+--+----+-------+-------+----+--+-------+
           |                         |
           +------"主通道"------------+
           |                         |
     +-----+-----+            +-----+-----+
     | "装载区"    |            | "卸载区"    |
     | "Load"     |            | "Unload"   |
     +-----------+            +-----------+
```


**图 19-2** 上图直观呈现了仓库地图场景的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch19-2 上图直观呈现了仓库地图场景的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

### 19.3 任务分配算法

#### 19.3.1 匈牙利算法实现

匈牙利算法求解最优任务-AGV 分配，使总运输距离最小：

```python
import numpy as np
from scipy.optimize import linear_sum_assignment

class TaskAllocator:
    """基于匈牙利算法的任务分配器"""

    def __init__(self):
        self.task_queue = []
        self.agv_states = {}

    def allocate(self, tasks, agv_positions):
        """
        tasks: list of (pick_x, pick_y, drop_x, drop_y, priority)
        agv_positions: dict {agv_id: (x, y)}
        返回: dict {agv_id: task_index}
        """
        n_tasks = len(tasks)
        n_agvs = len(agv_positions)
        agv_ids = list(agv_positions.keys())

        # 构建代价矩阵（距离 + 优先级惩罚）
        cost_matrix = np.zeros((n_agvs, n_tasks))
        for i, agv_id in enumerate(agv_ids):
            ax, ay = agv_positions[agv_id]
            for j, task in enumerate(tasks):
                px, py = task[0], task[1]
                distance = np.sqrt((ax - px)**2 + (ay - py)**2)
                priority_weight = 1.0 / task[4]  # 高优先级 → 低权重
                cost_matrix[i][j] = distance * priority_weight

        # 匈牙利算法求解
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        allocation = {}
        for r, c in zip(row_ind, col_ind):
            allocation[agv_ids[r]] = c

        return allocation
```

#### 19.3.2 拍卖算法实现

去中心化拍卖机制，每个 AGV 对任务出价：

```python
class AuctionAllocator:
    """基于拍卖机制的去中心化任务分配"""

    def __init__(self, epsilon=0.1):
        self.epsilon = epsilon  # 最小加价幅度

    def auction_round(self, tasks, agv_positions):
        """单轮拍卖"""
        n_tasks = len(tasks)
        prices = np.zeros(n_tasks)      # 任务价格
        assignment = {}                  # AGV → 任务
        agv_ids = list(agv_positions.keys())

        unassigned = set(agv_ids)

        while unassigned:
            for agv_id in list(unassigned):
                ax, ay = agv_positions[agv_id]

                # 计算对每个任务的估值（负距离，距离越近估值越高）
                values = []
                for j, task in enumerate(tasks):
                    dist = np.sqrt((ax - task[0])**2 + (ay - task[1])**2)
                    values.append(-dist - prices[j])

                # 选择最优任务
                best_task = np.argmax(values)
                best_value = values[best_task]

                # 计算出价（第二高估值 + epsilon）
                sorted_values = sorted(values, reverse=True)
                bid = prices[best_task] + (sorted_values[0] - sorted_values[1]) + self.epsilon

                # 更新分配
                # 如果该任务已被占用，释放原 AGV
                for other_agv, other_task in list(assignment.items()):
                    if other_task == best_task:
                        del assignment[other_agv]
                        unassigned.add(other_agv)

                assignment[agv_id] = best_task
                prices[best_task] = bid
                unassigned.discard(agv_id)

        return assignment
```

### 19.4 冲突消解策略

#### 19.4.1 基于优先级的路口互斥

```bob
"冲突场景示意：十字路口"

         "AGV 2"
           |
           v
  -----> +---+ ----->
"AGV 1"  | X |  
  -----> +---+ ----->
           |
           v
```


**图 19-3** 上图以框图形式描绘了基于优先级的路口互斥的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch19-3 上图以框图形式描绘了基于优先级的路口互斥的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

```python

import threading
from enum import Enum

class IntersectionManager:
    """路口交通管理器"""

    def __init__(self):
        self.locks = {}  # intersection_id → Lock
        self.queue = {}  # intersection_id → priority queue

    def register_intersection(self, intersection_id):
        self.locks[intersection_id] = threading.Lock()
        self.queue[intersection_id] = []

    def request_passage(self, agv_id, intersection_id, priority):
        """AGV 请求通过路口"""
        lock = self.locks[intersection_id]

        # 尝试获取锁
        acquired = lock.acquire(timeout=0.1)
        if acquired:
            return True  # 允许通过

        # 未获取到锁，加入等待队列
        self.queue[intersection_id].append((priority, agv_id))
        self.queue[intersection_id].sort()  # 按优先级排序
        return False

    def release_passage(self, agv_id, intersection_id):
        """AGV 离开路口，释放通行权"""
        self.locks[intersection_id].release()

        # 通知等待队列中的下一个 AGV
        if self.queue[intersection_id]:
            next_priority, next_agv = self.queue[intersection_id].pop(0)
            return next_agv
        return None
```

#### 19.4.2 CBS 冲突搜索算法

CBS（Conflict-Based Search）是多机器人路径规划的经典算法：

```python
from dataclasses import dataclass
from typing import List, Tuple
import heapq

@dataclass
class Constraint:
    agv_id: str
    position: Tuple[int, int]
    timestep: int

@dataclass
class CBSNode:
    constraints: List[Constraint]
    solution: dict  # agv_id → path
    cost: float

    def __lt__(self, other):
        return self.cost < other.cost

class CBSSolver:
    """CBS 多机器人无冲突路径规划"""

    def __init__(self, grid_map):
        self.grid = grid_map

    def solve(self, starts, goals):
        """
        starts: dict {agv_id: (x, y)}
        goals:  dict {agv_id: (x, y)}
        """
        # 根节点：无约束，各自独立规划
        root = CBSNode(constraints=[], solution={}, cost=0)
        for agv_id in starts:
            path = self.a_star(starts[agv_id], goals[agv_id], [])
            root.solution[agv_id] = path
        root.cost = sum(len(p) for p in root.solution.values())

        open_list = [root]

        while open_list:
            node = heapq.heappop(open_list)

            # 检测冲突
            conflict = self.find_conflict(node.solution)
            if conflict is None:
                return node.solution  # 无冲突，返回解

            agv1, agv2, pos, t = conflict

            # 对冲突双方分别添加约束
            for agv_id in [agv1, agv2]:
                new_constraints = node.constraints + [
                    Constraint(agv_id, pos, t)
                ]
                new_solution = dict(node.solution)

                # 在新约束下重新规划该 AGV 路径
                agv_constraints = [c for c in new_constraints if c.agv_id == agv_id]
                new_path = self.a_star(
                    starts[agv_id], goals[agv_id], agv_constraints
                )

                if new_path is not None:
                    new_solution[agv_id] = new_path
                    child = CBSNode(
                        constraints=new_constraints,
                        solution=new_solution,
                        cost=sum(len(p) for p in new_solution.values())
                    )
                    heapq.heappush(open_list, child)

        return None  # 无解

    def find_conflict(self, solution):
        """检测路径冲突（同一时刻同一位置）"""
        agv_ids = list(solution.keys())
        max_t = max(len(p) for p in solution.values())

        for t in range(max_t):
            positions = {}
            for agv_id in agv_ids:
                path = solution[agv_id]
                pos = path[min(t, len(path) - 1)]
                if pos in positions:
                    return (positions[pos], agv_id, pos, t)
                positions[pos] = agv_id
        return None

    def a_star(self, start, goal, constraints):
        """带时间约束的 A* 搜索（此处省略完整实现）"""
        # 标准 A* 加上时间维度约束检查
        pass
```

### 19.5 调度监控面板

#### 19.5.1 实时状态监控

```python
"""调度监控节点 — 汇总所有 AGV 状态"""
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import json

class DispatchMonitor(Node):
    def __init__(self, agv_names):
        super().__init__('dispatch_monitor')
        self.agv_states = {}

        for name in agv_names:
            self.create_subscription(
                Odometry,
                f'/{name}/odom',
                lambda msg, n=name: self.odom_callback(n, msg),
                10
            )

        self.status_pub = self.create_publisher(String, '/dispatch/status', 10)
        self.create_timer(1.0, self.publish_status)

    def odom_callback(self, agv_name, msg):
        self.agv_states[agv_name] = {
            'x': msg.pose.pose.position.x,
            'y': msg.pose.pose.position.y,
            'vx': msg.twist.twist.linear.x,
            'status': 'moving' if abs(msg.twist.twist.linear.x) > 0.01 else 'idle'
        }

    def publish_status(self):
        status_msg = String()
        status_msg.data = json.dumps(self.agv_states, indent=2)
        self.status_pub.publish(status_msg)

def main():
    rclpy.init()
    agv_names = ['agv1', 'agv2', 'agv3', 'agv4', 'agv5']
    node = DispatchMonitor(agv_names)
    rclpy.spin(node)
```

### 19.6 完整实验流程

#### 19.6.1 实验步骤

```bash
# 步骤 1：启动仓库仿真环境
ros2 launch agv_simulation warehouse.launch.py

# 步骤 2：启动 5 台 AGV
ros2 launch agv_simulation multi_agv.launch.py

# 步骤 3：启动调度中心
ros2 run agv_dispatch dispatch_server

# 步骤 4：启动监控面板
ros2 run agv_dispatch monitor_panel

# 步骤 5：发送任务
ros2 topic pub /dispatch/new_task std_msgs/String \
    '{"pick": "A1", "drop": "Unload", "priority": 1}'
```

#### 19.6.2 实验评分标准

**表 19-1** 实验评分标准
<!-- tab:ch19-1 实验评分标准 -->

| 评分项 | 权重 | 满分条件 |
|--------|------|---------|
| 任务完成率 | 30% | 所有任务在时限内完成 |
| 无冲突运行 | 25% | 全程无碰撞、无死锁 |
| 系统吞吐量 | 20% | 单位时间完成任务数量 |
| 代码质量 | 15% | 架构清晰、注释完整 |
| 实验报告 | 10% | 分析到位、结论准确 |

通过上表的对比可以看出，不同方案在评分项、权重、满分条件等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

### 19.7 本章小结


**表 19-2** 本章通过多 AGV 调度系统实验，综合运用了课程中多个章节的核心技术：
<!-- tab:ch19-2 本章通过多 AGV 调度系统实验，综合运用了课程中多个章节的核心技术： -->

| 技术点 | 对应章节 |
|--------|---------|
| ROS2 命名空间与多实例 | 第9章 ROS 程序设计 |
| Nav2 导航栈 | 第11章 导航与路径规划 |
| 多机器人通信与协同 | 第12章 多机器人系统 |
| 任务分配算法 | 第12章 §12.5 协同算法 |
| 路径规划（A*、CBS） | 第11章 §11.2-11.3 |

上表对本章小结的核心信息进行了结构化整理，读者可根据需要快速查阅相关内容。

### 19.8 本章测验

<div id="exam-meta" data-exam-id="chapter15" data-exam-title="第 19 章 多 AGV 调度实验 测验" style="display:none"></div>

<!-- mkdocs-quiz intro -->

<quiz>
1) 匈牙利算法解决的是哪类优化问题？
- [ ] 最短路径问题
- [x] 二部图最优匹配（最小代价分配）问题
- [ ] 旅行商问题
- [ ] 背包问题

匈牙利算法是求解二部图最大权匹配/最小代价分配的经典多项式时间算法，适用于 AGV-任务的一对一最优分配。
</quiz>

<quiz>
2) 在多 AGV 路口冲突消解中，使用互斥锁的目的是？
- [ ] 加速 AGV 通过路口
- [ ] 提高路径规划效率
- [x] 确保同一时刻只有一台 AGV 占用路口，防止碰撞
- [ ] 均衡各 AGV 的工作负载

互斥锁将路口建模为临界资源，通过串行化通行来消除碰撞风险。
</quiz>

<quiz>
3) CBS（Conflict-Based Search）算法的核心思想是？
- [ ] 所有机器人同时搜索最优路径
- [ ] 使用势场法进行避障
- [x] 先独立规划各机器人路径，检测冲突后通过添加约束分支搜索进行消解
- [ ] 将多机器人问题转化为单机器人多目标问题

CBS 采用两层搜索：高层搜索冲突并分支添加约束，低层在约束下用 A* 为单个机器人重新规划路径。
</quiz>

<quiz>
4) ROS2 中使用命名空间（namespace）管理多 AGV 的主要好处是？
- [ ] 提高消息传输速度
- [ ] 减少内存占用
- [x] 自动隔离各 AGV 的 Topic/Service，避免命名冲突
- [ ] 简化 URDF 模型

命名空间使每个 AGV 的 `/cmd_vel`、`/scan`、`/odom` 等 Topic 自动变为 `/agv1/cmd_vel` 等，实现逻辑隔离。
</quiz>

<quiz>
5) 拍卖算法相比匈牙利算法在多 AGV 调度中的主要优势是？
- [ ] 计算速度更快
- [ ] 一定能找到全局最优解
- [x] 去中心化执行，不依赖中央服务器，适合动态环境
- [ ] 需要的通信带宽更低

拍卖算法可以分布式执行，无需中央节点全局计算，更适合 AGV 动态加入/退出的实际场景。
</quiz>

<!-- mkdocs-quiz results -->
