---
number headings: first-level 2, start-at 14
---

## 14 第 14 章 机器人导航与路径规划

自主导航是移动机器人最核心的能力——在已知或未知环境中，从起点安全、高效地到达目标点。本章从路径规划的基本算法出发，逐步深入到 ROS2 Nav2 导航栈的工程实践，使学生具备为轮式机器人实现完整自主导航的能力。

学习目标：

- 掌握经典路径规划算法（A\*、Dijkstra、RRT）的原理与实现；
- 理解局部规划与避障算法（DWA、TEB）；
- 了解代价地图的构建与使用；
- 掌握 ROS2 Nav2 导航栈的架构与配置；
- 能完成从地图加载到自主导航的完整流程。

---

### 14.1 导航问题概述

#### 14.1.1 自主导航的要素

一个完整的自主导航系统需要回答四个问题：

1. **我在哪？**（定位）——通过 SLAM 或已知地图上的定位（AMCL）；
2. **要去哪？**（目标）——用户指定或任务规划给出的目标位姿；
3. **怎么去？**（全局规划）——在地图上规划从当前位置到目标的路径；
4. **如何走？**（局部规划）——跟踪全局路径、实时避障、控制速度。

```bob
┌──────────────────────────────────────────────────────┐
│                自主导航系统模块                        │
│                                                      │
│  ┌──────────┐                  ┌──────────────┐      │
│  │  定位    │                  │  目标输入    │      │
│  │ AMCL     │                  │  用户/任务   │      │
│  └────┬─────┘                  └──────┬───────┘      │
│       │                               │              │
│       └──────────┬────────────────────┘              │
│                  │                                   │
│           ┌──────▼───────┐                           │
│           │  全局规划    │                           │
│           │ "A* / Dijkstra"│                           │
│           └──────┬───────┘                           │
│                  │ 全局路径                           │
│           ┌──────▼───────┐                           │
│           │  局部规划    │                           │
│           │ "DWA / TEB"  │◄──── 传感器实时数据       │
│           └──────┬───────┘                           │
│                  │ 速度指令                           │
│           ┌──────▼───────┐                           │
│           │  运动控制    │                           │
│           │ "cmd_vel"    │                           │
│           └──────────────┘                           │
└──────────────────────────────────────────────────────┘
```


**图 14-1** 该框图展示了自主导航的要素的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch14-1 该框图展示了自主导航的要素的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

#### 14.1.2 导航与前置章节的关系

**表 14-1** 导航与前置章节的关系
<!-- tab:ch14-1 导航与前置章节的关系 -->

| 依赖章节 | 提供的能力 | 在导航中的角色 |
|---------|-----------|--------------|
| 第8章 机器人运动与电机驱动 | 差速运动学、PWM 控制 | 执行速度指令 |
| 第9章 闭环控制与 PID | 编码器反馈、速度闭环 | 底层速度控制 |
| 第13章 ROS2 程序设计 | 节点、话题、服务、micro-ROS | 通信框架 |
| 第14章 SLAM | 地图构建与定位 | 提供地图和位姿 |

---

### 14.2 全局路径规划算法

全局规划器在整个地图上搜索一条从起点到终点的无碰撞路径。

#### 14.2.1 图搜索基础

路径规划问题可建模为图搜索：将地图离散化为节点（网格或采样点），相邻节点之间建立边（代价为距离或通行难度）。

**Dijkstra 算法**：

- 找到起点到所有节点的最短路径
- 不使用启发信息，向所有方向均匀扩展
- 时间复杂度 $O((V+E)\log V)$（优先队列实现）
- 保证最优解

```text

Dijkstra(start, goal, graph):
  dist[start] = 0

  open_set = PriorityQueue({start: 0})
  

  while open_set is not empty:
    current = open_set.pop_min()
    if current == goal: return path
    
    for neighbor in graph.neighbors(current):
      new_cost = dist[current] + edge_cost(current, neighbor)
      if new_cost < dist[neighbor]:
        dist[neighbor] = new_cost
        parent[neighbor] = current
        open_set.push(neighbor, new_cost)
  
  return failure
```

#### 14.2.2 A\* 算法

A\* 是机器人路径规划中使用最广泛的算法。它在 Dijkstra 的基础上引入启发函数 $h(n)$，优先搜索更可能接近目标的方向。

**核心公式**：

$$
f(n) = g(n) + h(n)
$$

- $g(n)$：从起点到节点 $n$ 的实际代价
- $h(n)$：从节点 $n$ 到目标的启发式估计代价
- $f(n)$：总估计代价

**启发函数的要求**：

- **可容纳性（Admissible）**：$h(n) \leq h^*(n)$，即不高估实际代价——保证找到最优解
- **一致性（Consistent）**：$h(n) \leq c(n,n') + h(n')$——保证不重复搜索

常用启发函数：

**表 14-2** A\* 算法
<!-- tab:ch14-2 A\* 算法 -->

| 启发函数 | 公式 | 适用场景 |
|---------|------|---------|
| 曼哈顿距离 | $\|x_1-x_2\| + \|y_1-y_2\|$ | 4-连通网格 |
| 欧几里得距离 | $\sqrt{(x_1-x_2)^2 + (y_1-y_2)^2}$ | 8-连通网格 |
| 切比雪夫距离 | $\max(\|x_1-x_2\|, \|y_1-y_2\|)$ | 8-连通网格 |

上表对 A\* 算法中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

```bob
┌──────────────────────────────────────────────────────────┐
│           Dijkstra vs A* 搜索对比                         │
│                                                          │
│   Dijkstra（无启发）          A*（有启发）               │
│  ┌─────────────────┐     ┌─────────────────┐            │
│  │ . . . . . . . . │     │ . . . . . . . . │            │
│  │ . # # # # . . . │     │ . # # # # . . . │            │
│  │ . . . . # . . . │     │ . . . . # . . . │            │
│  │ S * * * # * * G │     │ S * * * # . . G │            │
│  │ . * * * # * * . │     │ . . * * # * * . │            │
│  │ . * * * * * * . │     │ . . . * * * . . │            │
│  │ . * * * * * . . │     │ . . . . . . . . │            │
│  │ . . . . . . . . │     │ . . . . . . . . │            │
│  └─────────────────┘     └─────────────────┘            │
│  扩展节点多，搜索慢         扩展节点少，搜索快            │
└──────────────────────────────────────────────────────────┘
```


**图 14-2** 上图直观呈现了 A\* 算法的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch14-2 上图直观呈现了 A\* 算法的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

**A\* Python 实现**：

```python

import heapq

def a_star(grid, start, goal):
    """A* 路径规划算法
    grid: 2D 数组，0=可通行，1=障碍物
    start, goal: (row, col) 元组
    """
    rows, cols = len(grid), len(grid[0])
    
    # 启发函数：欧几里得距离
    def heuristic(a, b):
        return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5
    
    # 8-连通方向
    directions = [(-1,-1),(-1,0),(-1,1),(0,-1),
                  (0,1),(1,-1),(1,0),(1,1)]
    
    open_set = [(0 + heuristic(start, goal), 0, start)]

    g_score = {start: 0}
    parent = {}
    
    while open_set:
        f, g, current = heapq.heappop(open_set)

        
        if current == goal:
            # 回溯路径
            path = []
            while current in parent:
                path.append(current)
                current = parent[current]
            path.append(start)
            return path[::-1]
        
        for dr, dc in directions:
            neighbor = (current[0]+dr, current[1]+dc)
            if (0 <= neighbor[0] < rows and 
                0 <= neighbor[1] < cols and
                grid[neighbor[0]][neighbor[1]] == 0):
                
                # 对角线移动代价为 √2
                move_cost = 1.414 if dr != 0 and dc != 0 else 1.0
                new_g = g + move_cost
                
                if new_g < g_score.get(neighbor, float('inf')):
                    g_score[neighbor] = new_g
                    parent[neighbor] = current
                    f_new = new_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_new, new_g, neighbor))
    
    return None  # 无可达路径
```

#### 14.2.3 A\* 的变体

**表 14-3** A\* 的变体
<!-- tab:ch14-3 A\* 的变体 -->

| 变体 | 改进 | 使用场景 |
|------|------|---------|
| Weighted A\* | $f = g + \epsilon \cdot h$，$\epsilon > 1$ 加速搜索 | 需要快速次优解 |
| Theta\* | 允许非网格方向移动，路径更平滑 | 全向机器人 |
| D\* Lite | 动态地图变化时增量更新路径 | 未知或变化环境 |
| ARA\* | 从高 $\epsilon$ 快速求解，逐步降低至最优 | 时间受限的规划 |

