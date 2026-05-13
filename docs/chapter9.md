---
number headings: first-level 2, start-at 9
---

## 9 第 9 章 传感器融合与状态估计

### 9.1 传感器融合概述

机器人在运动过程中需要精确地知道自身的位置、速度和姿态——这一信息统称为**状态（State）**。然而，任何单一传感器都有其局限性：

- **编码器**：累积误差（轮子打滑、地面不平）导致长期漂移
- **IMU（惯性测量单元）**：陀螺仪存在零偏漂移，加速度计受振动干扰
- **GPS**：室内不可用，室外精度受限（米级），更新率低（1-10 Hz）
- **激光雷达/相机**：受遮挡、光照变化影响，计算量大

**传感器融合**（Sensor Fusion）的核心思想是：利用多个传感器的**互补特性**，通过数学方法将它们的测量值融合，得到优于任何单一传感器的状态估计。

```bob
                            +-------------------+
   "编码器"  ──────────────→|                   |
                            |                   |
   "IMU"     ──────────────→|   "传感器融合"     |───→ "最优状态估计"
                            |   "算法"          |     (x, y, θ, v, ω)
   "GPS"     ──────────────→|                   |
                            |                   |
   "激光雷达" ─────────────→|                   |
                            +-------------------+
```


**图 9-1** 该框图展示了传感器融合概述的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch9-1 该框图展示了传感器融合概述的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

#### 9.1.1 融合的三种模式

**表 9-1** 融合的三种模式
<!-- tab:ch9-1 融合的三种模式 -->

| 融合模式 | 描述 | 典型场景 |
|---------|------|---------|
| **互补融合** | 不同传感器覆盖不同维度或频段 | IMU（高频姿态）+ GPS（低频位置） |
| **冗余融合** | 多个同类传感器测量同一量 | 双 IMU 交叉验证，提高可靠性 |
| **竞争融合** | 不同传感器测量同一量，选择最优 | 激光雷达 vs 视觉里程计，取置信度高者 |

通过上表的对比可以看出，不同方案在融合模式、描述、典型场景等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

#### 9.1.2 融合层级

```bob

  "数据级融合"              "特征级融合"              "决策级融合"
  (低层)                    (中层)                    (高层)

+---------------+     +------------------+     +------------------+
| "原始数据"     |     | "提取特征后"      |     | "各传感器独立"    |
| "直接合并"     |     | "匹配融合"        |     | "决策后投票"      |
| "如：点云拼接" |     | "如：特征匹配"    |     | "如：障碍物判定"  |
+---------------+     +------------------+     +------------------+
```


**图 9-2** 上图直观呈现了融合层级的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch9-2 上图直观呈现了融合层级的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

- **数据级**：在原始测量值层面融合（卡尔曼滤波对传感器原始读数的融合）
- **特征级**：先从各传感器提取特征，再融合特征（视觉特征 + 激光特征匹配）
- **决策级**：各传感器独立给出判断结果，最终投票或加权决策

本章主要聚焦**数据级融合**，即基于概率框架的状态估计方法。

### 9.2 概率基础与贝叶斯估计

#### 9.2.1 随机变量与高斯分布

机器人的状态和传感器测量都带有不确定性，我们用**概率**来描述这种不确定性。

一维高斯分布的概率密度函数：

$$
p(x) = \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)
$$

其中 $\mu$ 为均值（最可能的值），$\sigma^2$ 为方差（不确定性的大小）。

多维高斯分布：

$$
p(\mathbf{x}) = \frac{1}{\sqrt{(2\pi)^n |\boldsymbol{\Sigma}|}} \exp\left(-\frac{1}{2}(\mathbf{x}-\boldsymbol{\mu})^T \boldsymbol{\Sigma}^{-1} (\mathbf{x}-\boldsymbol{\mu})\right)
$$

其中 $\boldsymbol{\Sigma}$ 为协方差矩阵，描述各维度之间的不确定性及其关联。

#### 9.2.2 贝叶斯滤波框架

贝叶斯滤波是所有概率状态估计方法的统一框架，包含两个核心步骤：

**1. 预测（Prediction）**——利用运动模型预测下一时刻的状态：

$$
\overline{bel}(\mathbf{x}_t) = \int p(\mathbf{x}_t | \mathbf{u}_t, \mathbf{x}_{t-1}) \cdot bel(\mathbf{x}_{t-1}) \, d\mathbf{x}_{t-1}
$$

**2. 更新（Update/Correction）**——利用传感器观测修正预测：

$$
bel(\mathbf{x}_t) = \eta \cdot p(\mathbf{z}_t | \mathbf{x}_t) \cdot \overline{bel}(\mathbf{x}_t)
$$

其中：

- $bel(\mathbf{x}_t)$ 为 $t$ 时刻的状态置信度（后验概率）
- $\mathbf{u}_t$ 为控制输入（如电机指令）
- $\mathbf{z}_t$ 为传感器观测
- $\eta$ 为归一化常数

