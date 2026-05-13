---
number headings: first-level 2, start-at 10
---

## 10 第 10 章 高级运动控制

### 10.1 从 PID 到高级控制


**表 10-1** 第 8 章介绍的 PID 控制器是工业中应用最广泛的控制方法，但在以下场景中存在明显局限：
<!-- tab:ch10-1 第 8 章介绍的 PID 控制器是工业中应用最广泛的控制方法，但在以下场景中存在明显局限： -->

| 局限场景 | 具体问题 | 需要的高级方法 |
|---------|---------|--------------|
| **多环嵌套** | 位置控制需要内嵌速度控制 | 串级 PID |
| **已知参考轨迹** | 纯反馈响应滞后 | 前馈 + 反馈复合控制 |
| **平滑运动** | 阶跃目标导致电机电流冲击 | 轨迹生成（S 曲线） |
| **约束处理** | 电机有最大转速/加速度限制 | 模型预测控制（MPC） |
| **非线性系统** | 线性 PID 适应范围有限 | 自适应/非线性控制 |
| **路径跟踪** | 差速机器人跟踪曲线路径 | 纯追踪 / Stanley 控制器 |

上表汇总了从 PID 到高级控制中常见的问题现象、可能原因及推荐解决方案，可作为排障时的快速参考手册。

```bob
                    "高级运动控制方法图谱"
                    

  "经典 PID"                                       "最优控制"
+------------+                                   +----------+

| "单环 PID"  |                                   | "MPC"    |
| "(第8章)"   |                                   | "LQR"   |
+-----+------+                                   +----+-----+
      |                                                |
      v                                                v
+------------+     +---------------+           +----------+
| "串级 PID"  |     | "前馈+反馈"    |           | "自适应"  |
| "位置+速度" |     | "复合控制"     |           | "鲁棒控制"|
+-----+------+     +-------+-------+           +----+-----+
      |                     |                        |
      +----------+----------+----------+-------------+
                 |                     |
                 v                     v
          +-------------+       +-----------+
          | "轨迹生成"   |       | "路径跟踪" |
          | "S曲线/多项式"|       | "纯追踪"   |
          +-------------+       | "Stanley"  |
                                +-----------+
```

上图以框图形式描绘了从 PID 到高级控制的系统架构，清晰呈现了各模块之间的连接关系与信号流向。

**图 10-1** 高级运动控制方法总览图
<!-- fig:ch10-1 高级运动控制方法总览图 -->

### 10.2 串级 PID 控制

#### 10.2.1 单环 vs 串级结构

单环位置 PID 的问题：位置误差直接输出 PWM 占空比，无法有效限制速度过冲。

串级 PID 将控制分为**外环（位置环）**和**内环（速度环）**：

```bob
                     "串级 PID 结构"

"位置目标" --+   "外环"     "速度目标"    "内环"     "PWM"     "电机"    "位置"

  x_ref    -+--->[ PID_pos ]---v_ref--->[ PID_vel ]---u--->[ Motor ]---+-> x
            ^-                          ^-                             |
            |                           |                              |
            +--------"位置反馈"----------+-------"速度反馈"-------------+
                     "编码器位置"                 "编码器速度"
```


**图 10-2** 该框图展示了单环 vs 串级结构的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch10-2 该框图展示了单环 vs 串级结构的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

#### 10.2.2 设计原则

1. **内环带宽 >> 外环带宽**：内环（速度环）响应应比外环（位置环）快 5-10 倍
2. **先调内环，后调外环**：先关闭外环，单独调好速度环；再接入外环
3. **内环抑制扰动**：负载变化等扰动首先被速度环快速抑制

#### 10.2.3 实现代码