通过上表的对比可以看出，不同方案在变体、改进、使用场景等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

#### 14.2.4 采样规划算法：RRT

**RRT（Rapidly-exploring Random Tree）** 通过随机采样快速探索高维空间，适合复杂环境和高自由度系统。

```text
RRT(start, goal, map, max_iter):
  tree = {start}
  
  for i = 1 to max_iter:
    x_rand = random_sample(map)          # 随机采样
    x_near = nearest(tree, x_rand)       # 找最近节点
    x_new = steer(x_near, x_rand, step)  # 沿方向延伸
    

    if collision_free(x_near, x_new):     # 碰撞检测
      tree.add(x_new)

      tree.add_edge(x_near, x_new)
      
      if distance(x_new, goal) < threshold:
        return extract_path(tree, start, x_new)
  
  return failure
```

#### 14.2.5 RRT\* 算法：渐近最优采样规划

**RRT\*** 是 RRT 的改进版，增加了两个关键操作——**近邻搜索（Near）** 和 **重连接（Rewire）**，使其在采样数趋于无穷时收敛到最优解。

**与 RRT 的核心区别**：

**表 14-4** RRT\* 算法：渐近最优采样规划
<!-- tab:ch14-4 RRT\* 算法：渐近最优采样规划 -->

| 步骤 | RRT | RRT\* |
|------|-----|-------|
| 新节点连接 | 连接到最近节点 | 在近邻集中选代价最小的父节点 |
| 树结构优化 | 无 | 对近邻节点尝试重连接（Rewire） |
| 最优性 | 概率完备但非最优 | **渐近最优** |

**RRT\* Python 完整实现**：

```python
import numpy as np
import matplotlib.pyplot as plt

class RRTStar:
    """RRT* 路径规划算法"""
    
    class Node:
        def __init__(self, x, y):
            self.x, self.y = x, y
            self.parent = None
            self.cost = 0.0  # 从起点到此节点的代价
    
    def __init__(self, start, goal, obstacles, x_range, y_range,
                 step_size=0.5, max_iter=3000, goal_threshold=0.5,

                 search_radius=2.0):
        self.start = self.Node(*start)

        self.goal = self.Node(*goal)
        self.obstacles = obstacles  # [(cx, cy, r), ...]
        self.x_range, self.y_range = x_range, y_range
        self.step = step_size
        self.max_iter = max_iter
        self.goal_thresh = goal_threshold
        self.search_radius = search_radius
        self.nodes = [self.start]
    
    def plan(self):
        for i in range(self.max_iter):
            # 1. 随机采样（偏向目标采样概率 5%）
            if np.random.random() < 0.05:
                x_rand = self.Node(self.goal.x, self.goal.y)
            else:
                x_rand = self.Node(
                    np.random.uniform(*self.x_range),
                    np.random.uniform(*self.y_range))
            
            # 2. 找最近节点
            x_nearest = self._nearest(x_rand)
            
            # 3. 沿方向延伸
            x_new = self._steer(x_nearest, x_rand)
            
            # 4. 碰撞检测
            if self._collision_free(x_nearest, x_new):
                # === RRT* 核心：选最优父节点 ===
                near_nodes = self._find_near(x_new)
                x_new.parent = x_nearest
                x_new.cost = x_nearest.cost + self._dist(x_nearest, x_new)
                
                # 在近邻中寻找代价更小的父节点
                for x_near in near_nodes:
                    new_cost = x_near.cost + self._dist(x_near, x_new)
                    if (new_cost < x_new.cost and
                            self._collision_free(x_near, x_new)):
                        x_new.parent = x_near
                        x_new.cost = new_cost
                
                self.nodes.append(x_new)
                
                # === RRT* 核心：重连接 ===
                for x_near in near_nodes:
                    new_cost = x_new.cost + self._dist(x_new, x_near)
                    if (new_cost < x_near.cost and
                            self._collision_free(x_new, x_near)):
                        x_near.parent = x_new
                        x_near.cost = new_cost
                
                # 检查是否到达目标
                if self._dist(x_new, self.goal) < self.goal_thresh:
                    self.goal.parent = x_new
                    self.goal.cost = (x_new.cost +
                                      self._dist(x_new, self.goal))
                    return self._extract_path()
        
        return None  # 未找到路径
    
    def _nearest(self, node):
        return min(self.nodes,
                   key=lambda n: self._dist(n, node))
    
    def _find_near(self, node):
        """在搜索半径内的所有节点"""
        return [n for n in self.nodes
                if self._dist(n, node) < self.search_radius]
    
    def _steer(self, from_node, to_node):
        d = self._dist(from_node, to_node)
        if d < self.step:
            return self.Node(to_node.x, to_node.y)
        ratio = self.step / d
        x = from_node.x + ratio * (to_node.x - from_node.x)
        y = from_node.y + ratio * (to_node.y - from_node.y)
        return self.Node(x, y)
    
    def _collision_free(self, n1, n2):
        """检查两节点间的路径是否无碰撞"""
        for (cx, cy, r) in self.obstacles:
            # 点到线段的最短距离
            dx, dy = n2.x - n1.x, n2.y - n1.y
            fx, fy = n1.x - cx, n1.y - cy
            a = dx*dx + dy*dy
            b = 2 * (fx*dx + fy*dy)
            c = fx*fx + fy*fy - r*r
            disc = b*b - 4*a*c
            if disc >= 0:
                disc = np.sqrt(disc)
                t1 = (-b - disc) / (2*a)
                t2 = (-b + disc) / (2*a)
                if 0 <= t1 <= 1 or 0 <= t2 <= 1:
                    return False
                if t1 < 0 and t2 > 1:
                    return False
        return True
    
    def _dist(self, n1, n2):
        return np.hypot(n1.x - n2.x, n1.y - n2.y)
    
    def _extract_path(self):
        path = []
        node = self.goal
        while node is not None:
            path.append((node.x, node.y))
            node = node.parent
        return path[::-1]

# === 使用示例 ===
obstacles = [(3, 3, 1.0), (5, 7, 1.5), (8, 4, 1.0)]
planner = RRTStar(
    start=(0, 0), goal=(10, 10),
    obstacles=obstacles,
    x_range=(0, 12), y_range=(0, 12),
    step_size=0.5, max_iter=5000, search_radius=2.0)
path = planner.plan()
if path:
    xs, ys = zip(*path)
    print(f"路径长度: {sum(np.hypot(np.diff(xs), np.diff(ys))):.2f}")
```

**RRT vs RRT\* 路径质量对比**：

```bob
┌──────────────────────────────────────────────────────┐
│          RRT vs RRT* 路径对比                         │
│                                                      │
│    RRT（不重连接）             RRT*（重连接优化）     │
│  ┌──────────────┐          ┌──────────────┐          │
│  │ S            │          │ S            │          │
│  │  \           │          │  \           │          │
│  │   \--+       │          │   \          │          │
│  │      |  ##   │          │    \    ##   │          │
│  │   +--+ ##    │          │     \  ##    │          │
│  │   |          │          │      \       │          │
│  │   +----+     │          │       \      │          │
│  │        |     │          │        \     │          │
│  │     +--+  G  │          │         \  G │          │
│  │     |    /   │          │          \/  │          │
│  └──────────────┘          └──────────────┘          │
│  路径曲折，代价高            路径平滑，趋近最优       │
└──────────────────────────────────────────────────────┘
```

**图 14-3** 
<!-- fig:ch14-3  -->

**表 14-5** 
<!-- tab:ch14-5  -->

| 算法 | 最优性 | 连通空间 | 高维适用 | 计算复杂度 |
|------|--------|---------|---------|-----------|
| A\* | 最优 | 离散网格 | 维度灾难 | $O(V \log V)$ |
| RRT | 概率完备 | 连续空间 | 适用 | $O(n \log n)$ |
| RRT\* | 渐近最优 | 连续空间 | 适用 | $O(n \log n)$ |

---

### 14.3 局部规划与避障

全局规划提供粗略的路径参考，但机器人需要在实际运动中处理未知障碍、动态环境和运动学约束。这是局部规划器的职责。

#### 14.3.1 DWA（Dynamic Window Approach）

DWA 是经典的局部避障算法，在速度空间中搜索最优控制指令。

**核心思想**：

1. **速度空间采样**：在允许的线速度 $(v)$ 和角速度 $(\omega)$ 范围内，考虑加速度约束，确定当前可达的速度窗口；
2. **轨迹仿真**：对窗口内的每组 $(v, \omega)$，仿真短期内（如 1-2 秒）机器人的运动轨迹；
3. **评价函数**：对每条轨迹打分，综合考虑：

   - **目标朝向**：轨迹终点与目标方向的对齐度；
   - **障碍距离**：轨迹上最近障碍物的距离；

   - **速度大小**：偏好较高速度（高效移动）；