```bob
 "t-1 时刻"          "预测"            "t 时刻预测"        "更新"          "t 时刻估计"
+----------+     +-----------+     +--------------+     +----------+     +------------+
|          |     | "运动模型" |     |              |     | "观测模型"|     |            |
| bel(x_t-1)|--->| p(x_t|u,x)|--->| bel_bar(x_t) |--->| p(z_t|x_t)|--->| bel(x_t)   |
|          |     |           |     |              |     |          |     |            |
+----------+     +-----------+     +--------------+     +----------+     +------------+
                      ^                                      ^
                      |                                      |
                  "控制输入 u_t"                        "传感器观测 z_t"
```


**图 9-3** 上图以框图形式描绘了贝叶斯滤波框架的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch9-3 上图以框图形式描绘了贝叶斯滤波框架的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->


**表 9-2** 不同的概率假设和计算方法，产生不同的具体算法：
<!-- tab:ch9-2 不同的概率假设和计算方法，产生不同的具体算法： -->

| 算法 | 概率分布假设 | 系统模型假设 | 计算复杂度 |
|------|------------|------------|-----------|
| 卡尔曼滤波（KF） | 高斯 | 线性 | $O(n^3)$ |
| 扩展卡尔曼滤波（EKF） | 高斯 | 非线性（线性化） | $O(n^3)$ |
| 无迹卡尔曼滤波（UKF） | 高斯 | 非线性（Sigma点） | $O(n^3)$ |
| 粒子滤波（PF） | 任意 | 任意 | $O(N \cdot n)$ |

上表对贝叶斯滤波框架中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

### 9.3 卡尔曼滤波器（KF）

卡尔曼滤波（Kalman Filter）是线性高斯系统中的**最优状态估计器**。

#### 9.3.1 线性状态空间模型

$$
\mathbf{x}_t = \mathbf{A} \mathbf{x}_{t-1} + \mathbf{B} \mathbf{u}_t + \mathbf{w}_t, \quad \mathbf{w}_t \sim \mathcal{N}(\mathbf{0}, \mathbf{Q})
$$

$$
\mathbf{z}_t = \mathbf{H} \mathbf{x}_t + \mathbf{v}_t, \quad \mathbf{v}_t \sim \mathcal{N}(\mathbf{0}, \mathbf{R})
$$

其中：

- $\mathbf{A}$：状态转移矩阵
- $\mathbf{B}$：控制输入矩阵
- $\mathbf{H}$：观测矩阵
- $\mathbf{Q}$：过程噪声协方差
- $\mathbf{R}$：观测噪声协方差

#### 9.3.2 KF 五步公式

**预测阶段：**

$$
\hat{\mathbf{x}}_t^- = \mathbf{A} \hat{\mathbf{x}}_{t-1} + \mathbf{B} \mathbf{u}_t \tag{1. 状态预测}
$$

$$
\mathbf{P}_t^- = \mathbf{A} \mathbf{P}_{t-1} \mathbf{A}^T + \mathbf{Q} \tag{2. 协方差预测}
$$

**更新阶段：**

$$
\mathbf{K}_t = \mathbf{P}_t^- \mathbf{H}^T (\mathbf{H} \mathbf{P}_t^- \mathbf{H}^T + \mathbf{R})^{-1} \tag{3. 卡尔曼增益}
$$

$$
\hat{\mathbf{x}}_t = \hat{\mathbf{x}}_t^- + \mathbf{K}_t (\mathbf{z}_t - \mathbf{H} \hat{\mathbf{x}}_t^-) \tag{4. 状态更新}
$$

$$
\mathbf{P}_t = (\mathbf{I} - \mathbf{K}_t \mathbf{H}) \mathbf{P}_t^- \tag{5. 协方差更新}
$$

卡尔曼增益 $\mathbf{K}_t$ 的直观含义：

- 当 $\mathbf{R}$ 很大（观测噪声大）→ $\mathbf{K}_t$ 小 → 更相信预测
- 当 $\mathbf{P}_t^-$ 很大（预测不确定）→ $\mathbf{K}_t$ 大 → 更相信观测

#### 9.3.3 一维温度估计实例

假设一个温度传感器测量室温，真实温度恒定为 $25°C$，传感器噪声标准差为 $\sigma_R = 2°C$。