```c

typedef struct {
    float kp, ki, kd;

    float integral;
    float prev_error;
    float output_min, output_max;
} PID_t;

float pid_compute(PID_t *pid, float error, float dt)
{
    pid->integral += error * dt;
    // 积分限幅
    if (pid->integral > pid->output_max) pid->integral = pid->output_max;
    if (pid->integral < pid->output_min) pid->integral = pid->output_min;
    
    float derivative = (error - pid->prev_error) / dt;
    pid->prev_error = error;
    
    float output = pid->kp * error + pid->ki * pid->integral + pid->kd * derivative;
    
    // 输出限幅
    if (output > pid->output_max) output = pid->output_max;
    if (output < pid->output_min) output = pid->output_min;
    
    return output;
}

// 串级 PID 主循环（100 Hz）
PID_t pid_pos = {.kp=2.0, .ki=0.1, .kd=0.5, .output_min=-1.0, .output_max=1.0};
PID_t pid_vel = {.kp=5.0, .ki=1.0, .kd=0.0, .output_min=-100, .output_max=100};

void cascade_pid_loop(float target_pos, float current_pos, float current_vel, float dt)
{
    // 外环：位置误差 → 速度目标
    float pos_error = target_pos - current_pos;
    float vel_target = pid_compute(&pid_pos, pos_error, dt);
    
    // 内环：速度误差 → PWM 输出
    float vel_error = vel_target - current_vel;
    float pwm_output = pid_compute(&pid_vel, vel_error, dt);
    
    motor_set_pwm((int)pwm_output);
}
```

### 10.3 前馈 + 反馈复合控制

#### 10.3.1 前馈控制原理

纯反馈控制必须"先有误差、后有校正"，存在固有的响应滞后。**前馈控制**在已知期望轨迹时，预先计算所需的控制输入，使系统"主动"跟随。

$$
u(t) = u_{ff}(t) + u_{fb}(t)
$$

- $u_{ff}$：前馈项，基于期望轨迹和系统模型计算
- $u_{fb}$：反馈项（PID），补偿模型误差和扰动

```bob
                     "前馈+反馈复合控制"

"期望轨迹" ─┬───→ "前馈" ──→ u_ff ──┐
  x_d(t)   |     "计算"            +──→ u(t) ──→ "被控对象" ──→ y(t)
           |                       |                             |
           +──→ "误差" ──→ "PID" ──→ u_fb ──┘                    |
                  ^                                              |
                  └──────────────────────────────────────────────┘
```


**图 10-3** 上图直观呈现了前馈控制原理的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch10-3 上图直观呈现了前馈控制原理的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

#### 10.3.2 速度前馈

对于电机速度控制，如果已知期望速度轨迹 $v_d(t)$，前馈项可以直接计算为：

$$
u_{ff} = \frac{v_d}{K_v}
$$

其中 $K_v$ 是电机电压-速度比例常数（空载时 $v \approx K_v \cdot u$）。

#### 10.3.3 加速度前馈

对于位置控制，还可以加入加速度前馈：

$$
u_{ff} = \frac{\dot{v}_d}{K_a} + \frac{v_d}{K_v}
$$

这样，反馈环节只需要处理小的残余误差，大幅提升跟踪精度。

### 10.4 轨迹生成

直接给电机一个阶跃目标（如"立刻移动到位置 100"）会导致电流冲击和机械振动。**轨迹生成器**将目标位置平滑地分解为随时间变化的位置、速度、加速度曲线。

#### 10.4.1 梯形速度曲线

最简单的平滑方案：加速 → 匀速 → 减速。

```bob
  "速度 v"
    ^
    |        v_max
    |    .-----------.
    |   /             \
    |  /               \
    | /                 \
    |/                   \
    +----+----+----+----+-→ "时间 t"
     t0   t1   t2   t3
    "加速"  "匀速" "减速"
```


**图 10-4** 上图以框图形式描绘了梯形速度曲线的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch10-4 上图以框图形式描绘了梯形速度曲线的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