4. **选择最优**：选择得分最高的 $(v, \omega)$ 作为当前控制指令。

```bob
┌──────────────────────────────────────────────────┐
│              DWA 工作流程                          │
│                                                  │
│  ┌────────────┐    ┌──────────────────┐          │
│  │ 当前速度   │───►│  动态窗口计算    │          │
│  │ "v, ω"    │    │  加速度约束      │          │
│  └────────────┘    └────────┬─────────┘          │
│                             │                    │
│                    ┌────────▼─────────┐          │
│                    │  速度空间采样    │          │
│                    │  N 组 "(v, ω)"  │          │
│                    └────────┬─────────┘          │
│                             │                    │
│                    ┌────────▼─────────┐          │
│  ┌──────────┐     │  轨迹仿真      │          │
│  │ 障碍物   │────►│  每组 → 轨迹弧 │          │
│  └──────────┘     └────────┬─────────┘          │
│                             │                    │
│  ┌──────────┐     ┌────────▼─────────┐          │
│  │ 目标点   │────►│  多目标评价函数  │          │
│  └──────────┘     └────────┬─────────┘          │
│                             │                    │
│                    ┌────────▼─────────┐          │
│                    │  最优 "(v, ω)"   │          │
│                    │  → "cmd_vel"     │          │
│                    └──────────────────┘          │
└──────────────────────────────────────────────────┘
```


**图 14-4** 上图以框图形式描绘了 DWA（Dynamic Window Approach）的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch14-4 上图以框图形式描绘了 DWA（Dynamic Window Approach）的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

#### 14.3.2 TEB（Timed Elastic Band）

TEB 将路径建模为带时间信息的弹性带，通过图优化同时考虑路径平滑性、时间最优和运动学约束。

与 DWA 对比：

**表 14-6** TEB（Timed Elastic Band）
<!-- tab:ch14-6 TEB（Timed Elastic Band） -->

| 特性 | DWA | TEB |
|------|-----|-----|
| 方法 | 速度空间采样 | 弹性带图优化 |
| 路径平滑性 | 一般 | 优秀 |
| 运动学约束 | 隐式（速度/加速度限制） | 显式（曲率、最小转弯半径） |
| 计算量 | 低 | 中 |
| 动态避障 | 即时响应 | 较好（可预测障碍运动） |
| 适用平台 | 差速、全向 | 差速、全向、阿克曼 |

**DWA Python 完整实现**：

以下是差速驱动机器人的完整 DWA 算法实现，可直接运行和调试：

```python
import numpy as np

import math

class DWAPlanner:
    """DWA 局部路径规划器（差速驱动机器人）"""

    def __init__(self):

        # 机器人参数
        self.max_v = 0.5       # 最大线速度 (m/s)
        self.min_v = 0.0       # 最小线速度
        self.max_w = 1.0       # 最大角速度 (rad/s)
        self.max_acc_v = 0.5   # 最大线加速度 (m/s^2)
        self.max_acc_w = 1.5   # 最大角加速度 (rad/s^2)

        # DWA 参数
        self.dt = 0.1          # 采样时间步长
        self.predict_time = 2.0  # 轨迹预测时长 (s)
        self.v_resolution = 0.05  # 线速度采样分辨率
        self.w_resolution = 0.1   # 角速度采样分辨率

        # 评价函数权重
        self.alpha = 0.6       # 目标朝向权重
        self.beta = 0.2        # 障碍距离权重
        self.gamma = 0.2       # 速度大小权重
        self.robot_radius = 0.2  # 机器人半径 (m)

    def plan(self, state, goal, obstacles):
        """
        DWA 主循环
        state: [x, y, theta, v, w] 当前状态
        goal: [gx, gy] 目标点
        obstacles: [[ox1, oy1], [ox2, oy2], ...] 障碍物位置
        返回: (best_v, best_w, best_trajectory)
        """
        # 1. 计算动态窗口
        dw = self._dynamic_window(state)

        # 2. 遍历所有 (v, w) 组合
        best_score = -float('inf')
        best_v, best_w = 0.0, 0.0
        best_traj = None

        v = dw[0]  # v_min
        while v <= dw[1]:  # v_max
            w = dw[2]  # w_min
            while w <= dw[3]:  # w_max
                # 3. 预测轨迹
                traj = self._predict_trajectory(state, v, w)

                # 4. 评价
                heading = self._heading_score(traj, goal)
                clearance = self._clearance_score(traj, obstacles)
                velocity = abs(v) / self.max_v

                # 障碍距离太小则跳过
                if clearance < self.robot_radius:
                    w += self.w_resolution
                    continue

                score = (self.alpha * heading +
                         self.beta * clearance +
                         self.gamma * velocity)

                if score > best_score:
                    best_score = score
                    best_v, best_w = v, w
                    best_traj = traj

                w += self.w_resolution
            v += self.v_resolution

        return best_v, best_w, best_traj

    def _dynamic_window(self, state):
        """计算当前状态下的动态窗口"""
        v, w = state[3], state[4]
        # 速度范围 ∩ 加速度约束窗口
        v_min = max(self.min_v, v - self.max_acc_v * self.dt)
        v_max = min(self.max_v, v + self.max_acc_v * self.dt)
        w_min = max(-self.max_w, w - self.max_acc_w * self.dt)
        w_max = min(self.max_w, w + self.max_acc_w * self.dt)
        return [v_min, v_max, w_min, w_max]

    def _predict_trajectory(self, state, v, w):
        """按给定 (v, w) 预测一段轨迹"""
        traj = [list(state)]
        x, y, theta = state[0], state[1], state[2]
        t = 0
        while t <= self.predict_time:
            x += v * math.cos(theta) * self.dt
            y += v * math.sin(theta) * self.dt
            theta += w * self.dt
            traj.append([x, y, theta, v, w])
            t += self.dt
        return np.array(traj)

    def _heading_score(self, traj, goal):
        """轨迹终点到目标方向的对齐度（越大越好）"""
        dx = goal[0] - traj[-1, 0]
        dy = goal[1] - traj[-1, 1]
        target_angle = math.atan2(dy, dx)
        angle_diff = abs(target_angle - traj[-1, 2])
        # 归一化到 [0, pi]
        angle_diff = angle_diff % (2 * math.pi)
        if angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff
        return math.pi - angle_diff  # 越对齐分越高

    def _clearance_score(self, traj, obstacles):
        """轨迹上离最近障碍物的最小距离"""
        if len(obstacles) == 0:
            return float('inf')
        min_dist = float('inf')
        for point in traj:
            for obs in obstacles:
                d = math.hypot(point[0] - obs[0], point[1] - obs[1])
                min_dist = min(min_dist, d)
        return min_dist

# === 使用示例 ===
dwa = DWAPlanner()
state = [0.0, 0.0, 0.0, 0.0, 0.0]  # [x, y, theta, v, w]
goal = [5.0, 5.0]
obstacles = [[2.0, 2.0], [3.0, 4.0], [4.5, 2.5]]

v, w, traj = dwa.plan(state, goal, obstacles)
print(f"最优控制: v={v:.2f} m/s, w={w:.2f} rad/s")
print(f"轨迹点数: {len(traj)}")
```

#### 14.3.3 VFH（Vector Field Histogram）

VFH 将传感器数据投射为极坐标直方图，寻找安全通行的方向：

1. 将 360° 划分为 $n$ 个扇区（如每 5° 一个，共 72 个扇区）；
2. 累加每个扇区内障碍物的密度/距离权重；
3. 在直方图中寻找足够宽的低密度谷（valley）；
4. 从候选谷中选择最接近目标方向的进行通行。

#### 14.3.4 Frenet 坐标系与横纵向解耦规划

Frenet 坐标系（又称 Frenet-Serret 坐标系）是自动驾驶和移动机器人领域中广泛使用的路径表示方法，特别适合结构化道路场景。它将规划问题从笛卡尔坐标系转换到沿参考路径的自然坐标系，实现**纵向（行驶方向）和横向（偏移方向）的解耦**。

**坐标定义**：

- $s$：沿参考路径的弧长（纵向位置）
- $d$：到参考路径的横向偏移（正值=左偏，负值=右偏）
- 参考路径：通常为道路中心线或全局规划路径