```python
import numpy as np

# 系统参数（一维，恒定温度）
A = 1.0   # 状态转移：温度不变
H = 1.0   # 观测矩阵：直接观测温度
Q = 0.01  # 过程噪声（温度可能微小变化）
R = 4.0   # 观测噪声方差 (2°C)^2

# 初始估计
x_hat = 20.0  # 初始猜测偏离真值
P = 10.0      # 初始不确定性很大

# 模拟观测数据
np.random.seed(42)
true_temp = 25.0
measurements = true_temp + np.random.randn(50) * 2.0

estimates = []
for z in measurements:
    # 预测
    x_pred = A * x_hat
    P_pred = A * P * A + Q
    
    # 更新
    K = P_pred * H / (H * P_pred * H + R)
    x_hat = x_pred + K * (z - H * x_pred)
    P = (1 - K * H) * P_pred
    
    estimates.append(x_hat)

print(f"最终估计: {x_hat:.2f}°C, 不确定性: {np.sqrt(P):.3f}°C")
# 输出：最终估计约 25.0°C，不确定性约 0.1°C
```

```bob
  "温度 °C"
    |
 28 + - - - - - - - * - - - - -* - - *  "观测值（噪声大）"
    |       *     *   *   *       *
 26 +    *     *       *     *      *
    |  *    *-----------*-------*-----*---  "KF 估计（平滑收敛）"
 24 + *  *        
    |*
 22 +
    |
 20 *  "初始猜测"
    +------+------+------+------+------→ "时间步"
    0     10     20     30     40     50
```

**图 9-4** 
<!-- fig:ch9-4  -->

### 9.4 扩展卡尔曼滤波（EKF）

现实中大多数系统是非线性的。扩展卡尔曼滤波通过**一阶泰勒展开（线性化）**将非线性系统近似为线性系统，然后应用标准 KF 公式。

#### 9.4.1 非线性状态空间模型

$$
\mathbf{x}_t = f(\mathbf{x}_{t-1}, \mathbf{u}_t) + \mathbf{w}_t
$$

$$
\mathbf{z}_t = h(\mathbf{x}_t) + \mathbf{v}_t
$$

其中 $f(\cdot)$ 和 $h(\cdot)$ 为非线性函数。

#### 9.4.2 雅可比矩阵

在当前估计点对非线性函数求偏导，得到雅可比矩阵：

$$
\mathbf{F}_t = \frac{\partial f}{\partial \mathbf{x}} \bigg|_{\hat{\mathbf{x}}_{t-1}, \mathbf{u}_t} \qquad \mathbf{H}_t = \frac{\partial h}{\partial \mathbf{x}} \bigg|_{\hat{\mathbf{x}}_t^-}
$$

EKF 公式与 KF 完全相同，只是将 $\mathbf{A}$ 替换为 $\mathbf{F}_t$，$\mathbf{H}$ 替换为 $\mathbf{H}_t$。

#### 9.4.3 差速机器人 EKF 定位

差速机器人的状态为 $\mathbf{x} = [x, y, \theta]^T$，运动模型（非线性）：

$$
f(\mathbf{x}, \mathbf{u}) = \begin{bmatrix} x + v \cos\theta \cdot \Delta t \\ y + v \sin\theta \cdot \Delta t \\ \theta + \omega \cdot \Delta t \end{bmatrix}
$$

其雅可比矩阵：

$$
\mathbf{F} = \frac{\partial f}{\partial \mathbf{x}} = \begin{bmatrix} 1 & 0 & -v \sin\theta \cdot \Delta t \\ 0 & 1 & v \cos\theta \cdot \Delta t \\ 0 & 0 & 1 \end{bmatrix}
$$

```python
import numpy as np

class DiffDriveEKF:
    def __init__(self, dt=0.1):
        self.dt = dt
        self.x = np.zeros(3)       # [x, y, theta]
        self.P = np.eye(3) * 0.1   # 初始协方差
        self.Q = np.diag([0.01, 0.01, 0.005])  # 过程噪声
        self.R = np.diag([0.5, 0.5])            # GPS 观测噪声 (x, y)
    
    def predict(self, v, omega):
        """运动模型预测"""
        theta = self.x[2]
        # 非线性状态转移
        self.x[0] += v * np.cos(theta) * self.dt
        self.x[1] += v * np.sin(theta) * self.dt
        self.x[2] += omega * self.dt
        # 雅可比矩阵
        F = np.array([
            [1, 0, -v * np.sin(theta) * self.dt],
            [0, 1,  v * np.cos(theta) * self.dt],
            [0, 0,  1]
        ])
        self.P = F @ self.P @ F.T + self.Q
    
    def update_gps(self, z_gps):
        """GPS 观测更新 (仅观测 x, y)"""
        H = np.array([
            [1, 0, 0],
            [0, 1, 0]
        ])
        y = z_gps - H @ self.x          # 观测残差
        S = H @ self.P @ H.T + self.R   # 残差协方差
        K = self.P @ H.T @ np.linalg.inv(S)  # 卡尔曼增益
        self.x = self.x + K @ y
        self.P = (np.eye(3) - K @ H) @ self.P
```

```bob
  y
  ^
  |           "GPS 观测 (x)"              "真实轨迹"
  |          x   x                      .--------.
  |        x       x                  .'          '.
  |       x    .----x---.           .'              '.
  |      x   .'    x     '.       .                  .
  |     x  .'       x      '.                        
  |    x  .          x       .
  |   x  '        "EKF估计"   '          
  |  x  . '------*--------'  .
  | x  .                      .
  |x  '                        '
  +--x------------------------------→ x
   "纯编码器（漂移）"
```