```python
def trapezoidal_profile(s_total, v_max, a_max, dt=0.001):
    """生成梯形速度曲线"""
    # 计算加速所需距离
    t_acc = v_max / a_max
    s_acc = 0.5 * a_max * t_acc**2
    

    if 2 * s_acc > s_total:
        # 距离不够达到最大速度，变为三角形曲线

        t_acc = np.sqrt(s_total / a_max)
        v_peak = a_max * t_acc
        t_cruise = 0
    else:
        v_peak = v_max
        s_cruise = s_total - 2 * s_acc
        t_cruise = s_cruise / v_max
    
    t_total = 2 * t_acc + t_cruise
    
    times, positions, velocities, accelerations = [], [], [], []
    t = 0
    while t <= t_total:
        if t < t_acc:
            a = a_max
            v = a_max * t
            s = 0.5 * a_max * t**2
        elif t < t_acc + t_cruise:
            a = 0
            v = v_peak
            s = s_acc + v_peak * (t - t_acc)
        else:
            dt_dec = t - t_acc - t_cruise
            a = -a_max
            v = v_peak - a_max * dt_dec
            s = s_acc + v_peak * t_cruise + v_peak * dt_dec - 0.5 * a_max * dt_dec**2
        
        times.append(t)
        positions.append(s)
        velocities.append(v)
        accelerations.append(a)
        t += dt
    
    return times, positions, velocities, accelerations
```

#### 10.4.2 S 曲线（七段式）

梯形曲线在加速度切换点有突变（加加速度/jerk 无穷大），导致机械振动。S 曲线增加了加加速度限制：

```bob
  "加速度 a"            "速度 v"              "位置 s"
    ^                    ^                      ^
    |   .---.            |       .-------.      |              .----
    |  /     \           |      /         \     |            .'
    | /       \          |     /           \    |           /
    |/         \         |    /             \   |         .'
    +-----------\----→   +---/               \--+→    +--/----------→
                 \       |                      |    /
                  \      |                      |  .'
                   '---' |                      |.'
  "7段加速度"            "S 形速度"             "平滑位置"
```


**图 10-5** 该框图展示了 S 曲线（七段式）的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch10-5 该框图展示了 S 曲线（七段式）的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

七段包括：加加速 → 匀加速 → 减加速 → 匀速 → 加减速 → 匀减速 → 减减速。

#### 10.4.3 五次多项式轨迹

对于给定起止位置、速度、加速度的点到点运动，五次多项式可以保证连续到加速度级别：

$$
s(t) = a_0 + a_1 t + a_2 t^2 + a_3 t^3 + a_4 t^4 + a_5 t^5
$$

6 个系数由 6 个边界条件确定：起点和终点的位置、速度、加速度。

```python
import numpy as np

def quintic_polynomial(t_f, s0, sf, v0, vf, a0, af):
    """五次多项式轨迹：求解系数"""
    T = np.array([
        [1, 0,    0,      0,       0,        0       ],
        [0, 1,    0,      0,       0,        0       ],
        [0, 0,    2,      0,       0,        0       ],
        [1, t_f,  t_f**2, t_f**3,  t_f**4,   t_f**5  ],
        [0, 1,    2*t_f,  3*t_f**2,4*t_f**3, 5*t_f**4],
        [0, 0,    2,      6*t_f,   12*t_f**2,20*t_f**3]
    ])
    b = np.array([s0, v0, a0, sf, vf, af])
    coeffs = np.linalg.solve(T, b)
    return coeffs

def eval_quintic(coeffs, t):
    """计算轨迹在时刻 t 的位置、速度、加速度"""
    a = coeffs
    pos = a[0] + a[1]*t + a[2]*t**2 + a[3]*t**3 + a[4]*t**4 + a[5]*t**5
    vel = a[1] + 2*a[2]*t + 3*a[3]*t**2 + 4*a[4]*t**3 + 5*a[5]*t**4
    acc = 2*a[2] + 6*a[3]*t + 12*a[4]*t**2 + 20*a[5]*t**3
    return pos, vel, acc
```

### 10.5 模型预测控制（MPC）入门

#### 10.5.1 MPC 基本思想

MPC 在每个控制周期内求解一个**有限时域最优化问题**：

1. 基于当前状态和系统模型，预测未来 $N$ 步的状态轨迹
2. 优化未来 $N$ 步的控制输入，使状态轨迹尽量接近参考轨迹
3. 只执行第一步的控制输入
4. 下一周期重复（滚动优化）