```bob
┌──────────────────────────────────────────────┐
│         Frenet 坐标系示意                     │
│                                              │
│           d（横向偏移）                      │
│           ^                                  │
│           |    机器人                         │
│           |   *--->                           │
│           |  /  d                             │
│    -------+------*--------*---------> s      │
│           |   参考路径（道路中心线）          │
│           |                                  │
│                                              │
│  笛卡尔 (x,y) ←→ Frenet (s,d)              │
└──────────────────────────────────────────────┘
```


**图 14-5** 该框图展示了 Frenet 坐标系与横纵向解耦规划的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch14-5 该框图展示了 Frenet 坐标系与横纵向解耦规划的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

**Frenet 坐标转换公式**：

给定参考路径 $\mathbf{r}(s) = (r_x(s), r_y(s))$，机器人位置 $(x, y)$ 的 Frenet 坐标：

$$
s = \arg\min_{s'} \| (x, y) - \mathbf{r}(s') \|
$$

$$
d = \text{sign}(\mathbf{n}(s) \cdot ((x,y) - \mathbf{r}(s))) \cdot \| (x, y) - \mathbf{r}(s) \|
$$

其中 $\mathbf{n}(s)$ 为参考路径在 $s$ 处的法向量。

**横纵向解耦规划策略**：

```bob
┌─────────────────────────────────────────────────────┐
│        Frenet 规划流程                               │
│                                                     │
│  ┌──────────────┐                                   │

│  │ 参考路径生成 │                                   │
│  │（全局规划输出）│                                   │

│  └──────┬───────┘                                   │
│         │                                           │
│   ┌─────▼──────────────────────────────────────┐    │
│   │ 坐标转换: 笛卡尔(x,y) → Frenet(s,d)      │    │
│   └─────┬────────────────────────┬─────────────┘    │
│         │                        │                  │
│  ┌──────▼───────┐     ┌─────────▼──────────┐       │
│  │  纵向规划    │     │   横向规划         │       │
│  │ s(t) 速度曲线│     │ d(t) 偏移曲线     │       │
│  │ 梯形/多项式  │     │ 五次多项式        │       │
│  └──────┬───────┘     └─────────┬──────────┘       │
│         │                        │                  │
│   ┌─────▼────────────────────────▼─────────────┐    │
│   │ 轨迹组合 + 碰撞检测 + 代价评估            │    │
│   └─────┬──────────────────────────────────────┘    │
│         │                                           │
│   ┌─────▼──────────────────────────────────────┐    │
│   │ 坐标逆转换: Frenet(s,d) → 笛卡尔(x,y)    │    │
│   └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```


**图 14-6** 上图直观呈现了 Frenet 坐标系与横纵向解耦规划的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch14-6 上图直观呈现了 Frenet 坐标系与横纵向解耦规划的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

**横向五次多项式轨迹生成**：

给定初始状态 $(d_0, \dot{d}_0, \ddot{d}_0)$ 和终止状态 $(d_f, \dot{d}_f, \ddot{d}_f)$，横向轨迹用五次多项式表示：

$$
d(t) = a_0 + a_1 t + a_2 t^2 + a_3 t^3 + a_4 t^4 + a_5 t^5
$$

六个系数由六个边界条件唯一确定。

**Python 实现：Frenet 横向规划核心**：

```python
import numpy as np

class FrenetPlanner:
    """Frenet 坐标系横纵向解耦规划器"""

    def __init__(self, ref_path):
        """

        ref_path: Nx2 数组，参考路径点 [[x0,y0], [x1,y1], ...]
        """
        self.ref = np.array(ref_path)
        # 预计算参考路径的弧长
        diffs = np.diff(self.ref, axis=0)
        self.ds = np.hypot(diffs[:, 0], diffs[:, 1])
        self.s_arr = np.concatenate([[0], np.cumsum(self.ds)])

    def cartesian_to_frenet(self, x, y):
        """笛卡尔坐标 → Frenet 坐标 (s, d)"""
        dists = np.hypot(self.ref[:, 0] - x, self.ref[:, 1] - y)
        idx = np.argmin(dists)

        # 精确投影到最近线段
        if idx < len(self.ref) - 1:
            p = np.array([x, y])
            a, b = self.ref[idx], self.ref[idx + 1]
            ab = b - a
            t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
            proj = a + t * ab
            s = self.s_arr[idx] + t * self.ds[idx]
        else:
            proj = self.ref[idx]
            s = self.s_arr[idx]

        # 横向偏移 d（含符号）
        dx, dy = x - proj[0], y - proj[1]
        # 参考路径方向向量
        if idx < len(self.ref) - 1:
            tangent = self.ref[idx + 1] - self.ref[idx]
        else:
            tangent = self.ref[idx] - self.ref[idx - 1]
        normal = np.array([-tangent[1], tangent[0]])
        d = np.sign(np.dot([dx, dy], normal)) * np.hypot(dx, dy)

        return s, d

    @staticmethod
    def quintic_polynomial(d0, dd0, ddd0, df, ddf, dddf, T):
        """
        五次多项式轨迹
        d0, dd0, ddd0: 初始 位置, 速度, 加速度
        df, ddf, dddf: 终止 位置, 速度, 加速度
        T: 时间跨度
        返回: 系数 [a0..a5]
        """
        a0 = d0
        a1 = dd0
        a2 = ddd0 / 2.0

        A = np.array([
            [T**3,     T**4,      T**5],
            [3*T**2,   4*T**3,    5*T**4],
            [6*T,      12*T**2,   20*T**3]
        ])
        b = np.array([
            df - a0 - a1*T - a2*T**2,
            ddf - a1 - 2*a2*T,
            dddf - 2*a2
        ])
        x = np.linalg.solve(A, b)
        return [a0, a1, a2, x[0], x[1], x[2]]

    def generate_lateral_candidates(self, d0, dd0, ddd0, T,
                                     d_offsets=None):
        """
        生成横向候选轨迹集
        d_offsets: 目标横向偏移集合（如 [-1.0, -0.5, 0, 0.5, 1.0]）
        """
        if d_offsets is None:
            d_offsets = np.arange(-2.0, 2.1, 0.5)

        candidates = []
        dt = 0.1
        t_arr = np.arange(0, T + dt, dt)

        for df in d_offsets:
            coeffs = self.quintic_polynomial(
                d0, dd0, ddd0, df, 0.0, 0.0, T)
            d_traj = np.polyval(coeffs[::-1], t_arr)

            # 代价 = 横向偏移 + 横向加速度平滑性
            jerk = np.diff(np.diff(d_traj)) / dt**2
            cost = abs(df) + 0.1 * np.sum(jerk**2) * dt
            candidates.append({
                't': t_arr, 'd': d_traj,
                'd_final': df, 'cost': cost})

        # 按代价排序
        candidates.sort(key=lambda c: c['cost'])
        return candidates

# === 使用示例 ===
# 参考路径：一段弯曲的道路中心线
t = np.linspace(0, 10, 100)
ref_path = np.column_stack([t, 2 * np.sin(0.3 * t)])

planner = FrenetPlanner(ref_path)

# 当前位置转 Frenet 坐标
s, d = planner.cartesian_to_frenet(3.0, 1.5)
print(f"Frenet坐标: s={s:.2f}, d={d:.2f}")

# 生成横向候选轨迹
candidates = planner.generate_lateral_candidates(
    d0=d, dd0=0.0, ddd0=0.0, T=3.0,
    d_offsets=[-1.0, -0.5, 0.0, 0.5, 1.0])
print(f"生成 {len(candidates)} 条候选轨迹")
print(f"最优轨迹目标偏移: d={candidates[0]['d_final']:.1f}m, "
      f"代价={candidates[0]['cost']:.3f}")
```

**Frenet 规划的应用场景**：

**表 14-7** 
<!-- tab:ch14-7  -->

| 场景 | 说明 |
|------|------|
| 结构化道路行驶 | 自动驾驶车辆在车道内保持/变道 |
| 走廊导航 | 移动机器人在走廊中避让行人 |
| 轨道跟踪 | AGV 沿磁条/激光导引线行驶 |
| 编队控制 | 多机器人沿参考路径保持队形 |

#### 14.3.5 局部规划算法对比总结

**表 14-8** 局部规划算法对比总结
<!-- tab:ch14-8 局部规划算法对比总结 -->

| 算法 | 原理 | 优势 | 劣势 | 适用场景 |
|------|------|------|------|---------|
| DWA | 速度空间采样+评价 | 实时性好、简单 | 局部最优、缺乏前瞻 | 差速/全向机器人 |
| TEB | 弹性带图优化 | 平滑、可处理约束 | 计算量中等 | 阿克曼/差速 |
| VFH | 极坐标直方图 | 适合密集障碍 | 参数敏感 | 窄道通行 |
| Frenet | 横纵向解耦+多项式 | 结构化、可预测 | 需要参考路径 | 结构化道路/走廊 |