**图 9-5** 该框图展示了差速机器人 EKF 定位的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch9-5 该框图展示了差速机器人 EKF 定位的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

### 9.5 互补滤波与 IMU 姿态估计

#### 9.5.1 IMU 传感器特性

IMU 通常包含两种（或三种）传感器：

**表 9-3** IMU 传感器特性
<!-- tab:ch9-3 IMU 传感器特性 -->

| 传感器 | 测量量 | 优点 | 缺点 |
|-------|--------|------|------|
| **加速度计** | 线加速度（含重力） | 长期稳定，无漂移 | 受振动干扰，动态响应差 |
| **陀螺仪** | 角速度 | 高频响应快，不受振动影响 | 零偏漂移，长期误差累积 |
| **磁力计** | 地磁场方向 | 提供绝对航向参考 | 受周围磁场干扰大 |

关键观察：加速度计在**低频**可靠（长期不漂移），陀螺仪在**高频**可靠（短期精确）——天然互补。

#### 9.5.2 互补滤波原理

互补滤波（Complementary Filter）是一种简单高效的传感器融合方法，利用高通/低通滤波器组合：

$$
\hat{\theta} = \alpha \cdot (\hat{\theta}_{prev} + \omega_{gyro} \cdot \Delta t) + (1 - \alpha) \cdot \theta_{accel}
$$

- 第一项：陀螺仪积分值经**高通滤波**（保留快速变化，抑制漂移）
- 第二项：加速度计算出的角度经**低通滤波**（保留稳态，抑制振动）
- $\alpha$：融合系数，典型值 0.96-0.99（偏向信任陀螺仪短期精度）

```bob
                                  "高通"
   "陀螺仪 ω" ──→ "∫ 积分" ──→  [  α  ] ──┐
                                            +──→ "θ_hat 姿态估计"
   "加速度计 a" ──→ "atan2" ──→ [ 1-α ] ──┘
                                  "低通"
```


**图 9-6** 上图直观呈现了互补滤波原理的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch9-6 上图直观呈现了互补滤波原理的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

#### 9.5.3 STM32 互补滤波实现

```c
#include "mpu6050.h"
#include <math.h>

#define COMP_FILTER_ALPHA  0.98f

#define RAD_TO_DEG         57.295779513f
#define DEG_TO_RAD         0.017453293f

typedef struct {
    float roll;      // 横滚角
    float pitch;     // 俯仰角
    float yaw;       // 偏航角（仅陀螺积分，无磁力计则会漂移）
    float dt;        // 采样周期 (s)
} AttitudeEstimate;

void complementary_filter_update(AttitudeEstimate *att,
                                  float ax, float ay, float az,
                                  float gx, float gy, float gz)
{
    // 加速度计计算俯仰和横滚（静态条件下）
    float accel_pitch = atan2f(-ax, sqrtf(ay*ay + az*az)) * RAD_TO_DEG;
    float accel_roll  = atan2f(ay, az) * RAD_TO_DEG;
    
    // 陀螺仪积分
    float gyro_pitch = att->pitch + gy * att->dt;
    float gyro_roll  = att->roll  + gx * att->dt;
    
    // 互补滤波融合
    att->pitch = COMP_FILTER_ALPHA * gyro_pitch
               + (1.0f - COMP_FILTER_ALPHA) * accel_pitch;
    att->roll  = COMP_FILTER_ALPHA * gyro_roll
               + (1.0f - COMP_FILTER_ALPHA) * accel_roll;
    
    // 偏航角只能用陀螺积分（无磁力计参考）
    att->yaw += gz * att->dt;
}
```

#### 9.5.4 互补滤波 vs 卡尔曼滤波

**表 9-4** 互补滤波 vs 卡尔曼滤波
<!-- tab:ch9-4 互补滤波 vs 卡尔曼滤波 -->

| 维度 | 互补滤波 | 卡尔曼滤波 |
|------|---------|-----------|
| 理论基础 | 频域分析（高通+低通） | 概率论（最优估计） |
| 参数 | 1个（$\alpha$） | 多个（$\mathbf{Q}, \mathbf{R}$） |
| 计算量 | 极低（几次加减乘） | 较高（矩阵运算） |
| 多传感器扩展 | 困难 | 自然支持 |
| 最优性 | 近似最优 | 理论最优（线性高斯条件下） |
| 适用场景 | 资源受限的嵌入式系统 | 需要精确估计的场景 |

实际工程中，互补滤波因其极低的计算量，在 STM32 等资源受限平台上广泛使用。

### 9.6 无迹卡尔曼滤波（UKF）