```bob
  "状态"
    ^
    |            "参考轨迹"
    |     - - -*- - -*- - -*- - -*- - - - - 
    |        *   *       *
    |       *  "预测轨迹"  *
    |      *    "（优化后）"  *
    |     *                   *
    |    *
    |---*-----------+---------+→ "时间"
   "当前"   "预测窗口 N"     "只执行"
   "状态"                   "第1步"
```


**图 10-6** 上图直观呈现了 MPC 基本思想的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch10-6 上图直观呈现了 MPC 基本思想的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

#### 10.5.2 线性 MPC 公式

对线性系统 $\mathbf{x}_{k+1} = \mathbf{A}\mathbf{x}_k + \mathbf{B}\mathbf{u}_k$，MPC 求解：

$$
\min_{\mathbf{u}_0, \ldots, \mathbf{u}_{N-1}} \sum_{k=0}^{N-1} \left[ (\mathbf{x}_k - \mathbf{x}_k^{ref})^T \mathbf{Q} (\mathbf{x}_k - \mathbf{x}_k^{ref}) + \mathbf{u}_k^T \mathbf{R} \mathbf{u}_k \right] + (\mathbf{x}_N - \mathbf{x}_N^{ref})^T \mathbf{Q}_f (\mathbf{x}_N - \mathbf{x}_N^{ref})
$$

$$
\text{s.t.} \quad \mathbf{x}_{k+1} = \mathbf{A}\mathbf{x}_k + \mathbf{B}\mathbf{u}_k
$$

$$
\mathbf{u}_{min} \leq \mathbf{u}_k \leq \mathbf{u}_{max}
$$
$$
\mathbf{x}_{min} \leq \mathbf{x}_k \leq \mathbf{x}_{max}
$$

其中 $\mathbf{Q}$ 惩罚状态偏差，$\mathbf{R}$ 惩罚控制输入大小。

#### 10.5.3 差速机器人 MPC 轨迹跟踪

```python
import numpy as np
from scipy.optimize import minimize

class DiffDriveMPC:
    def __init__(self, dt=0.1, N=10):
        self.dt = dt
        self.N = N        # 预测步数
        self.Q = np.diag([10, 10, 1])  # 状态权重 [x, y, theta]
        self.R = np.diag([0.1, 0.01])  # 控制权重 [v, omega]
        self.v_max = 0.5   # 最大线速度 m/s
        self.omega_max = 1.0  # 最大角速度 rad/s
    
    def dynamics(self, x, u):
        """差速机器人离散运动模型"""
        x_next = np.array([
            x[0] + u[0] * np.cos(x[2]) * self.dt,
            x[1] + u[0] * np.sin(x[2]) * self.dt,
            x[2] + u[1] * self.dt
        ])
        return x_next
    
    def cost_function(self, u_flat, x0, x_ref_traj):
        """目标函数：轨迹跟踪误差 + 控制量"""
        u_seq = u_flat.reshape(self.N, 2)
        cost = 0.0
        x = x0.copy()
        
        for k in range(self.N):
            x = self.dynamics(x, u_seq[k])
            error = x - x_ref_traj[k]
            error[2] = np.arctan2(np.sin(error[2]), np.cos(error[2]))
            cost += error @ self.Q @ error + u_seq[k] @ self.R @ u_seq[k]
        
        return cost
    
    def solve(self, x0, x_ref_traj):
        """求解 MPC 优化问题"""
        u0 = np.zeros(self.N * 2)
        bounds = []
        for _ in range(self.N):
            bounds.append((-self.v_max, self.v_max))
            bounds.append((-self.omega_max, self.omega_max))
        
        result = minimize(
            self.cost_function, u0,
            args=(x0, x_ref_traj),
            method='SLSQP', bounds=bounds
        )
        
        u_optimal = result.x.reshape(self.N, 2)
        return u_optimal[0]  # 只返回第一步控制输入
```

#### 10.5.4 MPC vs PID 对比

**表 10-2** MPC vs PID 对比
<!-- tab:ch10-2 MPC vs PID 对比 -->