---

### 14.4 代价地图（Costmap）

#### 14.4.1 什么是代价地图


**表 14-9** 代价地图是导航系统对环境的一种量化表示，将每个栅格赋予一个 0-255 的代价值：
<!-- tab:ch14-9 代价地图是导航系统对环境的一种量化表示，将每个栅格赋予一个 0-255 的代价值： -->

| 代价值 | 含义 |
|--------|------|
| 0 | 空闲空间 |
| 1-252 | 不同程度的通行代价 |
| 253 | 膨胀区域（靠近障碍） |
| 254 | 致命障碍（已知障碍） |
| 255 | 未知区域 |

上表列出了什么是代价地图所涉及的关键参数及其典型取值，这些参数的选择直接影响系统的整体性能与稳定性。

#### 14.4.2 代价地图层

Nav2 的代价地图由多个层叠加而成：

```bob
┌────────────────────────────────────────────┐
│            代价地图分层结构                  │
│                                            │
│  ┌───────────────────────────────────────┐  │
│  │          Master Costmap               │  │
│  │       （各层叠加的结果）              │  │
│  └───────────────────┬───────────────────┘  │
│                      │ 叠加                 │
│  ┌───────────┬───────┴──────┬────────────┐  │
│  │           │              │            │  │
│  ▼           ▼              ▼            ▼  │
│ ┌─────┐  ┌──────┐  ┌───────────┐ ┌─────┐  │
│ │静态层│  │障碍层│  │  膨胀层   │ │其他 │  │
│ │     │  │     │  │           │ │自定义│  │
│ │已知 │  │实时 │  │ 机器人    │ │ 层  │  │
│ │地图 │  │激光 │  │ 半径膨胀  │ │     │  │
│ └─────┘  └──────┘  └───────────┘ └─────┘  │
└────────────────────────────────────────────┘
```


**图 14-7** 上图以框图形式描绘了代价地图层的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch14-7 上图以框图形式描绘了代价地图层的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

- **静态层（Static Layer）**：来自预先构建的地图（SLAM 的输出），标记已知障碍和空闲区域；
- **障碍层（Obstacle Layer）**：根据激光雷达、深度相机等实时传感器数据，动态更新障碍物信息；
- **膨胀层（Inflation Layer）**：将障碍物向外膨胀，形成安全缓冲区。膨胀半径通常等于机器人半径 + 安全裕量；
- **自定义层**：可添加禁行区域、限速区域、虚拟墙等。

#### 14.4.3 全局代价地图 vs 局部代价地图

**表 14-10** 全局代价地图 vs 局部代价地图
<!-- tab:ch14-10 全局代价地图 vs 局部代价地图 -->

| 特性 | 全局代价地图 | 局部代价地图 |
|------|------------|------------|
| 范围 | 整个地图 | 机器人周围窗口（如 5×5m） |
| 更新频率 | 低（静态为主） | 高（传感器实时更新） |
| 用途 | 全局规划器使用 | 局部规划器使用 |
| 滚动 | 固定 | 跟随机器人移动 |

---

### 14.5 定位：AMCL

当使用已知地图导航时，机器人需要在地图上定位自身。AMCL（Adaptive Monte Carlo Localization）是 ROS2 中最常用的定位方法。

#### 14.5.1 粒子滤波定位

AMCL 基于粒子滤波（蒙特卡洛定位）：

1. **初始化**：在地图上均匀撒布 $N$ 个粒子（每个粒子代表一种可能的位姿）；
2. **预测**：根据里程计数据，按运动模型移动所有粒子（加入噪声）；
3. **更新**：将激光扫描与地图对比，计算每个粒子的权重（观测似然）；
4. **重采样**：按权重重新采样粒子——权重高的粒子被复制，低的被淘汰；
5. **收敛**：经过多次迭代，粒子聚集到真实位姿附近。

```bob
┌────────────────────────────────────────────────────┐
│           AMCL 粒子滤波定位流程                     │
│                                                    │
│  步骤1: 初始化                步骤2: 预测           │
│  ┌──────────────┐            ┌──────────────┐      │
│  │ . . . . . .  │            │ . . . . . .  │      │
│  │ . . . . . .  │  里程计    │  . . . . . . │      │
│  │ . . . . . .  │ ────────►  │   . . . . .  │      │
│  │ . . . . . .  │  +噪声     │    . . . . . │      │
│  └──────────────┘            └──────────────┘      │
│                                                    │
│  步骤3: 更新权重              步骤4: 重采样         │
│  ┌──────────────┐            ┌──────────────┐      │
│  │ . . o . . .  │  激光匹配  │       O      │      │
│  │  . . o . .   │ ────────►  │      OOO     │      │
│  │   . o O o .  │  权重大=O  │       O      │      │
│  │    . . . . . │            │              │      │
│  └──────────────┘            └──────────────┘      │
│                              粒子聚集=定位成功      │
└────────────────────────────────────────────────────┘
```


**图 14-8** 该框图展示了粒子滤波定位的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch14-8 该框图展示了粒子滤波定位的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

#### 14.5.2 AMCL 配置要点

```yaml
amcl:
  ros__parameters:
    # 粒子数量
    min_particles: 500
    max_particles: 2000
    
    # 运动模型参数（差速驱动）

    robot_model_type: differential
    alpha1: 0.2  # 旋转-旋转噪声

    alpha2: 0.2  # 旋转-平移噪声
    alpha3: 0.2  # 平移-平移噪声
    alpha4: 0.2  # 平移-旋转噪声
    
    # 激光模型
    laser_model_type: likelihood_field
    laser_max_range: 12.0
    max_beams: 60
    z_hit: 0.5
    z_rand: 0.5
    sigma_hit: 0.2
    
    # 更新阈值
    update_min_d: 0.25   # 最小平移 0.25m 触发更新
    update_min_a: 0.2    # 最小旋转 0.2rad 触发更新
```

---

### 14.6 ROS2 Nav2 导航栈

#### 14.6.1 Nav2 架构概览

Nav2 是 ROS2 的标准导航框架，采用行为树（Behavior Tree）驱动的模块化架构：

```bob
┌──────────────────────────────────────────────────────────────┐
│                     Nav2 导航栈架构                           │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              行为树（BT Navigator）                     │  │
│  │  NavigateToPose → ComputePath → FollowPath → Recovery  │  │
│  └─────┬────────────────┬──────────────┬──────────────────┘  │
│        │                │              │                     │
│  ┌─────▼─────┐  ┌──────▼──────┐  ┌───▼─────────┐           │
│  │ 全局规划  │  │  局部控制   │  │  恢复行为   │           │
│  │ Planner   │  │ Controller  │  │ Recovery    │           │
│  │ Server    │  │ Server      │  │ Server      │           │
│  └─────┬─────┘  └──────┬──────┘  └─────────────┘           │
│        │                │                                    │
│  ┌─────▼────────────────▼─────────────────────────────┐     │
│  │                代价地图                             │     │
│  │  全局 Costmap          局部 Costmap                │     │
│  └────────────────────────────────────────────────────┘     │
│        ▲                ▲                                    │
│  ┌─────┴─────┐  ┌──────┴──────┐                             │
│  │  地图服务 │  │    AMCL     │                             │
│  │ Map Server│  │    定位     │                             │
│  └───────────┘  └─────────────┘                             │
└──────────────────────────────────────────────────────────────┘
```


**图 14-9** 上图直观呈现了 Nav2 架构概览的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch14-9 上图直观呈现了 Nav2 架构概览的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

核心组件：

- **BT Navigator**：行为树导航器，协调规划、控制和恢复行为的执行顺序；
- **Planner Server**：全局路径规划服务，默认使用 NavFn（基于 Dijkstra/A\*）；
- **Controller Server**：局部控制服务，默认使用 DWB（DWA 的改进版）；
- **Recovery Server**：恢复行为（如旋转、后退、清除代价地图），在导航失败时尝试恢复；
- **Costmap**：代价地图（全局+局部），管理导航的环境感知。

#### 14.6.2 Nav2 安装与基本配置

```bash

# 安装 Nav2 全套
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup

# 安装 Turtlebot3 仿真（用于学习）
sudo apt install ros-humble-turtlebot3-gazebo ros-humble-turtlebot3-navigation2
export TURTLEBOT3_MODEL=burger
```

#### 14.6.3 Nav2 参数配置

Nav2 的配置文件是一个大型 YAML 文件，以下是核心部分：

