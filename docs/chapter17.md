---
number headings: first-level 2, start-at 17
---

## 17 第 17 章 课程实验一：K3 机器人

> 本章通过 K3 教学机器人平台，将前述章节的理论知识（嵌入式编程、电机驱动、PID 控制、传感器融合）落地为可运行的完整系统。学生将完成从底层驱动到上层应用的全栈开发。

### 17.1 K3 机器人平台概述

#### 17.1.1 硬件架构

K3 是一款面向教学的轮式移动机器人，核心控制器采用 STM32F103，搭配丰富的传感器与执行器：

```bob
+-------------------------------------------------------------------+
|                    "K3 机器人硬件架构"                              |
+-------------------------------------------------------------------+
|                                                                   |
|  +------------------+    +------------------+    +---------------+ |
|  |  "主控制器"       |    |  "传感器模块"     |    | "通信模块"     | |
|  |  STM32F103RCT6   |    |  红外避障 x4     |    | WiFi ESP8266  | |
|  |  72MHz Cortex-M3 |<---+  超声波测距 x1   |    | 蓝牙 HC-05    | |
|  |  256KB Flash     |    |  循迹传感器 x5   |    | 串口 USART    | |
|  |  48KB SRAM       |    |  编码器 x2       |    +-------+-------+ |
|  +---------+--------+    +------------------+            |         |
|            |                                             |         |
|            v                                             v         |
|  +---------+--------+    +------------------+    +-------+-------+ |
|  |  "电机驱动"       |    |  "显示交互"       |    | "电源管理"     | |
|  |  TB6612FNG x2    |    |  OLED 128x64     |    | 7.4V 锂电池   | |
|  |  直流减速电机 x2  |    |  蜂鸣器           |    | LDO 3.3V/5V  | |
|  |  PWM 控制        |    |  LED 状态灯 x4   |    | 电压检测 ADC  | |
|  +------------------+    +------------------+    +---------------+ |
+-------------------------------------------------------------------+
```


**图 17-1** 上图直观呈现了硬件架构的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch17-1 上图直观呈现了硬件架构的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

#### 17.1.2 软件架构

K3 机器人的软件采用分层架构设计，与第 2 章介绍的设计模式一脉相承：

**表 17-1** 软件架构
<!-- tab:ch17-1 软件架构 -->

| 层次 | 模块 | 说明 |
|------|------|------|
| 应用层 | 任务调度器 | FreeRTOS 多任务管理，状态机控制 |
| 算法层 | PID 控制、循迹、避障 | 第8章 PID 理论的实际应用 |
| 驱动层 | 电机、传感器、OLED | 基于 HAL 的外设封装 |
| HAL 层 | STM32 HAL 库 | CubeMX 自动生成 |

通过上表的对比可以看出，不同方案在层次、模块、说明等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

### 17.2 实验一：电机驱动与速度闭环

#### 17.2.1 实验目标

- 理解 TB6612FNG 双 H 桥驱动原理
- 实现编码器测速功能
- 完成速度 PID 闭环控制
- 验证直线行走精度

#### 17.2.2 驱动原理

TB6612FNG 通过两路 PWM 信号控制两个电机的转速与方向：

```bob
              "TB6612FNG 驱动逻辑"

"STM32"                                          "电机"
+--------+     +---------------------------+     +--------+
|        |     |      TB6612FNG            |     |        |
| PA6 ---|---->| AIN1    AO1 |------------>|---->| M1+    |
| PA7 ---|---->| AIN2    AO2 |------------>|---->| M1-    |
| TIM3C1-|---->| PWMA                      |     |        |
|        |     |                           |     +--------+
| PB0 ---|---->| BIN1    BO1 |------------>|---->| M2+    |
| PB1 ---|---->| BIN2    BO2 |------------>|---->| M2-    |
| TIM3C2-|---->| PWMB                      |     |        |
|        |     |                           |     +--------+
| 3.3V --|---->| STBY                      |
+--------+     +---------------------------+
                    |               |
                   VCC            GND
                  "7.4V"
```


**图 17-2** 上图以框图形式描绘了驱动原理的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch17-2 上图以框图形式描绘了驱动原理的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

**方向控制真值表：**

**表 17-2** 
<!-- tab:ch17-2  -->

| AIN1 | AIN2 | 电机状态 |
|:----:|:----:|---------|
| H | L | 正转 |
| L | H | 反转 |
| L | L | 停止（滑行） |
| H | H | 制动 |