| 维度 | PID | MPC |
|------|-----|-----|
| 理论基础 | 经验法则 | 最优控制理论 |
| 约束处理 | 事后限幅（不优雅） | 优化中直接处理约束 |
| 多变量 | 需要解耦设计 | 天然支持 MIMO |
| 计算量 | 极低 | 需要在线求解优化 |
| 实时性 | 微秒级 | 毫秒级（取决于预测步长） |
| 适用平台 | 任何微控制器 | 需要一定算力（STM32H7 或更高） |

通过上表的对比可以看出，不同方案在维度、PID、MPC 等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

### 10.6 自适应与鲁棒控制概念

#### 10.6.1 为什么需要自适应

PID 和 MPC 都依赖准确的系统模型参数。但实际中：

- 机器人负载变化（未知质量的物体）
- 地面摩擦系数变化（室内瓷砖 vs 室外草地）
- 电池电压下降导致电机特性变化

**自适应控制**通过在线辨识系统参数，自动调整控制器。

```bob
"参考输入" ──→ "控制器" ──→ "被控对象" ──→ "输出"
              "（参数可调）"   "（参数未知）"    |
                  ^                           |
                  |                           |
              "自适应律"                       |
              "（在线辨识）" <─────────────────┘
```


**图 10-7** 上图以框图形式描绘了为什么需要自适应的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch10-7 上图以框图形式描绘了为什么需要自适应的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

#### 10.6.2 模型参考自适应控制（MRAC）

核心思想：设计一个"参考模型"描述期望的闭环行为，自适应律不断调整控制器参数，使实际系统行为趋近参考模型。

#### 10.6.3 鲁棒控制

与自适应控制不同，**鲁棒控制**不尝试辨识不确定性，而是设计控制器使其在所有可能的不确定性范围内都能保证稳定性和性能。

常见鲁棒控制方法：

- **滑模控制（SMC）**：在状态空间中定义滑动面，强制系统在滑动面上运动，对参数不确定性具有强鲁棒性
- **$H_\infty$ 控制**：在频域中最小化最坏情况下的增益

这些高级方法超出本课程深入讲授的范围，但理解其基本思想有助于在实际项目中选择合适的控制策略。

### 10.7 电机控制实战：位置 + 速度双闭环

#### 10.7.1 系统配置

在 STM32 + TB6612 电机驱动板上实现直流减速电机的位置伺服控制：

```bob
+----------+    "PWM"    +----------+    "电压"   +--------+
| "STM32"  |────────────→| "TB6612"  |───────────→| "直流"  |
| "TIM1"   |             | "驱动板"  |            | "电机"  |
+-----+----+             +----------+            +----+---+
      ^                                               |
      |                                          +----+---+
      |             "编码器脉冲"                   | "编码器" |
      +──────────────────────────────────────────| "AB相"  |
                    "TIM3 编码器模式"              +--------+
```


**图 10-8** 该框图展示了系统配置的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch10-8 该框图展示了系统配置的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

#### 10.7.2 完整串级 PID 实现

```c
#include "stm32f1xx_hal.h"

// 编码器读取
#define ENCODER_PPR  1320    // 每转脉冲数（含减速比）
#define WHEEL_RADIUS 0.033f  // 轮半径 33mm

static volatile int32_t encoder_count = 0;
static float current_position_rad = 0.0f;
static float current_velocity_rps = 0.0f;

// 定时器中断回调（100 Hz）
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM4) {  // 100 Hz 控制定时器
        // 读取编码器
        int32_t count = (int16_t)__HAL_TIM_GET_COUNTER(&htim3);
        __HAL_TIM_SET_COUNTER(&htim3, 0);
        
        encoder_count += count;
        
        // 计算位置（弧度）和速度（弧度/秒）
        current_position_rad = (float)encoder_count / ENCODER_PPR * 2.0f * 3.14159f;
        current_velocity_rps = (float)count / ENCODER_PPR * 2.0f * 3.14159f * 100.0f;
        
        // 串级 PID 计算
        float target_position = get_target_position();
        cascade_pid_loop(target_position, current_position_rad,
                        current_velocity_rps, 0.01f);
    }
}

// 电机 PWM 设置
void motor_set_pwm(int pwm)
{
    if (pwm >= 0) {
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_SET);   // 正转
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_RESET);
        __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, (uint32_t)pwm);
    } else {
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_RESET); // 反转
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_SET);
        __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, (uint32_t)(-pwm));
    }
}
```