EKF 通过线性化近似非线性函数，当非线性程度较大时，线性化误差可能很显著。UKF 提出了一种不同的思路：不对函数线性化，而是精心选取一组**Sigma 点**，让它们通过非线性函数变换，再从变换后的点恢复均值和协方差。

#### 9.6.1 Sigma 点采样

对 $n$ 维状态 $\hat{\mathbf{x}}$（协方差 $\mathbf{P}$），生成 $2n+1$ 个 Sigma 点：

$$
\chi_0 = \hat{\mathbf{x}}
$$

$$
\chi_i = \hat{\mathbf{x}} + \left(\sqrt{(n+\lambda)\mathbf{P}}\right)_i, \quad i=1,\ldots,n
$$

$$
\chi_{i+n} = \hat{\mathbf{x}} - \left(\sqrt{(n+\lambda)\mathbf{P}}\right)_i, \quad i=1,\ldots,n
$$

其中 $\lambda = \alpha^2(n+\kappa) - n$ 是缩放参数。

#### 9.6.2 UKF 算法流程

```bob
+------------------+        +------------------+        +------------------+
| "1. 生成"         |        | "2. 传播"         |        | "3. 恢复"         |
| "Sigma 点"        |------->| "通过非线性函数"   |------->| "加权均值"         |
| "围绕当前估计"     |        | f(χ_i)"或" h(χ_i) |        | "加权协方差"        |
+------------------+        +------------------+        +------------------+
                                     ↑
                              "无需求雅可比"
                              "无需线性化！"
```


**图 9-7** 上图以框图形式描绘了 UKF 算法流程的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch9-7 上图以框图形式描绘了 UKF 算法流程的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

**预测步骤：**

1. 对 $\hat{\mathbf{x}}_{t-1}, \mathbf{P}_{t-1}$ 生成 Sigma 点 $\chi_{t-1}^{(i)}$

2. 传播：$\chi_t^{(i)*} = f(\chi_{t-1}^{(i)}, \mathbf{u}_t)$
3. 恢复预测均值和协方差：$\hat{\mathbf{x}}_t^- = \sum w_i^m \chi_t^{(i)*}$，$\mathbf{P}_t^- = \sum w_i^c (\chi_t^{(i)*} - \hat{\mathbf{x}}_t^-)(\cdots)^T + \mathbf{Q}$

**更新步骤：**

4. 对预测状态重新生成 Sigma 点
5. 通过观测模型传播：$\mathcal{Z}_t^{(i)} = h(\chi_t^{(i)})$
6. 计算观测均值、协方差和互协方差
7. 计算卡尔曼增益并更新

#### 9.6.3 EKF vs UKF 对比

**表 9-5** EKF vs UKF 对比
<!-- tab:ch9-5 EKF vs UKF 对比 -->

| 维度 | EKF | UKF |
|------|-----|-----|
| 非线性处理 | 雅可比矩阵线性化 | Sigma 点传播 |
| 精度 | 一阶近似 | 二阶近似（更精确） |
| 实现难度 | 需要推导雅可比（易出错） | 无需推导雅可比（代码更通用） |
| 计算量 | $O(n^3)$ | $O(n^3)$（常数略大） |
| 适用场景 | 弱非线性系统 | 强非线性系统 |

通过上表的对比可以看出，不同方案在维度、EKF、UKF 等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

### 9.7 粒子滤波简介

当系统高度非线性或概率分布非高斯时（如多模态分布），卡尔曼系列滤波器不再适用。**粒子滤波**（Particle Filter）使用一组随机采样的"粒子"来表示任意概率分布。

#### 9.7.1 蒙特卡洛方法

核心思想：用大量随机样本（粒子）来近似概率分布。

$$
bel(\mathbf{x}_t) \approx \sum_{i=1}^{N} w_t^{(i)} \delta(\mathbf{x}_t - \mathbf{x}_t^{(i)})
$$

每个粒子 $\mathbf{x}_t^{(i)}$ 代表一个可能的状态假设，权重 $w_t^{(i)}$ 表示该假设的可信度。

#### 9.7.2 粒子滤波算法

```bob
  "粒子集合"     "采样预测"     "加权"         "重采样"        "新粒子集合"
 { x^(i) } ──→ "运动模型" ──→ "观测模型" ──→ "淘汰低权" ──→ { x'^(i) }
               "+ 噪声"       "计算权重"     "复制高权"
```


**图 9-8** 该框图展示了粒子滤波算法的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch9-8 该框图展示了粒子滤波算法的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