上表对驱动原理中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

#### 17.2.3 编码器测速

使用 STM32 的编码器模式读取光电编码器脉冲：

```c
/* 编码器初始化（TIM2, TIM4 编码器模式） */
void Encoder_Init(void) {
    /* CubeMX 已配置 TIM2/TIM4 为 Encoder Mode */
    HAL_TIM_Encoder_Start(&htim2, TIM_CHANNEL_ALL);
    HAL_TIM_Encoder_Start(&htim4, TIM_CHANNEL_ALL);
}

/* 获取编码器计数值并清零（每 10ms 调用一次） */
int16_t Encoder_Read(TIM_HandleTypeDef *htim) {
    int16_t count = (int16_t)__HAL_TIM_GET_COUNTER(htim);
    __HAL_TIM_SET_COUNTER(htim, 0);
    return count;
}

/* 速度计算（单位：cm/s） */
float Speed_Calculate(int16_t encoder_count) {
    /* 轮径 65mm, 编码器线数 330, 减速比 30:1 */
    /* 每圈脉冲 = 330 * 4 * 30 = 39600（四倍频） */
    float wheel_circumference = 3.14159f * 6.5f;  /* cm */
    float speed = (float)encoder_count / 396.0f * wheel_circumference * 100.0f;
    return speed;  /* cm/s */
}
```

#### 17.2.4 PID 速度闭环

```c
typedef struct {
    float Kp, Ki, Kd;
    float target;
    float integral;
    float last_error;
    float output;
} PID_t;

PID_t pid_left  = {.Kp = 8.0f, .Ki = 0.5f, .Kd = 1.0f};
PID_t pid_right = {.Kp = 8.0f, .Ki = 0.5f, .Kd = 1.0f};

float PID_Update(PID_t *pid, float measured, float dt) {
    float error = pid->target - measured;
    pid->integral += error * dt;

    /* 积分限幅 */
    if (pid->integral > 500.0f)  pid->integral = 500.0f;
    if (pid->integral < -500.0f) pid->integral = -500.0f;

    float derivative = (error - pid->last_error) / dt;
    pid->output = pid->Kp * error + pid->Ki * pid->integral + pid->Kd * derivative;
    pid->last_error = error;

    /* 输出限幅 */
    if (pid->output > 999.0f)  pid->output = 999.0f;
    if (pid->output < -999.0f) pid->output = -999.0f;

    return pid->output;
}
```

### 17.3 实验二：多传感器循迹

#### 17.3.1 实验目标

- 理解红外循迹传感器工作原理
- 实现 5 路循迹传感器数据融合
- 基于 PID 实现平滑循迹控制

#### 17.3.2 传感器布局

```bob
          "K3 底部循迹传感器布局（俯视）"

                 前进方向
                    |
                    v

          S1   S2   S3   S4   S5
          o    o    o    o    o
          |    |    |    |    |
     +----+----+----+----+----+----+
     |                              |
     |        K3 机器人底盘         |
     |                              |
     +-----+------------------+-----+
           |                  |
          "左轮"            "右轮"
```


**图 17-3** 该框图展示了传感器布局的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch17-3 该框图展示了传感器布局的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

#### 17.3.3 加权偏差算法

```c
/* 5 路传感器加权偏差计算 */
float TrackLine_GetError(uint8_t sensor[5]) {
    /* 权值：-2, -1, 0, +1, +2 */
    static const float weight[5] = {-2.0f, -1.0f, 0.0f, 1.0f, 2.0f};
    float weighted_sum = 0;
    int active_count = 0;

    for (int i = 0; i < 5; i++) {
        if (sensor[i]) {  /* 1 = 检测到黑线 */
            weighted_sum += weight[i];
            active_count++;
        }
    }

    if (active_count == 0) {
        return 999.0f;  /* 全部丢线，返回异常值 */
    }

    return weighted_sum / active_count;  /* 偏差范围 [-2, +2] */
}

/* 循迹 PID 控制 */
void TrackLine_Task(void *argument) {
    PID_t track_pid = {.Kp = 30.0f, .Ki = 0.0f, .Kd = 15.0f};
    uint8_t sensor[5];
    float base_speed = 25.0f;  /* cm/s */

    for (;;) {
        Sensor_ReadTrack(sensor);
        float error = TrackLine_GetError(sensor);

        if (error == 999.0f) {
            Motor_Stop();  /* 丢线停车 */
        } else {
            float correction = PID_Update(&track_pid, error, 0.01f);
            pid_left.target  = base_speed + correction;
            pid_right.target = base_speed - correction;
        }

        osDelay(10);
    }
}
```