```yaml
# nav2_params.yaml
bt_navigator:
  ros__parameters:
    default_bt_xml_filename: "navigate_w_replanning_and_recovery.xml"
    plugin_lib_names:
      - nav2_compute_path_to_pose_action_bt_node
      - nav2_follow_path_action_bt_node
      - nav2_back_up_action_bt_node
      - nav2_spin_action_bt_node
      - nav2_wait_action_bt_node

controller_server:
  ros__parameters:
    controller_frequency: 20.0
    FollowPath:
      plugin: "dwb_core::DWBLocalPlanner"
      min_vel_x: 0.0
      max_vel_x: 0.26
      max_vel_theta: 1.0
      min_speed_xy: 0.0
      max_speed_xy: 0.26
      acc_lim_x: 2.5
      acc_lim_theta: 3.2
      decel_lim_x: -2.5
      decel_lim_theta: -3.2

planner_server:
  ros__parameters:
    GridBased:
      plugin: "nav2_navfn_planner/NavfnPlanner"
      tolerance: 0.5
      use_astar: true
      allow_unknown: true

global_costmap:
  global_costmap:
    ros__parameters:
      update_frequency: 1.0
      publish_frequency: 1.0
      robot_base_frame: base_link
      global_frame: map
      resolution: 0.05
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      inflation_layer:
        inflation_radius: 0.55
        cost_scaling_factor: 2.58
      obstacle_layer:
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: true
          marking: true

local_costmap:
  local_costmap:
    ros__parameters:
      update_frequency: 5.0
      publish_frequency: 2.0
      rolling_window: true
      width: 3
      height: 3
      resolution: 0.05
      plugins: ["voxel_layer", "inflation_layer"]
```

#### 14.6.4 运行完整导航示例

```bash
# 终端1：启动 Turtlebot3 仿真
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# 终端2：启动导航
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
  use_sim_time:=true map:=$HOME/map.yaml

# 在 RViz2 中：
# 1. 使用 "2D Pose Estimate" 设置初始位置
# 2. 使用 "Nav2 Goal" 设置目标位置
# 3. 观察全局路径（绿线）和局部轨迹（红线）
```

---

### 14.7 行为树（Behavior Tree）与任务规划

#### 14.7.1 为什么用行为树

Nav2 使用行为树（BT）替代传统的有限状态机（FSM）来管理导航逻辑。行为树的优势：

- **模块化**：每个行为是独立节点，易于组合和复用；
- **可扩展**：添加新行为只需创建新节点，无需修改现有逻辑；
- **可读性**：树结构直观表达任务优先级和执行顺序；
- **可调试**：通过 BT 可视化工具实时监控每个节点的状态。

**行为树 vs 有限状态机（FSM）深度对比**：

**表 14-11** 为什么用行为树
<!-- tab:ch14-11 为什么用行为树 -->

| 维度 | FSM | 行为树 |
|------|-----|--------|
| 结构 | 状态+转移（图） | 节点+子树（树） |
| 可扩展性 | 新增状态需修改多处转移 | 新增子树仅需挂载到父节点 |
| 状态爆炸 | $n$ 状态之间最多 $n^2$ 转移 | 深度 $d$ 的树节点数线性增长 |
| 可复用性 | 状态与转移紧耦合 | 子树可独立封装为库供复用 |
| 并发支持 | 需引入并行状态（复杂） | 原生 Parallel 节点支持 |
| 调试 | 需追踪当前状态和转移条件 | 每个节点有明确的 SUCCESS/FAILURE/RUNNING 状态 |
| 适用场景 | 简单的模式切换（如遥控/自动） | 复杂的任务编排（导航、巡检、操纵） |

通过上表的对比可以看出，不同方案在维度、FSM、行为树等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

```bob

┌─────────────────────────────────────────────────────────┐
│  FSM: 状态+转移（N个状态可能有 N^2 条转移线）           │
│                                                         │
│  ┌───────┐  避障触发   ┌───────┐                        │
│  │ 巡航  │────────────►│ 避障  │                        │
│  │       │◄────────────│       │                        │
│  └───┬───┘  障碍解除   └───┬───┘                        │
│      │                     │                            │
│      │ 电量低              │ 电量低                     │
│      ▼                     ▼                            │
│  ┌───────┐             ┌───────┐                        │
│  │ 充电  │             │ 充电  │  ← 重复的充电转移!      │
│  └───────┘             └───────┘                        │
│                                                         │
│  BT: 树形结构，职责清晰                                  │
│                                                         │
│              ┌──────────┐                                │
│              │ Fallback │                                │
│              └─────┬────┘                                │
│          ┌─────────┼──────────┐                         │
│          │         │          │                         │
│   ┌──────▼──────┐  ▼    ┌────▼──────┐                  │
│   │ IsBatteryOK │ 巡航  │ GoCharge  │                  │
│   │ (Condition) │ 子树  │ (Action)  │                  │
│   └─────────────┘       └───────────┘                  │
└─────────────────────────────────────────────────────────┘
```


**图 14-10** 上图以框图形式描绘了为什么用行为树的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch14-10 上图以框图形式描绘了为什么用行为树的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

#### 14.7.2 行为树执行机制（Tick 模型）


**表 14-12** 行为树的执行遵循 **Tick（心跳）** 机制：每个 tick 周期，从根节点开始递归调用子节点的 `tick()` 方法，每个节点返回三种状态之一：
<!-- tab:ch14-12 行为树的执行遵循 **Tick（心跳）** 机制：每个 tick 周期，从根节点开始递归调用子节点的 `tick()` 方法，每个节点返回三种状态之一： -->

| 状态 | 含义 | 后续行为 |
|------|------|---------|
| **SUCCESS** | 节点任务完成 | 父节点收到成功信号 |
| **FAILURE** | 节点任务失败 | 父节点收到失败信号 |
| **RUNNING** | 节点仍在执行中 | 下次 tick 继续调用此节点 |

上表对行为树执行机制（Tick 模型）中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

```bob
┌──────────────────────────────────────────────────┐
│         Tick 执行流程                             │

│                                                  │
│  外部时钟（如 10Hz）                              │
│      │                                           │
│      ▼ tick()                                    │
│  ┌───────┐                                       │
│  │ Root  │                                       │
│  └───┬───┘                                       │
│      │ tick()                                    │
│  ┌───▼───────┐                                   │
│  │ Sequence  │──► 按序 tick 子节点               │
│  └───┬───────┘                                   │
│      │                                           │
│  ┌───▼───┐  SUCCESS  ┌───────┐  RUNNING          │
│  │ 节点A │─────────► │ 节点B │────────► 停止     │
│  └───────┘           └───────┘    本轮tick结束    │
│                                                  │
│  下次 tick: Root → Sequence → 跳过A → 继续B     │
└──────────────────────────────────────────────────┘
```


**图 14-11** 该框图展示了行为树执行机制（Tick 模型）的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch14-11 该框图展示了行为树执行机制（Tick 模型）的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

**Blackboard（黑板）通信机制**：

行为树节点之间通过 **Blackboard**（共享键值对存储）传递数据，避免节点间的直接依赖：

```xml

<!-- Nav2 BT XML 示例：通过 Blackboard 传递目标和路径 -->
<root main_tree_to_execute="MainTree">

  <BehaviorTree ID="MainTree">
    <Sequence>
      <!-- ComputePathToPose 将路径写入 Blackboard 的 "path" 键 -->
      <ComputePathToPose goal="{goal}" path="{path}" 
                         planner_id="GridBased"/>
      
      <!-- FollowPath 从 Blackboard 读取 "path" 键 -->
      <FollowPath path="{path}" controller_id="FollowPath"/>
    </Sequence>
  </BehaviorTree>
</root>
```

**表 14-13** 
<!-- tab:ch14-13  -->

| Blackboard 键 | 写入者 | 读取者 | 类型 |
|---------------|--------|--------|------|
| `goal` | 外部（RViz/API） | ComputePathToPose | PoseStamped |
| `path` | ComputePathToPose | FollowPath | Path |
| `number_of_recoveries` | RecoveryNode | 恢复行为 | int |

通过上表的对比可以看出，不同方案在 Blackboard 键、写入者、读取者等等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

#### 14.7.3 行为树基本结构

```bob
┌──────────────────────────────────────────────────────┐
│           Nav2 默认行为树（简化）                      │
│                                                      │
│                  ┌───────────┐                        │
│                  │ Sequence  │                        │
│                  └─────┬─────┘                        │
│               ┌────────┼────────────┐                │
│               │        │            │                │
│         ┌─────▼─────┐ ┌▼──────┐ ┌──▼────────────┐   │
│         │ Compute   │ │Follow │ │ Recovery       │   │
│         │ PathTo    │ │ Path  │ │ Fallback       │   │
│         │ Pose      │ │       │ │                │   │
│         └───────────┘ └───────┘ │ ┌────┐ ┌────┐ │   │
│                                 │ │Spin│ │Back│ │   │
│                                 │ └────┘ └────┘ │   │
│                                 └────────────────┘   │
└──────────────────────────────────────────────────────┘
```