```python

import numpy as np

class ParticleFilter:
    def __init__(self, num_particles=1000, state_dim=3):
        self.N = num_particles
        # 初始化粒子：均匀分布在地图范围内
        self.particles = np.random.uniform(
            low=[0, 0, -np.pi],
            high=[10, 10, np.pi],
            size=(self.N, state_dim)
        )
        self.weights = np.ones(self.N) / self.N
    
    def predict(self, v, omega, dt, noise_std):
        """运动模型采样"""
        theta = self.particles[:, 2]
        # 给每个粒子加不同的噪声
        v_noisy = v + np.random.randn(self.N) * noise_std[0]
        omega_noisy = omega + np.random.randn(self.N) * noise_std[1]
        
        self.particles[:, 0] += v_noisy * np.cos(theta) * dt
        self.particles[:, 1] += v_noisy * np.sin(theta) * dt
        self.particles[:, 2] += omega_noisy * dt
    
    def update(self, z_observed, landmarks, sensor_noise):
        """观测更新权重"""
        for lm in landmarks:
            # 每个粒子到地标的预测距离
            dx = self.particles[:, 0] - lm[0]
            dy = self.particles[:, 1] - lm[1]
            predicted_dist = np.sqrt(dx**2 + dy**2)
            # 实际观测距离
            observed_dist = z_observed[landmarks.index(lm)]
            # 高斯似然
            self.weights *= np.exp(
                -0.5 * ((predicted_dist - observed_dist) / sensor_noise) ** 2
            )
        # 归一化
        self.weights /= np.sum(self.weights)
    
    def resample(self):
        """系统重采样"""
        cumsum = np.cumsum(self.weights)
        positions = (np.arange(self.N) + np.random.random()) / self.N
        indices = np.searchsorted(cumsum, positions)
        self.particles = self.particles[indices]
        self.weights = np.ones(self.N) / self.N
    
    def estimate(self):
        """加权均值估计"""
        return np.average(self.particles, weights=self.weights, axis=0)
```

#### 9.7.3 与 AMCL 的关系

ROS2 中的 AMCL（Adaptive Monte Carlo Localization）就是粒子滤波在机器人定位中的应用——将在第 14 章导航中详细使用。本章提供了理解 AMCL 的理论基础。

### 9.8 里程计融合：轮式 + IMU

这是移动机器人中最常见的传感器融合场景：将编码器里程计与 IMU 数据融合，得到更准确的里程计估计。

#### 9.8.1 编码器里程计误差模型

差速机器人通过左右轮编码器计算位移：

$$
\Delta s = \frac{\Delta s_L + \Delta s_R}{2}, \quad \Delta\theta = \frac{\Delta s_R - \Delta s_L}{L}
$$

误差来源：
- 轮径不一致：左右轮实际半径差异
- 轮子打滑：在光滑/不平地面
- 离散化误差：编码器分辨率有限
- 非理想接触：轮子不完全贴地

#### 9.8.2 IMU 误差模型

陀螺仪角速度测量：

$$
\omega_{meas} = \omega_{true} + b_\omega + n_\omega
$$

其中 $b_\omega$ 为缓慢变化的零偏（bias），$n_\omega$ 为白噪声。

零偏的建模（随机游走）：

$$
\dot{b}_\omega = n_b, \quad n_b \sim \mathcal{N}(0, \sigma_b^2)
$$

#### 9.8.3 融合 EKF 设计

状态向量扩展为包含 IMU 零偏：

$$
\mathbf{x} = [x, y, \theta, b_\omega]^T
$$

运动模型（使用编码器线速度 + IMU 角速度）：

$$
f(\mathbf{x}, \mathbf{u}) = \begin{bmatrix} x + v_{enc} \cos\theta \cdot \Delta t \\ y + v_{enc} \sin\theta \cdot \Delta t \\ \theta + (\omega_{imu} - b_\omega) \cdot \Delta t \\ b_\omega \end{bmatrix}
$$

融合策略：
- **线速度**来自编码器（编码器测速精度高）
- **角速度**来自 IMU（陀螺仪短期精度远优于差速里程计计算的角速度）
- **零偏 $b_\omega$** 作为状态量被滤波器在线估计

```bob
+----------+        +----------+
| "左编码器" |------->|          |
+----------+   v_L  |          |      +------+
                     | "里程计"  |--v-->|      |
+----------+   v_R  | "计算"    |      |      |
| "右编码器" |------->|          |      |      |
+----------+        +----------+      | "EKF" |---> "x, y, θ, b_ω"
                                      |      |
+----------+        +----------+      |      |
| "陀螺仪"  |------->| "去零偏"  |--ω-->|      |
+----------+        +----------+      +------+
                                         ^
                                         |
                                  "GPS/地标观测"
                                  "(可选)"
```


**图 9-9** 上图直观呈现了融合 EKF 设计的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch9-9 上图直观呈现了融合 EKF 设计的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

### 9.9 嵌入式状态估计实现

#### 9.9.1 定点化 EKF

在 STM32F103（无 FPU）上实现 EKF 需要考虑：

1. **定点数运算**：使用 Q16.16 格式替代浮点数
2. **查表法**：$\sin/\cos$ 使用查找表替代计算
3. **矩阵运算**：对 $4\times4$ 小矩阵手动展开循环