### 10.8 移动机器人轨迹跟踪

#### 10.8.1 运动学控制器（Lyapunov 方法）

对于差速机器人跟踪参考点 $(x_r, y_r, \theta_r)$，定义误差坐标系：

$$
\begin{bmatrix} e_x \\ e_y \\ e_\theta \end{bmatrix} = \begin{bmatrix} \cos\theta & \sin\theta & 0 \\ -\sin\theta & \cos\theta & 0 \\ 0 & 0 & 1 \end{bmatrix} \begin{bmatrix} x_r - x \\ y_r - y \\ \theta_r - \theta \end{bmatrix}
$$

基于 Lyapunov 稳定性分析，控制律为：

$$
v = v_r \cos e_\theta + k_1 e_x
$$

$$
\omega = \omega_r + v_r (k_2 e_y + k_3 \sin e_\theta)
$$

其中 $k_1, k_2, k_3 > 0$ 为增益参数。

#### 10.8.2 纯追踪算法（Pure Pursuit）

纯追踪是移动机器人中最经典的路径跟踪算法之一，由 CMU 在 1992 年提出。

**核心思想**：在路径前方找一个"目标点"（lookahead point），计算从当前位置到该点的圆弧，用圆弧的曲率作为转向指令。

```bob
                      "目标点 (gx, gy)"
                           *
                          /|
                         / |
                    L_d /  |
          "前视距离"   /   | "α"
                      /    |
                     /  "α"|
  "机器人" --------*-------+
  "(x, y, θ)"     "当前位置"
                   
  "圆弧曲率" κ = 2·sin(α) / L_d
  "角速度"   ω = v · κ
```


**图 10-9** 上图直观呈现了纯追踪算法（Pure Pursuit）的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch10-9 上图直观呈现了纯追踪算法（Pure Pursuit）的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

算法步骤：

1. 在路径上找到距机器人前视距离 $L_d$ 处的目标点

2. 计算机器人到目标点的方向角 $\alpha$
3. 计算转向曲率 $\kappa = \frac{2 \sin\alpha}{L_d}$
4. 输出角速度 $\omega = v \cdot \kappa$

```python
import numpy as np

class PurePursuit:
    def __init__(self, lookahead_distance=0.5, max_velocity=0.3):
        self.L_d = lookahead_distance
        self.v_max = max_velocity
    
    def find_lookahead_point(self, path, robot_pos):
        """在路径上找到前视距离处的目标点"""
        min_dist = float('inf')
        nearest_idx = 0
        for i, pt in enumerate(path):
            dist = np.hypot(pt[0] - robot_pos[0], pt[1] - robot_pos[1])
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        
        # 从最近点向前搜索前视点
        for i in range(nearest_idx, len(path)):
            dist = np.hypot(path[i][0] - robot_pos[0],
                           path[i][1] - robot_pos[1])
            if dist >= self.L_d:
                return path[i]
        
        return path[-1]  # 路径末端
    
    def compute_control(self, robot_state, path):
        """计算控制输出 (v, omega)"""
        x, y, theta = robot_state
        goal = self.find_lookahead_point(path, (x, y))
        
        # 计算目标点在机器人坐标系下的方向
        dx = goal[0] - x
        dy = goal[1] - y
        alpha = np.arctan2(dy, dx) - theta
        alpha = np.arctan2(np.sin(alpha), np.cos(alpha))  # 归一化
        
        # 曲率
        kappa = 2.0 * np.sin(alpha) / self.L_d
        
        v = self.v_max
        omega = v * kappa
        
        return v, omega
```

#### 10.8.3 Stanley 控制器

Stanley 控制器是 Stanford 大学在 DARPA Grand Challenge 中使用的路径跟踪算法，以前轮为参考点。