**图 14-12** 上图直观呈现了行为树基本结构的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch14-12 上图直观呈现了行为树基本结构的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

核心节点类型：

**表 14-14** 行为树基本结构
<!-- tab:ch14-14 行为树基本结构 -->

| 节点类型 | 行为 | 示例 |
|---------|------|------|
| **Sequence** | 依次执行子节点，全部成功才成功 | ComputePath → FollowPath |
| **Fallback** | 依次尝试子节点，任一成功就成功 | Recovery 策略选择 |
| **Parallel** | 并行执行子节点，按策略汇总结果 | 同时检测电池+执行任务 |
| **Action** | 执行具体操作 | ComputePathToPose, FollowPath |
| **Condition** | 检查条件（不改变世界状态） | IsGoalReached, IsBatteryLow |
| **Decorator** | 修饰子节点行为 | RateController, Inverter, Repeat |

**Decorator 装饰器节点详解**：

**表 14-15** 
<!-- tab:ch14-15  -->

| 装饰器 | 作用 | Nav2 中的使用 |
|--------|------|--------------|
| Inverter | 翻转子节点结果（SUCCESS↔FAILURE） | 条件取反 |
| Repeat(N) | 重复执行子节点 N 次 | 多点巡航循环 |
| Retry(N) | 失败后重试最多 N 次 | 规划失败重试 |
| RateController | 限制子节点的 tick 频率 | 降低规划频率 |
| RecoveryNode | 主行为失败时执行恢复行为 | Nav2 核心模式 |

上表对行为树基本结构中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

#### 14.7.4 自定义行为树节点（C++ 实现）

在 Nav2 中，可以使用 `behaviortree_cpp_v3` 库创建自定义 BT 节点：

**自定义 Condition 节点——检查电池电量**：

```cpp
// is_battery_ok.hpp
#include "behaviortree_cpp_v3/condition_node.h"
#include "sensor_msgs/msg/battery_state.hpp"
#include "rclcpp/rclcpp.hpp"

class IsBatteryOK : public BT::ConditionNode {
public:
    IsBatteryOK(const std::string& name,
                const BT::NodeConfiguration& config)
        : BT::ConditionNode(name, config) {}

    // 声明 Blackboard 端口
    static BT::PortsList providedPorts() {
        return {
            BT::InputPort<double>("threshold", 0.2,
                                   "最低电量百分比")
        };
    }

    BT::NodeStatus tick() override {
        double threshold;
        getInput("threshold", threshold);

        // 从 Blackboard 获取电池电量
        double battery_level;
        auto res = config().blackboard->get("battery_level",
                                             battery_level);
        if (!res) {
            return BT::NodeStatus::FAILURE;
        }

        return (battery_level > threshold)
            ? BT::NodeStatus::SUCCESS
            : BT::NodeStatus::FAILURE;
    }
};
```

**自定义 Action 节点——发送语音提示**：

```cpp
// speak_action.hpp
#include "behaviortree_cpp_v3/action_node.h"
#include "std_msgs/msg/string.hpp"

class SpeakAction : public BT::SyncActionNode {
public:
    SpeakAction(const std::string& name,
                const BT::NodeConfiguration& config)
        : BT::SyncActionNode(name, config) {
        node_ = rclcpp::Node::make_shared("speak_bt_node");
        pub_ = node_->create_publisher<std_msgs::msg::String>(
            "speech", 10);
    }

    static BT::PortsList providedPorts() {
        return {BT::InputPort<std::string>("message")};
    }

    BT::NodeStatus tick() override {
        std::string msg;
        getInput("message", msg);

        std_msgs::msg::String ros_msg;
        ros_msg.data = msg;
        pub_->publish(ros_msg);

        return BT::NodeStatus::SUCCESS;
    }

private:
    rclcpp::Node::SharedPtr node_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr pub_;
};
```

**注册并在 XML 中使用**：

```cpp
// 在插件注册文件中
BT_REGISTER_NODES(factory) {
    factory.registerNodeType<IsBatteryOK>("IsBatteryOK");
    factory.registerNodeType<SpeakAction>("SpeakAction");
}
```

```xml
<!-- 在 BT XML 中使用自定义节点 -->
<BehaviorTree ID="PatrolWithBatteryCheck">
  <Fallback>
    <Sequence>
      <IsBatteryOK threshold="0.2"/>
      <Sequence>
        <ComputePathToPose goal="{patrol_goal}" path="{path}"/>
        <FollowPath path="{path}"/>
        <SpeakAction message="到达巡检点"/>
      </Sequence>
    </Sequence>
    <Sequence>
      <SpeakAction message="电量不足，返回充电"/>
      <ComputePathToPose goal="{charging_station}" path="{path}"/>
      <FollowPath path="{path}"/>
    </Sequence>
  </Fallback>
</BehaviorTree>
```

#### 14.7.5 任务规划层：从导航到使命

行为树不仅用于导航，还可以扩展为机器人的**任务规划层**（Mission Planning），将多个导航任务组织成更高层的使命逻辑：

```bob
┌─────────────────────────────────────────────────────────┐
│              机器人任务规划层次                           │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Layer 3: Mission（使命层）                        │  │
│  │  "完成仓库巡检任务"                               │  │
│  │  包含: 多个区域巡检 + 异常上报 + 充电管理         │  │
│  └─────────────────────┬─────────────────────────────┘  │
│                        │                                │
│  ┌─────────────────────▼─────────────────────────────┐  │
│  │  Layer 2: Task（任务层）                           │  │
│  │  "巡检A区域": 导航到A1 → 拍照 → 导航到A2 → ...  │  │
│  └─────────────────────┬─────────────────────────────┘  │
│                        │                                │
│  ┌─────────────────────▼─────────────────────────────┐  │
│  │  Layer 1: Navigation（导航层）                     │  │
│  │  Nav2: ComputePath → FollowPath → Recovery        │  │
│  └─────────────────────┬─────────────────────────────┘  │
│                        │                                │
│  ┌─────────────────────▼─────────────────────────────┐  │
│  │  Layer 0: Control（控制层）                        │  │
│  │  micro-ROS: PID → 电机PWM → 编码器反馈            │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```


**图 14-13** 上图以框图形式描绘了任务规划层：从导航到使命的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch14-13 上图以框图形式描绘了任务规划层：从导航到使命的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

**使命级行为树示例——仓库巡检机器人**：

```xml
<BehaviorTree ID="WarehousePatrol">
  <Repeat num_cycles="0">  <!-- 0 = 无限循环 -->
    <Fallback>
      <!-- 优先级1：电量检查 -->
      <Sequence>
        <IsBatteryOK threshold="0.15"/>
        <!-- 优先级2：正常巡检 -->
        <Sequence>
          <ForEach items="{patrol_points}" item="{current_goal}">
            <Sequence>
              <ComputePathToPose goal="{current_goal}" path="{path}"/>
              <FollowPath path="{path}"/>
              <TakePhoto save_path="{photo_path}"/>
              <AnalyzeImage image="{photo_path}" result="{anomaly}"/>
              <Fallback>
                <Inverter>
                  <IsAnomaly result="{anomaly}"/>
                </Inverter>
                <ReportAnomaly location="{current_goal}" 
                               image="{photo_path}"/>
              </Fallback>
            </Sequence>
          </ForEach>
        </Sequence>
      </Sequence>
      <!-- 优先级3：低电量 → 充电 -->
      <Sequence>
        <SpeakAction message="电量不足，前往充电"/>
        <ComputePathToPose goal="{charging_station}" path="{path}"/>
        <FollowPath path="{path}"/>
        <WaitForCharge target_level="0.9"/>
      </Sequence>
    </Fallback>
  </Repeat>
</BehaviorTree>
```

**行为树工具链**：

**表 14-16** 
<!-- tab:ch14-16  -->