```c
// Q16.16 定点数类型
typedef int32_t fixed_t;
#define FIXED_SHIFT    16
#define FLOAT_TO_FIXED(f) ((fixed_t)((f) * (1 << FIXED_SHIFT)))
#define FIXED_TO_FLOAT(q) ((float)(q) / (1 << FIXED_SHIFT))
#define FIXED_MUL(a, b)   ((fixed_t)(((int64_t)(a) * (b)) >> FIXED_SHIFT))

// 正弦查找表 (0-90°, 256 entries)
static const int16_t sin_table[257] = {
    0, 402, 804, 1206, /* ... 省略 ... */ 32767
};

fixed_t fixed_sin(fixed_t angle_rad) {
    // 将弧度转换为表索引 [0, 1024)
    int32_t idx = (FIXED_MUL(angle_rad, FLOAT_TO_FIXED(162.97)) >> FIXED_SHIFT) & 0x3FF;
    // 利用对称性查表
    if (idx < 256) return sin_table[idx] << 1;
    else if (idx < 512) return sin_table[512 - idx] << 1;
    else if (idx < 768) return -(sin_table[idx - 512] << 1);
    else return -(sin_table[1024 - idx] << 1);
}
```

在带 FPU 的 STM32F4 上可以直接使用浮点运算，代码简洁许多。

#### 9.9.2 FreeRTOS 多任务架构

```bob
 "优先级高"                                          "优先级低"
+-------------+    +-------------+    +-------------+    +-----------+
| "IMU 采集"   |    | "编码器采集" |    | "EKF 融合"   |    | "OLED/串口"|
| "1000 Hz"   |    | "100 Hz"    |    | "100 Hz"    |    | "10 Hz"   |
| "DMA+中断"  |    | "定时器中断" |    | "消息队列"   |    | "显示位姿" |
+------+------+    +------+------+    +------+------+    +-----+-----+
       |                  |                  |                  |
       v                  v                  v                  v
  +---------+        +---------+        +---------+        +---------+
  | "Queue1" |------->|         |        |         |        |         |
  +---------+        | "Queue2" |------->| "EKF"   |------->| "显示"   |
                     |         |        | "任务"   |        | "任务"   |
                     +---------+        +---------+        +---------+
```


**图 9-10** 上图以框图形式描绘了 FreeRTOS 多任务架构的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch9-10 上图以框图形式描绘了 FreeRTOS 多任务架构的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

```c

// FreeRTOS 任务示例
#define IMU_QUEUE_SIZE    16
#define ODOM_QUEUE_SIZE   16

static QueueHandle_t xImuQueue;
static QueueHandle_t xOdomQueue;

typedef struct {
    float ax, ay, az;      // 加速度 (m/s²)
    float gx, gy, gz;      // 角速度 (rad/s)
    uint32_t timestamp_us;
} ImuData_t;

typedef struct {
    float v_left, v_right; // 左右轮速度 (m/s)
    uint32_t timestamp_us;
} OdomData_t;

// EKF 融合任务
void vEkfTask(void *pvParameters)
{
    EkfState_t ekf;
    ekf_init(&ekf);
    
    ImuData_t imu;
    OdomData_t odom;
    
    for (;;) {
        // 等待编码器数据（100 Hz 节拍驱动）
        if (xQueueReceive(xOdomQueue, &odom, pdMS_TO_TICKS(20)) == pdTRUE) {
            // 计算线速度
            float v = (odom.v_left + odom.v_right) / 2.0f;
            
            // 读取最新 IMU 数据
            while (xQueueReceive(xImuQueue, &imu, 0) == pdTRUE) {
                // 消耗队列中累积的 IMU 数据
            }
            float omega = imu.gz;  // 使用最新的陀螺仪角速度
            
            // EKF 预测 + 更新
            ekf_predict(&ekf, v, omega, 0.01f);  // dt = 10ms
            
            // 如果有外部观测（GPS/地标），执行更新
            // ekf_update_gps(&ekf, gps_x, gps_y);
        }
    }
}
```

#### 9.9.3 计算负载分析

**表 9-6** 计算负载分析
<!-- tab:ch9-6 计算负载分析 -->

| 平台 | 4维 EKF 单次耗时 | 占 100Hz 周期比例 |
|------|-----------------|-----------------|
| STM32F103 (72 MHz, 无 FPU) | ~150 μs（定点） | 1.5% |
| STM32F103 (72 MHz, 软浮点) | ~800 μs | 8.0% |
| STM32F407 (168 MHz, 有 FPU) | ~30 μs（浮点） | 0.3% |

即使在低端 STM32F103 上，4 维 EKF 也完全可以实时运行。

### 9.10 小结与习题

本章介绍了传感器融合与状态估计的核心方法，从贝叶斯滤波框架出发，依次讲授了卡尔曼滤波（KF/EKF/UKF）、互补滤波和粒子滤波，并结合差速机器人里程计融合展示了工程实现。