```bob
             "路径切线方向"
               .─────→
              /|
             / | "横向误差 e"
            /  |
  "机器人" /   |
  "前轮"  *    +──────── "最近路径点"
          "θ_e 航向偏差"
```


**图 10-10** 上图以框图形式描绘了 Stanley 控制器的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch10-10 上图以框图形式描绘了 Stanley 控制器的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

转向角公式：

$$
\delta = \theta_e + \arctan\left(\frac{k \cdot e}{v}\right)
$$

其中：

- $\theta_e$：航向偏差（机器人朝向与路径切线方向的夹角）
- $e$：横向误差（机器人到路径的垂直距离）
- $k$：增益参数
- $v$：当前车速

特点：速度越快，横向误差修正越保守（避免急转弯）。

#### 10.8.4 三种路径跟踪方法对比

**表 10-3** 三种路径跟踪方法对比
<!-- tab:ch10-3 三种路径跟踪方法对比 -->

| 维度 | 纯追踪 | Stanley | Lyapunov |
|------|--------|---------|----------|
| 参考点 | 前视距离处 | 最近路径点 | 参考轨迹点 |
| 核心参数 | 前视距离 $L_d$ | 增益 $k$ | $k_1, k_2, k_3$ |
| 速度适应 | 需动态调整 $L_d$ | 自动适应 | 需要参考速度 |
| 转弯性能 | 转弯内切 | 反应灵敏 | 理论最优 |
| 实现复杂度 | 低 | 中 | 高 |
| 典型应用 | ROS2 Nav2 插件 | 自动驾驶 | 学术研究 |

上表对三种路径跟踪方法对比中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

### 10.9 综合实验：轨迹跟踪控制

#### 实验一：串级 PID 电机位置伺服

**目标**：在 STM32 上实现电机的串级 PID 位置控制，使电机转轴精确旋转到指定角度。

**步骤**：

1. 配置 TIM3 编码器模式，TIM1 PWM 输出
2. 先调速度环：给定速度阶跃目标，调整 $K_p^{vel}, K_i^{vel}$ 使速度响应无超调
3. 再调位置环：给定位置阶跃目标，调整 $K_p^{pos}, K_d^{pos}$ 使位置精确、稳定
4. 发送方波/三角波位置目标，观察跟踪效果

**验收标准**：位置阶跃响应超调 < 5%，稳态误差 < 1°。

#### 实验二：差速机器人纯追踪

**目标**：在仿真或 K3 机器人上实现纯追踪路径跟踪。

**步骤**：

1. 定义参考路径（直线 + 圆弧 + S 型）
2. 实现纯追踪算法
3. 测试不同前视距离 $L_d$ 对跟踪效果的影响
4. 对比纯追踪与简单 PID 转向的差异

```bob
  "实验参考路径"
  
  y ^
    |                       .--------.
    |                      /          \
    |    .-----.          /            \
    |   /       \        /              \
    |  /   "圆弧"\------/   "S 型"       \
    | /                                   \
    |/                                     \
    *------------------------------------------→ x
  "起点"        "直线段"                  "终点"
```


**图 10-11** 该框图展示了实验二：差速机器人纯追踪的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch10-11 该框图展示了实验二：差速机器人纯追踪的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

### 10.10 小结与习题

本章从 PID 出发，扩展到串级控制、前馈补偿、轨迹生成、MPC 和路径跟踪等高级运动控制方法。这些方法构成机器人"小脑"的执行层——将大脑规划的路径转化为精确、平滑的运动。

```bob
+--------+     +--------+     +--------+     +--------+     +--------+
|"串级"   |     |"前馈"   |     |"轨迹"   |     |"MPC"   |     |"路径"   |
|"PID"   |---->|"复合"   |---->|"生成"   |---->|"入门"  |---->|"跟踪"   |
+--------+     +--------+     +--------+     +--------+     +--------+
     |                              |                             |
     v                              v                             v
 "底层电机"                    "平滑运动"                     "大脑规划"
 "(第6,8章)"                  "（无冲击）"                   "(第14章Nav2)"
```