### 17.4 实验三：超声波避障

#### 17.4.1 实验目标

- 掌握 HC-SR04 超声波传感器驱动
- 实现基于状态机的避障逻辑
- 对比反应式避障与规划式避障

#### 17.4.2 核心代码

```c
/* 超声波测距 (HC-SR04) */
float Ultrasonic_GetDistance(void) {
    uint32_t start, end;

    /* 发送 10us 触发脉冲 */
    HAL_GPIO_WritePin(TRIG_GPIO, TRIG_PIN, GPIO_PIN_SET);
    delay_us(10);
    HAL_GPIO_WritePin(TRIG_GPIO, TRIG_PIN, GPIO_PIN_RESET);

    /* 等待 Echo 上升沿 */
    while (!HAL_GPIO_ReadPin(ECHO_GPIO, ECHO_PIN));
    start = __HAL_TIM_GET_COUNTER(&htim1);

    /* 等待 Echo 下降沿 */
    while (HAL_GPIO_ReadPin(ECHO_GPIO, ECHO_PIN));
    end = __HAL_TIM_GET_COUNTER(&htim1);

    /* 计算距离 (cm) */
    return (float)(end - start) * 0.017f;
}

/* 避障状态机 */
typedef enum {
    STATE_FORWARD,
    STATE_TURN_LEFT,
    STATE_TURN_RIGHT,
    STATE_BACKWARD
} Obstacle_State_t;

void Obstacle_Task(void *argument) {
    Obstacle_State_t state = STATE_FORWARD;
    float distance;
    uint32_t turn_tick = 0;

    for (;;) {
        distance = Ultrasonic_GetDistance();

        switch (state) {
            case STATE_FORWARD:
                pid_left.target = 20.0f;
                pid_right.target = 20.0f;
                if (distance < 25.0f) {
                    state = STATE_TURN_LEFT;
                    turn_tick = osKernelGetTickCount();
                }
                break;

            case STATE_TURN_LEFT:
                pid_left.target = -15.0f;
                pid_right.target = 15.0f;
                if (osKernelGetTickCount() - turn_tick > 500) {
                    state = STATE_FORWARD;
                }
                break;

            default:
                state = STATE_FORWARD;
                break;
        }

        osDelay(50);
    }
}
```

### 17.5 实验四：OLED 状态显示

#### 17.5.1 实验目标

- 掌握 I2C 通信驱动 OLED
- 实现机器人运行状态实时显示
- 理解嵌入式 GUI 的基本方法

#### 17.5.2 显示界面设计

```bob
+------------------------------+
|  "K3 Robot  v1.0"            |
|------------------------------|
|  "Mode: Track  Batt: 7.2V"  |
|  "L:25.3 cm/s R:24.8 cm/s"  |
|  "Dist: 42.5cm  Err: 0.3"   |
+------------------------------+
      "OLED 128x64 显示"
```


**图 17-4** 上图直观呈现了显示界面设计的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch17-4 上图直观呈现了显示界面设计的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

### 17.6 综合实验：自主巡航任务

#### 17.6.1 任务描述

综合运用前述实验的所有功能，完成以下自主巡航任务：

1. 机器人从起点出发，沿黑线循迹前进
2. 遇到障碍物时切换为避障模式，绕过障碍物后重新寻找黑线
3. 到达终点后自动停车并通过蜂鸣器提示
4. 全程在 OLED 上实时显示状态信息

#### 17.6.2 任务调度框架