```bob
+--------+     +-----------+     +-----+     +-----+     +----------+
| "概率"  |     | "卡尔曼"   |     |"互补"|     |"UKF" |     | "粒子"    |
| "基础"  |---->| "滤波 KF"  |---->|"滤波"|---->|      |---->| "滤波"    |
+--------+     +-----------+     +-----+     +-----+     +----------+
                     |                                          |
                     v                                          v
               +-----------+                             +-----------+
               | "EKF"     |                             | "AMCL"    |
               | "差速定位" |                             | "(第14章)" |
               +-----------+                             +-----------+
```


**图 9-11** 该框图展示了小结与习题的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch9-11 该框图展示了小结与习题的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

#### 习题

??? question "9-1 KF 参数调优"
    考虑一维 KF 估计温度的场景。如果将过程噪声 $Q$ 增大 10 倍，卡尔曼滤波器的行为会如何变化？如果将观测噪声 $R$ 增大 10 倍呢？请分别分析并用代码验证。

??? question "9-2 EKF 雅可比推导"
    推导差速机器人运动模型关于控制输入 $\mathbf{u} = [v, \omega]^T$ 的雅可比矩阵 $\mathbf{G}_t = \frac{\partial f}{\partial \mathbf{u}}$。这个矩阵在 EKF 中有什么作用？

??? question "9-3 互补滤波参数选择"
    互补滤波的参数 $\alpha$ 设为 0.50 和 0.99 时，滤波器的频率响应有何不同？在什么条件下应选择较大的 $\alpha$？

??? question "9-4 粒子数量与精度"
    在粒子滤波中，粒子数量 $N$ 对估计精度和计算量有什么影响？设计实验验证：$N = 10, 100, 1000, 10000$ 时的估计收敛速度和最终误差。

??? question "9-5 综合设计"
    设计一个完整的里程计融合系统：使用编码器（100 Hz）和 IMU（1000 Hz）对差速机器人进行 EKF 定位。考虑：（1）如何处理两个传感器的不同更新率？（2）如何在线估计陀螺仪零偏？（3）如何检测轮子打滑？


---

### 9.11 本章测验

<div id="exam-meta" data-exam-id="chapter9" data-exam-title="第九章 传感器融合与状态估计测验" style="display:none"></div>

<!-- mkdocs-quiz intro -->

<quiz>
1) 卡尔曼滤波的预测步骤中，状态协方差矩阵 P 的变化趋势是什么？
- [x] P 增大（不确定性增加）
- [ ] P 减小（不确定性减小）
- [ ] P 保持不变
- [ ] P 的变化取决于观测噪声 R

预测步骤中 $P_{k|k-1} = F P_{k-1|k-1} F^T + Q$，过程噪声 Q 的叠加使协方差增大，反映了仅靠模型预测时不确定性的累积。更新步骤再利用观测信息将 P 缩小。
</quiz>

<quiz>
2) EKF 与 UKF 的核心区别是什么？
- [x] EKF 用雅可比矩阵线性化，UKF 用 Sigma 点传播
- [ ] EKF 只能处理线性系统，UKF 可处理非线性系统
- [ ] UKF 的计算量远低于 EKF
- [ ] EKF 需要粒子采样，UKF 不需要

EKF 对非线性函数做一阶泰勒展开（需推导雅可比矩阵），UKF 通过确定性采样的 Sigma 点直接传播概率分布，精度更高（二阶近似）且无需推导雅可比。两者都能处理非线性系统，计算量同为 $O(n^3)$。
</quiz>

<quiz>
3) 互补滤波器中参数 α 的物理意义是什么？
- [x] α 决定了对陀螺仪（高频）和加速度计（低频）的信任权重
- [ ] α 是卡尔曼增益的简化形式
- [ ] α 越大表示越信任加速度计
- [ ] α 的取值范围是 0 到 100

互补滤波公式 $\theta = \alpha(\theta + \omega \cdot dt) + (1-\alpha) \theta_{acc}$，α 接近 1 时更信任陀螺仪积分（高频响应好），接近 0 时更信任加速度计（低频稳定）。典型取值 0.95–0.98，并非卡尔曼增益但思想类似。
</quiz>

<quiz>
4) 以下哪些措施有助于提高 EKF 里程计融合系统的定位精度？
- [x] 在状态向量中加入陀螺仪零偏作为待估计量
- [x] 提高编码器的分辨率（每转脉冲数）
- [ ] 将过程噪声 Q 设为零以增加模型置信度
- [ ] 降低 EKF 的更新频率以减少计算开销

在线估计陀螺仪零偏可消除积分漂移，提高编码器分辨率可减小量化误差——两者都能改善精度。Q 设为零会使滤波器过度信赖模型而忽略实际扰动，降低更新频率会增大离散化误差。
</quiz>

<!-- mkdocs-quiz results -->

---