**图 10-12** 上图直观呈现了小结与习题的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch10-12 上图直观呈现了小结与习题的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

#### 习题

??? question "10-1 串级 PID 带宽"
    为什么串级 PID 要求内环带宽远大于外环？如果内环和外环使用相同的采样频率和增益，会出现什么问题？

??? question "10-2 梯形 vs S 曲线"
    分别用梯形速度曲线和 S 曲线生成从 0 到 1 米的运动轨迹（$v_{max}=0.5$ m/s，$a_{max}=1.0$ m/s²，$j_{max}=5.0$ m/s³），绘出位置、速度、加速度、加加速度的时间曲线并对比。

??? question "10-3 MPC 预测步长"
    MPC 的预测步数 $N$ 对控制性能和计算量有什么影响？设计实验：$N = 3, 10, 30$ 时差速机器人跟踪圆形轨迹的效果对比。

??? question "10-4 纯追踪前视距离"
    纯追踪的前视距离 $L_d$ 选择对路径跟踪有什么影响？$L_d$ 太小和太大分别会导致什么问题？设计一条包含急弯的路径来验证。

??? question "10-5 综合设计"
    设计一个完整的差速机器人轨迹跟踪系统，包括：（1）五次多项式轨迹生成器生成参考轨迹；（2）纯追踪或 Stanley 控制器输出 $(v, \omega)$；（3）串级 PID 底层控制左右轮电机。画出完整的控制框图，并讨论各环节的采样频率选择。


---

### 10.11 本章测验

<div id="exam-meta" data-exam-id="chapter10" data-exam-title="第十章 高级运动控制测验" style="display:none"></div>

<!-- mkdocs-quiz intro -->

<quiz>
1) 串级 PID 中，内环和外环的典型设计原则是什么？
- [x] 内环快、外环慢；内环带宽高于外环
- [ ] 内环慢、外环快；外环负责快速响应
- [ ] 内外环使用相同的 PID 参数
- [ ] 内环只用 P 控制，外环只用 I 控制

串级控制要求内环响应速度远快于外环（通常 5–10 倍），内环先稳定电流/速度，外环再调节位置/轨迹。内环带宽高于外环是保证稳定性的基本条件。
</quiz>

<quiz>
2) 梯形速度曲线相比 S 曲线（七段式）的主要缺点是什么？
- [x] 加速/减速段加加速度（jerk）不连续，导致机械冲击
- [ ] 运动时间更长
- [ ] 无法达到指定的最大速度
- [ ] 实现复杂度更高

梯形曲线的加速度在段间瞬变（阶跃），产生无穷大的 jerk，导致机械振动和冲击。S 曲线通过将加速度变化限制为有限值（有限 jerk）来消除冲击，但实现较复杂。
</quiz>

<quiz>
3) MPC（模型预测控制）相比 PID 的核心优势是什么？
- [x] 能在预测时域内考虑约束（如执行器饱和）并优化未来轨迹
- [ ] 计算量更低，适合资源受限的 MCU
- [ ] 不需要系统数学模型
- [ ] 参数调节比 PID 更简单

MPC 在每步求解一个带约束的优化问题，能系统性地处理输入/状态约束和多目标权衡。代价是计算量大（需在线求解优化），且需要较精确的系统模型。PID 实现简单但无法显式处理约束。
</quiz>

<quiz>
4) 纯追踪（Pure Pursuit）控制器中，前视距离 $L_d$ 对跟踪效果有何影响？
- [x] $L_d$ 越小跟踪越紧但容易振荡，$L_d$ 越大轨迹更平滑但可能切弯
- [ ] $L_d$ 只影响直线段跟踪，不影响弯道
- [ ] $L_d$ 越大跟踪精度越高
- [ ] $L_d$ 必须固定为一个常数

前视距离是纯追踪的唯一可调参数。小 $L_d$ 使机器人紧跟路径但在弯道处容易振荡；大 $L_d$ 平滑但会"切弯"偏离路径。工程中常用速度自适应策略：$L_d = L_0 + k_v \cdot v$。
</quiz>

<!-- mkdocs-quiz results -->

---