| 工具 | 用途 | 说明 |
|------|------|------|
| [Groot](https://www.behaviortree.dev/groot/) | BT 可视化编辑器 | 图形化拖拽创建 BT，实时监控节点状态 |
| [BehaviorTree.CPP](https://github.com/BehaviorTree/BehaviorTree.CPP) | C++ BT 引擎 | Nav2 使用的核心 BT 库 |
| [py_trees](https://github.com/splintered-reality/py_trees) | Python BT 引擎 | 适合快速原型验证 |
| [py_trees_ros](https://github.com/splintered-reality/py_trees_ros) | ROS2 BT 集成 | py_trees 的 ROS2 接口封装 |

---

### 14.8 导航实战：自定义导航系统

#### 14.8.1 自定义全局规划器

在 Nav2 中，可以通过插件机制实现自定义规划器：

```cpp
// my_planner.hpp
#include "nav2_core/global_planner.hpp"

class MyPlanner : public nav2_core::GlobalPlanner {
public:
    void configure(
        const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
        std::string name,
        std::shared_ptr<tf2_ros::Buffer> tf,
        std::shared_ptr<nav2_costmap_2d::Costmap2DROS> costmap_ros) override;
    
    void cleanup() override;
    void activate() override;
    void deactivate() override;
    
    nav_msgs::msg::Path createPlan(
        const geometry_msgs::msg::PoseStamped & start,
        const geometry_msgs::msg::PoseStamped & goal) override;
};
```

#### 14.8.2 多点巡航（Waypoint Following）

```python
# waypoint_follower.py
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator

class WaypointFollower(Node):
    def __init__(self):
        super().__init__('waypoint_follower')
        self.navigator = BasicNavigator()
        
        # 等待 Nav2 激活
        self.navigator.waitUntilNav2Active()
        
        # 定义巡航点
        waypoints = [
            self.create_pose(1.0, 0.0, 0.0),
            self.create_pose(2.0, 1.0, 1.57),
            self.create_pose(0.0, 2.0, 3.14),
            self.create_pose(0.0, 0.0, 0.0),
        ]
        
        # 开始巡航
        self.navigator.followWaypoints(waypoints)
        
        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            self.get_logger().info(
                f'Executing waypoint {feedback.current_waypoint + 1}/'
                f'{len(waypoints)}')
        
        result = self.navigator.getResult()
        self.get_logger().info(f'Navigation result: {result}')
    
    def create_pose(self, x, y, yaw):
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.z = math.sin(yaw / 2)
        pose.pose.orientation.w = math.cos(yaw / 2)
        return pose
```

#### 14.8.3 与 micro-ROS 底盘集成

结合第 13 章的 micro-ROS 底盘节点，完整的导航数据流：

```bob
┌─────────────────────────────────────────────────────────────┐
│           Nav2 + micro-ROS 导航数据流                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    Nav2                             │    │
│  │  目标点 → 全局规划 → 局部规划 → "cmd_vel"          │    │
│  └──────────────────┬──────────────▲───────────────────┘    │
│                     │ "cmd_vel"    │ /odom, /scan           │
│  ┌──────────────────▼──────────────┴───────────────────┐    │
│  │              micro-ROS Agent                        │    │
│  └──────────────────┬──────────────▲───────────────────┘    │
│                     │ UART         │ UART                   │
│  ┌──────────────────▼──────────────┴───────────────────┐    │
│  │            STM32  底盘控制器                         │    │
│  │  订阅 "cmd_vel" → 差速运动学 → PID → 电机 PWM     │    │
│  │  编码器 → 里程计 → 发布 /odom                       │    │
│  │  激光雷达 → 转发 /scan                              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```


**图 14-14** 该框图展示了与 micro-ROS 底盘集成的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch14-14 该框图展示了与 micro-ROS 底盘集成的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

---

### 14.9 本章小结与拓展资源

#### 14.9.1 关键知识点回顾

1. **全局规划**：A\* 算法（启发搜索、最优路径）、RRT（采样规划、高维空间）；
2. **局部规划**：DWA（速度空间搜索）、TEB（弹性带优化）、VFH（直方图避障）；
3. **代价地图**：静态层+障碍层+膨胀层的分层架构，全局/局部代价地图分工；
4. **定位**：AMCL 粒子滤波在已知地图上的定位方法；
5. **Nav2 架构**：行为树驱动的模块化导航栈，Planner/Controller/Recovery Server 协作；
6. **工程实践**：Nav2 配置、多点巡航、与 micro-ROS 底盘的集成。

#### 14.9.2 推荐学习资源

**表 14-17** 推荐学习资源
<!-- tab:ch14-17 推荐学习资源 -->

| 资源 | 说明 |
|------|------|
| [Nav2 官方文档](https://navigation.ros.org/) | 完整 API、教程和配置指南 |
| [Nav2 Simple Commander](https://github.com/ros-planning/navigation2/tree/main/nav2_simple_commander) | Python API 快速上手 |
| 《Planning Algorithms》(LaValle) | 路径规划理论经典 |
| 《Probabilistic Robotics》Ch. 5-7 | 粒子滤波、栅格地图、定位 |
| [MoveBase Flex](http://wiki.ros.org/move_base_flex) | ROS1 导航框架参考 |

以上内容归纳了推荐学习资源的关键要素，为后续深入学习和工程实践提供了参考依据。

#### 14.9.3 课后练习

1. **算法实现**：用 Python 实现 A\* 算法，在 50×50 的栅格地图上（含随机障碍物）搜索最短路径，可视化搜索过程和最终路径。
2. **算法对比**：对比 Dijkstra 和 A\*（使用不同启发函数）在同一地图上的搜索效率（扩展节点数、路径长度、计算时间）。
3. **Nav2 配置**：修改 Nav2 的参数，将全局规划器从 NavFn 切换为 Smac Planner（Hybrid A\*），观察路径平滑度的变化。
4. **多点巡航**：编写一个 ROS2 节点，使用 Nav2 Simple Commander 实现机器人在 5 个巡航点之间循环导航。
5. **综合挑战**：结合 SLAM（第 14 章）和 Nav2，在 Gazebo 仿真中实现机器人自主探索未知环境——边建图边导航到未探索区域。


---

### 14.10 本章测验

<div id="exam-meta" data-exam-id="chapter14" data-exam-title="第十四章 机器人导航与路径规划测验" style="display:none"></div>

<!-- mkdocs-quiz intro -->

<quiz>
1) A* 算法中，评价函数 $f(n) = g(n) + h(n)$ 的各项含义是什么？
- [x] $g(n)$ 是起点到 $n$ 的实际代价，$h(n)$ 是 $n$ 到终点的启发式估计
- [ ] $g(n)$ 是到终点的估计，$h(n)$ 是从起点的实际代价
- [ ] $g(n)$ 和 $h(n)$ 都是启发式估计值
- [ ] $f(n)$ 只考虑路径长度，不考虑障碍物

$g(n)$ 记录从起点沿已探索路径到节点 $n$ 的真实累积代价，$h(n)$ 是对 $n$ 到目标剩余代价的估计（常用欧几里得/曼哈顿距离）。当 $h(n)$ 是可容许的（不高估）时，A* 保证找到最优路径。
</quiz>

<quiz>
2) RRT（快速随机树）相比 A* 的主要优势是什么？
- [x] 能高效处理高维连续空间的路径规划
- [ ] 保证找到最短路径
- [ ] 搜索速度总是比 A* 快
- [ ] 不需要碰撞检测

A* 适合离散化的低维栅格地图，维度增加时节点数指数爆炸。RRT 通过随机采样渐进式探索连续空间，对高维问题（如机械臂规划）特别有效。基本 RRT 不保证最优性，RRT* 在渐近意义上收敛到最优。
</quiz>

<quiz>
3) DWA（Dynamic Window Approach）局部规划器的核心思想是什么？
- [x] 在速度空间中采样可行速度，评价并选择最优的 $(v, \omega)$ 组合
- [ ] 在位置空间中搜索最短路径
- [ ] 使用梯度下降优化全局路径
- [ ] 离线计算所有可能的运动轨迹

DWA 在每个控制周期内，根据机器人的动力学约束确定一个"动态窗口"（可行速度范围），对窗口内的 $(v, \omega)$ 进行采样，前向模拟短期轨迹，通过评价函数（目标距离 + 障碍物距离 + 速度）选择最优控制。
</quiz>

<quiz>
4) Nav2 中代价地图（Costmap）的膨胀层（Inflation Layer）的作用是什么？
- [x] 在障碍物周围设置渐变代价区域，使机器人与障碍物保持安全距离
- [ ] 压缩地图以减少内存使用
- [ ] 检测动态障碍物的运动趋势
- [ ] 将三维点云投影为二维地图

膨胀层以障碍物为中心向外扩展一个代价衰减区。核心半径（inscribed_radius）内代价为致命值（机器人必碰撞），外围按指数衰减。路径规划器会自动避开高代价区域，从而保持安全间距。
</quiz>

<!-- mkdocs-quiz results -->

---