```c
/* FreeRTOS 任务创建 */
void App_Init(void) {
    /* 高优先级：PID 速度控制（1kHz） */
    osThreadNew(MotorPID_Task, NULL, &(osThreadAttr_t){
        .name = "PID", .priority = osPriorityRealtime, .stack_size = 512
    });

    /* 中优先级：传感器采集（100Hz） */
    osThreadNew(Sensor_Task, NULL, &(osThreadAttr_t){
        .name = "Sensor", .priority = osPriorityHigh, .stack_size = 512
    });

    /* 中优先级：导航决策（50Hz） */
    osThreadNew(Navigation_Task, NULL, &(osThreadAttr_t){
        .name = "Nav", .priority = osPriorityAboveNormal, .stack_size = 1024
    });

    /* 低优先级：显示更新（10Hz） */
    osThreadNew(Display_Task, NULL, &(osThreadAttr_t){
        .name = "OLED", .priority = osPriorityNormal, .stack_size = 512
    });
}

/* 导航决策任务 */
void Navigation_Task(void *argument) {
    typedef enum { NAV_TRACK, NAV_AVOID, NAV_STOP } NavState_t;
    NavState_t state = NAV_TRACK;

    for (;;) {
        switch (state) {
            case NAV_TRACK:
                TrackLine_Control();
                if (Ultrasonic_GetDistance() < 20.0f) {
                    state = NAV_AVOID;
                }
                if (Sensor_AllBlack()) {
                    state = NAV_STOP;  /* 终点检测 */
                }
                break;

            case NAV_AVOID:
                Obstacle_Avoidance();
                if (Sensor_AnyTrack()) {
                    state = NAV_TRACK;  /* 重新找到黑线 */
                }
                break;

            case NAV_STOP:
                Motor_Stop();
                Buzzer_Beep(3);
                osThreadExit();
                break;
        }
        osDelay(20);
    }
}
```

### 17.7 本章小结


**表 17-3** 本章通过 K3 教学机器人平台，将课程前半部分的核心知识串联为一个完整的工程项目：
<!-- tab:ch17-3 本章通过 K3 教学机器人平台，将课程前半部分的核心知识串联为一个完整的工程项目： -->

| 实验内容 | 对应章节知识 |
|----------|-------------|
| 电机驱动与速度闭环 | 第5章（定时器PWM）、第6章（电机驱动）、第8章（PID） |
| 多传感器循迹 | 第3章（GPIO/ADC）、第8章（PID） |
| 超声波避障 | 第2章（状态机模式）、第3章（GPIO定时器） |
| OLED 显示 | 第3章（I2C通信） |
| 综合巡航 | 第4章（FreeRTOS多任务）、第2章（分层架构） |

以上内容归纳了本章小结的关键要素，为后续深入学习和工程实践提供了参考依据。

### 17.8 本章测验

<div id="exam-meta" data-exam-id="chapter13" data-exam-title="第 17 章 K3 机器人实验 测验" style="display:none"></div>

<!-- mkdocs-quiz intro -->

<quiz>
1) 在 K3 机器人的速度闭环控制中，编码器的主要作用是？
- [ ] 控制电机方向
- [ ] 提供 PWM 信号
- [x] 测量电机实际转速，作为 PID 反馈量
- [ ] 检测障碍物距离

编码器将电机转动转化为脉冲信号，用于测量实际转速，是速度闭环控制中反馈环节的核心传感器。
</quiz>

<quiz>
2) K3 机器人 5 路循迹传感器的加权偏差算法中，权值从左到右为 -2, -1, 0, +1, +2。若仅 S4 和 S5 检测到黑线，偏差值为？
- [ ] 0.5
- [ ] 1.0
- [x] 1.5
- [ ] 2.0

偏差 = (1 + 2) / 2 = 1.5，表示机器人偏向左侧，需要右转修正。
</quiz>

<quiz>
3) 在 FreeRTOS 任务调度中，为何将 PID 速度控制任务设为最高优先级？
- [ ] 因为它的代码最复杂
- [ ] 因为它需要最多的栈空间
- [x] 因为电机控制需要最高的实时性，延迟会导致速度波动
- [ ] 因为它是最先创建的任务

电机 PID 控制需要稳定的执行周期（1kHz），任何延迟都会导致控制效果下降，因此必须设为最高优先级。
</quiz>

<quiz>
4) HC-SR04 超声波传感器测距的原理是？
- [x] 发送超声波脉冲，测量回波时间，根据声速计算距离
- [ ] 通过红外线反射强度判断距离
- [ ] 利用电磁波多普勒效应测速
- [ ] 通过激光三角测量法计算距离

HC-SR04 发送 40kHz 超声波脉冲，测量 Echo 引脚高电平持续时间，距离 = 时间 × 声速 / 2。
</quiz>

<quiz>
5) K3 机器人综合巡航任务中，从循迹模式切换到避障模式的触发条件是？
- [ ] 所有循迹传感器检测到黑线
- [ ] 电池电压低于阈值
- [x] 超声波传感器检测到前方障碍物距离小于安全阈值
- [ ] 编码器计数达到预设值

当超声波检测到前方障碍物距离小于安全阈值（如 20cm）时，状态机从 NAV_TRACK 切换到 NAV_AVOID。
</quiz>

<!-- mkdocs-quiz results -->
