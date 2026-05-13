---
number headings: first-level 2, start-at 7
---

## 7 第 7 章 机器人硬件仿真（PicSimlab 与 Renode）

> 硬件仿真是嵌入式开发的利器，允许在没有实物硬件的情况下进行软件开发、调试与测试。本章介绍两种主流仿真工具：面向教学的 PicSimlab 和面向高级场景的 Renode。

### 7.1 PicSimlab 仿真器简介

#### 7.1.1 为什么选择仿真器


**表 7-1** 嵌入式开发的学习门槛在于：**代码不能在普通计算机上直接运行**，必须依赖真实的硬件开发板。然而，硬件存在以下限制：
<!-- tab:ch7-1 嵌入式开发的学习门槛在于：**代码不能在普通计算机上直接运行**，必须依赖真实的硬件开发板。然而，硬件存在以下限制： -->

| 问题 | 说明 |
|------|------|
| 成本问题 | 开发板、传感器、杜邦线等器件需要一定费用 |
| 调试困难 | 硬件故障与代码 bug 难以区分，排查耗时 |
| 携带不便 | 外出或宿舍学习时不方便搭建硬件环境 |
| 烧录风险 | 操作不当可能损坏芯片或外设 |

**仿真器**（Simulator）能够在软件层面模拟真实硬件的行为，允许开发者在没有实物硬件的条件下：

- ✅ 编写并运行嵌入式程序
- ✅ 观察 GPIO 电平、PWM 波形、ADC 采样值
- ✅ 调试串口通信
- ✅ 验证控制逻辑的正确性

> 💡 仿真器不能完全替代真实硬件，但在**学习阶段**和**初期验证阶段**，仿真器是效率最高的工具。

#### 7.1.2 PicSimlab 概述

**PicSimlab**（PIC Simulator Lab）是一款开源、跨平台的微控制器仿真软件，由巴西开发者 lcgamboa 主导开发。尽管名称中包含"PIC"，但它同样支持 **STM32 系列微控制器**的仿真，这正是本章使用它的原因。

**PicSimlab 的核心特性：**

**表 7-2** PicSimlab 概述
<!-- tab:ch7-2 PicSimlab 概述 -->

| 特性 | 说明 |
|------|------|
| 开源免费 | GitHub 开源，完全免费使用 |
| 跨平台 | 支持 Windows、Linux、macOS |
| 支持 STM32 | 通过 QEMU 后端仿真 STM32F103C8T6（Blue Pill） |
| 可视化外设 | 提供 LED、按键、电位器、LCD、示波器等虚拟外设 |
| 直接加载固件 | 无需修改代码，直接加载 CubeIDE 编译产物 `.bin` |
| 串口终端 | 内置虚拟串口，可与 USART 实时交互 |
| 示波器 | 可观察 GPIO 电平变化和 PWM 波形 |

**官方资源：**

```text
GitHub:  https://github.com/lcgamboa/picsimlab
文档:    https://lcgamboa.github.io/picsimlab_docs/

```

#### 7.1.3 安装与界面

**下载安装（以 Windows 为例）：**

① 访问 GitHub Releases 页面，下载最新版 `picsimlab_win_XX.zip`  
② 解压后双击 `picsimlab.exe` 即可运行（无需安装）  
③ 首次运行会在 `%USERPROFILE%/.picsimlab/` 创建配置目录

**主界面布局：**

```text
┌─────────────────────────────────────────────────────────────────┐
│  File  Edit  Board  View  Tools  About              [菜单栏]    │
├──────────────────┬──────────────────────────────────────────────┤
│                  │                                              │
│   [板卡视图]     │           [外设区域 / Parts]                 │
│                  │                                              │
│  ┌────────────┐  │   ┌──────┐  ┌──────┐  ┌──────────┐         │
│  │  STM32     │  │   │ LED  │  │ BTN  │  │   POT    │         │
│  │  Blue Pill │  │   │      │  │      │  │          │         │
│  │  (QEMU)    │  │   └──────┘  └──────┘  └──────────┘         │
│  └────────────┘  │                                              │
│                  │   ┌────────────────────────────────────┐     │
│  [运行/暂停/重置] │   │  虚拟示波器 / UART 终端              │     │
│                  │   └────────────────────────────────────┘     │
└──────────────────┴──────────────────────────────────────────────┘
```

**界面区域说明：**

**表 7-3** 
<!-- tab:ch7-3  -->

| 区域 | 功能 |
|------|------|
| 板卡视图 | 显示仿真的微控制器芯片，可查看引脚状态 |
| 外设区域 | 拖入 LED、按键、电位器等虚拟组件并连接到引脚 |
| 示波器 | 实时显示选定引脚的电压波形 |
| UART 终端 | 与 MCU 的 USART 进行文本通信 |
| 控制栏 | 运行（▶）、暂停（⏸）、重置（⟳）仿真 |

上表对安装与界面的核心信息进行了结构化整理，读者可根据需要快速查阅相关内容。

#### 7.1.4 选择 STM32 仿真板卡

启动 PicSimlab 后，需要先选择仿真目标板卡：

① 点击菜单 **Board → Change Board**  

② 在列表中找到并选择 **`stm32_blue_pill`**（基于 STM32F103C8T6）  
③ 确认后界面切换至 STM32 Blue Pill 仿真界面

> ⚠️ **注意：** PicSimlab 对 STM32 的仿真基于 QEMU，需要确保系统已安装 QEMU ARM 组件。在 Windows 下，PicSimlab 安装包通常已内置 QEMU，无需单独安装。

---

### 7.2 仿真开发工作流

#### 7.2.1 完整开发流程

PicSimlab 与 CubeMX / CubeIDE 的联合开发工作流分为三个阶段：

```text
  ┌──────────────┐     ┌──────────────────┐     ┌────────────────┐
  │   CubeMX     │────▶│    CubeIDE       │────▶│   PicSimlab    │
  │              │     │                  │     │                │
  │ · 芯片选型   │     │ · 编写业务逻辑   │     │ · 加载 .bin    │
  │ · 引脚配置   │     │ · 编译工程       │     │ · 连接虚拟外设 │
  │ · 外设初始化 │     │ · 生成 .bin      │     │ · 运行仿真     │
  │ · 生成代码   │     │                  │     │ · 观察结果     │
  └──────────────┘     └──────────────────┘     └────────────────┘
        ①                      ②                        ③
    配置与生成               编码与编译                仿真验证
```

**步骤 ① — CubeMX 配置**

1. 选择芯片 `STM32F103C8Tx`
2. 配置 RCC：HSE → Crystal/Ceramic Resonator
3. 配置 SYS：Debug → Serial Wire
4. 按项目需求配置外设（GPIO / TIM / ADC / USART）
5. 时钟树设置 HCLK = 72 MHz
6. 生成代码（Toolchain: STM32CubeIDE）

**步骤 ② — CubeIDE 编译**

1. 打开生成的工程
2. 在 `USER CODE BEGIN` 区域编写应用代码
3. 选择 **Debug** 或 **Release** 配置
4. 点击 **Build Project**（Ctrl+B）
5. 编译产物位于 `Debug/` 目录下，找到 `.bin` 文件

**步骤 ③ — PicSimlab 仿真**

1. 选择对应板卡（stm32_blue_pill）
2. 点击 **File → Load Hex/Bin**，选择编译出的 `.bin` 文件
3. 在外设区域添加所需虚拟组件（LED / 按键 / 电位器等）
4. 右键组件 → **Properties**，将组件引脚映射到 MCU 对应引脚
5. 点击 ▶ 运行仿真

#### 7.2.2 常用虚拟外设对照表

**表 7-4** 常用虚拟外设对照表
<!-- tab:ch7-4 常用虚拟外设对照表 -->

| 组件名称 | 类型 | 典型用途 | 连接方式 |
|---------|------|---------|---------|
| LED | 输出显示 | 指示灯、流水灯 | 阳极接 GPIO，阴极接 GND |
| Push Button | 数字输入 | 按键触发 | 一端接 GPIO，一端接 GND（配合上拉） |
| Potentiometer | 模拟输入 | 模拟电压（ADC 测试）| 中间抽头接 ADC 引脚，两端接 VCC/GND |
| LCD 16×2 | 输出显示 | 文字信息显示 | 并口或 I2C 连接 |
| Buzzer | 输出 | 蜂鸣器（PWM 驱动）| 正极接 PWM 引脚，负极接 GND |
| Servo Motor | 输出 | 舵机角度控制 | 信号线接 PWM 引脚 |
| UART Terminal | 串口终端 | 串口收发调试 | TX/RX 连接 USART 引脚 |
| Oscilloscope | 观测工具 | 电平与波形观察 | 探针连接目标引脚 |

通过上表的对比可以看出，不同方案在组件名称、类型、典型用途等等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

#### 7.2.3 常见问题与调试技巧

**表 7-5** 常见问题与调试技巧
<!-- tab:ch7-5 常见问题与调试技巧 -->

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 程序不运行 | .bin 文件路径错误或格式不对 | 确认选择的是 Debug/.bin 文件 |
| LED 不亮 | 引脚映射错误 | 检查组件属性中的引脚编号是否与代码一致 |
| 串口无输出 | 波特率不匹配 | PicSimlab UART 终端波特率需与代码一致 |
| 仿真速度慢 | QEMU 仿真开销 | 调低系统时钟或关闭不必要的示波器通道 |
| ADC 值始终为 0 | 电位器未正确连接 | 检查 ADC 输入引脚编号，确认电位器两端有电源 |

---

#### 7.3.1 命令行启动与 PWZ 工程文件

PicSimlab 支持通过命令行直接启动仿真，跳过手动选板卡和加载固件的步骤，显著加快开发-调试循环。

**PWZ 文件**（PicSimlab Workspace ZIP）是 PicSimlab 的项目打包格式，包含：

**表 7-6** 命令行启动与 PWZ 工程文件
<!-- tab:ch7-6 命令行启动与 PWZ 工程文件 -->

| 文件内容 | 说明 |
|----------|------|
| 板卡配置 | 仿真目标板型（如 stm32_blue_pill） |
| 外设布局 | 虚拟组件位置与引脚映射 |
| ROM/固件 | 自动加载的 .hex/.bin 文件 |
| 仿真参数 | 时钟频率、波特率等配置 |

**命令行启动语法：**

```bash
# 直接加载 PWZ 工程文件启动仿真
picsimlab --file=my_project.pwz

# 指定板卡 + 固件（不使用 PWZ）

picsimlab --board=stm32_blue_pill --firmware=Debug/project.bin

# 无头模式（用于 CI 自动化测试）
picsimlab --file=my_project.pwz --nogui
```

**创建 PWZ 工程文件的步骤：**

1. 在 PicSimlab GUI 中完成板卡选择、外设布局和固件加载
2. 确认仿真运行正常
3. 点击 **File → Save Workspace** 保存为 `.pwz` 文件
4. 此后每次开发只需双击 `.pwz` 即可恢复完整仿真环境

```bob
  "开发流程加速"

  传统流程：                          PWZ 流程：
  ┌──────────────┐                   ┌──────────────┐
  │ 启动 PicSimlab│                   │ 双击 .pwz    │
  ├──────────────┤                   │ 或 CLI 启动   │
  │ 选择板卡     │                   ├──────────────┤
  ├──────────────┤                   │ 自动恢复全部 │
  │ 添加外设     │                   │ 配置与固件   │
  ├──────────────┤                   ├──────────────┤
  │ 配置引脚映射 │                   │ 运行仿真 ▶   │
  ├──────────────┤                   └──────────────┘
  │ 加载固件     │                      仅需 1 步
  ├──────────────┤
  │ 运行仿真 ▶   │
  └──────────────┘
     需要 5 步
```

**图 7-1** 
<!-- fig:ch7-1  -->

> **优势：** CLI + PWZ 模式将每次调试的仿真启动时间从数分钟缩短到秒级。在团队协作中，PWZ 文件可纳入 Git 版本控制，确保所有开发者使用相同的仿真环境。

#### 7.3.2 GDB 远程调试与 CubeIDE 集成

PicSimlab 内置 GDB Server 功能，可通过网络（TCP）连接到 CubeIDE 或 VSCode，实现**源代码级单步调试**，与调试真实硬件的体验完全一致。

**原理架构：**

```bob
  ┌──────────────────┐     TCP:1234     ┌──────────────────┐

  │   "CubeIDE"      │<───────────────>│   "PicSimlab"    │
  │                  │                  │                  │

  │ · 源码编辑       │  GDB RSP 协议    │ · QEMU 仿真引擎 │
  │ · 断点设置       │<───────────────>│ · GDB Server     │
  │ · 变量监视       │                  │ · 虚拟外设       │
  │ · 调用栈查看     │                  │                  │
  └──────────────────┘                  └──────────────────┘
```


**图 7-2** 上图直观呈现了 GDB 远程调试与 CubeIDE 集成的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch7-2 上图直观呈现了 GDB 远程调试与 CubeIDE 集成的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

**配置步骤：**

**① PicSimlab 端 — 启用 GDB Server**

1. 打开 PicSimlab，加载工程（或通过 CLI 启动）
2. 点击菜单 **Debug → Enable Remote Control**
3. GDB Server 默认监听端口 **1234**（可在设置中修改）
4. 状态栏显示 `GDB: listening on port 1234`

**② CubeIDE 端 — 配置远程 GDB 调试**

1. 打开编译好的工程
2. 菜单 **Run → Debug Configurations...**
3. 双击 **GDB Hardware Debugging** 新建配置
4. 配置关键参数：

**表 7-7** 
<!-- tab:ch7-7  -->

| 配置项 | 值 | 说明 |
|--------|-----|------|
| C/C++ Application | `Debug/project.elf` | 含调试符号的 ELF 文件 |
| GDB Command | `arm-none-eabi-gdb` | ARM GDB 路径 |
| Remote Target | `localhost:1234` | PicSimlab GDB Server 地址 |
| Load image | 取消勾选 | 固件已由 PicSimlab 加载 |

5. 在 **Startup** 选项卡中取消 "Reset and Delay" 和 "Halt"
6. 点击 **Debug** 启动调试

**③ 调试操作**

连接成功后，CubeIDE 自动切换到 Debug 透视图，可执行：

- **设置断点**：在源码行号处点击，PicSimlab 仿真会在该处暂停
- **单步执行**：Step Into（F5）/ Step Over（F6）/ Step Return（F7）
- **变量监视**：在 Variables 或 Expressions 视图中查看全局/局部变量实时值
- **寄存器查看**：在 Registers 视图中查看 ARM 内核寄存器和外设寄存器
- **内存查看**：Memory 视图直接读取 MCU 地址空间

```bash
# 也可在终端中直接使用 GDB 命令行
arm-none-eabi-gdb Debug/project.elf
(gdb) target remote localhost:1234
(gdb) break main
(gdb) continue
(gdb) print counter_value
(gdb) info registers
```

> **优势：** 无需任何调试硬件（ST-Link/J-Link），即可在仿真环境中进行完整的源码级调试，特别适合无硬件条件的远程教学和 CI 环境。

#### 7.3.3 UART Monitor 插件与 VSCode 串口调试

PicSimlab 的 UART Terminal 组件可将仿真中的串口输出重定向到外部工具，结合 VSCode 实现**串口日志实时监控**和**自动化测试**。

**方案一：TCP 串口桥接**

PicSimlab 支持将 UART 输出通过 TCP socket 转发，外部工具（如 VSCode 或 Python 脚本）通过网络连接获取串口数据。

```bob
  ┌──────────────┐   UART TX   ┌──────────────┐  TCP:5000  ┌──────────┐
  │  "STM32 固件" │───────────>│  "PicSimlab"  │──────────>│ "VSCode"  │
  │  printf()    │             │  UART→TCP    │            │ 串口监视 │
  │  HAL_UART.. │             │  Bridge      │            │ 自动化   │
  └──────────────┘             └──────────────┘            └──────────┘
```


**图 7-3** 上图以框图形式描绘了 UART Monitor 插件与 VSCode 串口调试的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch7-3 上图以框图形式描绘了 UART Monitor 插件与 VSCode 串口调试的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

配置步骤：

1. 在 PicSimlab 中添加 **UART Terminal** 组件，连接到 USART1 的 TX/RX 引脚
2. 右键 UART Terminal → **Properties** → 启用 **TCP Server** 模式
3. 设置监听端口（默认 5000）
4. 在 VSCode 中使用终端连接：

```bash
# 方式 1：nc/socat 直接查看串口输出

nc localhost 5000

# 方式 2：socat 创建虚拟串口，供 VSCode Serial Monitor 使用
socat pty,link=/tmp/vserial0,raw TCP:localhost:5000 &
# 然后在 VSCode Serial Monitor 中打开 /tmp/vserial0
```

**方案二：Python 自动化测试**

通过 TCP 连接获取串口输出，编写自动化测试脚本验证固件行为：

```python
import socket
import time

def test_uart_output():
    """自动化测试：验证固件串口输出"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 5000))
    sock.settimeout(5.0)

    collected = b''
    try:
        while True:
            data = sock.recv(1024)
            if not data:
                break
            collected += data
            output = collected.decode('utf-8', errors='ignore')

            # 断言：检查预期输出
            if 'System Init OK' in output:
                print('[PASS] 系统初始化成功')
            if 'Temperature:' in output:
                temp = float(output.split('Temperature:')[1].split()[0])
                assert 20.0 <= temp <= 40.0, f'温度异常: {temp}'
                print(f'[PASS] 温度读取正常: {temp}°C')
    except socket.timeout:
        pass
    finally:
        sock.close()

    # 最终验证
    output = collected.decode('utf-8', errors='ignore')
    assert 'System Init OK' in output, '未检测到初始化消息'
    print('[ALL PASSED] 串口自动化测试通过')

if __name__ == '__main__':
    test_uart_output()
```

**完整的 CI 测试流程：**

```bob
  ┌─────────┐    ┌─────────────┐    ┌──────────┐    ┌─────────┐
  │ "编译"   │───>│ "PicSimlab"  │───>│ "Python"  │───>│ "报告"   │
  │ 固件.bin │    │ CLI + PWZ   │    │ TCP 连接  │    │ PASS/   │
  │         │    │ 自动加载    │    │ 串口断言  │    │ FAIL    │
  └─────────┘    └─────────────┘    └──────────┘    └─────────┘
```


**图 7-4** 该框图展示了然后在 VSCode Serial Monitor 中打开 /tmp/vserial0 的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch7-4 该框图展示了然后在 VSCode Serial Monitor 中打开 /tmp/vserial0 的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

**表 7-8** 
<!-- tab:ch7-8  -->

| 步骤 | 命令/操作 | 说明 |
|------|----------|------|
| ① 编译固件 | `make -C project/ all` | 生成 .bin 文件 |
| ② 启动仿真 | `picsimlab --file=test.pwz --nogui &` | 无头模式后台运行 |
| ③ 等待就绪 | `sleep 3` | 等待 QEMU 启动完成 |
| ④ 运行测试 | `python3 test_uart.py` | TCP 连接并验证输出 |
| ⑤ 清理进程 | `kill %1` | 终止 PicSimlab |

> **优势：** 通过 UART Monitor + TCP 桥接 + Python 断言，可以实现**零硬件的固件行为自动化验证**，将传统需要示波器和物理串口才能完成的调试工作转化为可在 CI/CD 流水线中自动执行的测试。

---

### 7.4 Renode 概述与体系

5.1.1 Renode 的定位
- Renode 是面向嵌入式系统的系统级仿真与验证平台，适合跨主机架构（ARM Cortex-M、RISC-V、Intel 等）进行多外设、多片上系统（SoC）联合仿真，强调可观察性、可脚本化与自动化验证能力。  
- 研究与工程价值：在固件开发周期中替代或补充实物验证，以低成本、可重复、可注入故障的方式实现系统级测试、回归测试与研究性试验。

5.1.2 体系结构（图形优先）
- 建议插图：Renode 架构组件图（仿真内核、设备模型库、RESC 脚本解析器、Python 控制接口、GDB/串口/网络桥接、监测/日志模块）。

Mermaid 流程图（表示组件关系，课堂中请配合图像资源）
```bob
  +---------------------+
  |"RESC / Python"      |
  |"Controller"         |
  +----------+----------+
             |
             v
  +---------------------+
  |   "Renode Core"     |
  +--+------+------+----+
     |      |      |
     v      v      v
  +------+ +------+ +---------+
  |"CPU" | |"外设" | |"Bus /"  |
  |"Model"| |"Models"| |"Interconn"|
  +------+ +------+ +---------+
     |      |      |
     v      v      v
  +--------+ +--------+ +----------+
  |"Monitor"| |"Debug" | |"External"|
  |"Analyzer"| |"GDB/"  | |"TCP/"    |
  |        | |"OpenOCD"| |"Serial"  |
  +--------+ +--------+ +----------+
```


**图 7-5** 上图直观呈现了 Renode 概述与体系的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch7-5 上图直观呈现了 Renode 概述与体系的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

5.1.3 与其他仿真器对比（表格次之）
- 下表比较 Renode、QEMU、PicSimlab 与基于硬件的仿真/仿真加速器的典型特性：

**表 7-9** 
<!-- tab:ch7-9  -->

| 特性 | PicSimlab | Renode | QEMU | 硬件在环 |
|------|----------|--------|------|----------|
| 目标用户 | 教学入门 | 嵌入式验证 | 系统研究 | 产品级验证 |
| 外设建模 | 固定板型 | 高度可定制 | 需修改源码 | 真实硬件 |
| 脚本自动化 | 弱 | 强（RESC+Python） | 弱 | 中等 |
| 多节点仿真 | 否 | 虚拟网络/总线 | 受限 | 需硬件互连 |
| CI/CD 集成 | 否 | 原生支持 | 可支持 | 复杂 |
| 学习曲线 | 低 | 中 | 高 | 高 |
| 调试桥接（GDB 等） | 支持 | 支持 | 支持/需适配 |
| 可重复性（检查点） | 支持 | 部分支持 | 依赖硬件能力 |
| 学术/教学便捷性 | 高 | 较高 | 低（成本高） |

5.1.4 小结
- Renode 的优势在于“外设可脚本化”、“高可观察性”与“便于自动化验证”，适用于研究生层次开展系统级固件验证、协议验证与故障注入研究。

——

### 7.5 高级仿真概念与时序建模

5.2.1 时钟与定时（图形优先）
- 关键点：仿真中需要明确主时钟、外设时钟与软件定时源（SysTick、定时器）；不同时钟域间的同步与漂移会影响中断到处理的延迟。  
- 推荐图形：多时钟域时序图，标注时钟频率、tick 到达、外设就绪信号与中断触发点。

Mermaid 时序图（定时器触发 I2C 采样 -> 中断 -> UART 发送）
```bob
  "Timer"       "I2C"         "CPU"         "UART"        "监控"
    |             |             |             |             |
    | "tick 1ms"  |             |             |             |
    +────────────→|             |             |             |
    |  "request"  |             |             |             |
    |  "sample"   | "DMA/IRQ"   |             |             |
    |             +────────────→|             |             |
    |             |             | "send pkt"  |             |
    |             |             +────────────→|             |
    |             |             |             | "transmit"  |
    |             |             |             +────────────→|
```


**图 7-6** 上图以框图形式描绘了高级仿真概念与时序建模的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch7-6 上图以框图形式描绘了高级仿真概念与时序建模的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

5.2.2 中断处理与优先级（文字补充 + 时序图）
- 说明：需建模硬件中断延迟（从外设事件到中断线上升的延迟）、优先级抢占、ISR 执行时间与中断嵌套的影响。使用时序图展示“外设事件 -> NVIC -> ISR -> DSR/Deferred work”。

5.2.3 总线与外设争用

- 关键点：在多主设备或 DMA 存在的系统中，总线争用会引入额外的访问延时，影响系统实时性。应在仿真中配置带宽、突发传输与仲裁策略以逼近真实行为。

5.2.4 非确定性与可重复性
- 方法要点：使用固定随机种子、禁用/控制非确定性事件（如系统时间源）、使用检查点（snapshot）和回放机制保证回归测试可复现。

5.2.5 性能与量化指标
- 建议监测项：中断响应时间分布、任务切换延时、外设传输吞吐与错误率等，使用 Renode 的监测器（analyzers）和日志导出后做统计分析。

——

### 7.6 Renode 脚本与 Python 自动化

5.3.1 RESC（Renode Script）语言要点（图表+代码）
- RESC 是 Renode 的主脚本语言，用于定义机器、加载固件、连接外设、启用分析器与断点。RESC 脚本常用于场景初始化与一次性仿真配置。

示例 RESC（简化平台加载与串口连接）
```resc
# RESC 脚本：创建机器，加载平台描述与固件，导出 UART 到 TCP
using sysbus

mach create "stm32-sim"
machine LoadPlatformDescription @platforms/cpus/stm32f4.repl

# 加载固件（本地路径或相对路径）
sysbus LoadELF @./build/firmware.elf

# 启用串口分析器，将 uart1 输出映射到 TCP 方便外部监听
showAnalyzer sysbus.uart1
connector Connect sysbus.uart1 tcp:127.0.0.1:2000

# 启动仿真
start
```
注：平台描述文件路径（@platforms/...）取决于 Renode 安装与平台库；上述脚本展示典型工作流，真实使用时按本地平台文件调整路径。

5.3.2 Python 控制接口（自动化、断言、回归）
- Renode 提供 Python 接口（Renode as a service / Python API），用于在测试框架中驱动仿真、注入数据、收集 trace 并断言行为。下述示例示范用 Python 驱动仿真、注入 I2C 数据并断言 UART 输出。

示例 Python 自动化（伪代码，需按环境安装 renode-python bindings 或通过 subprocess 调用 renode-cli）
```python
"""
Python 测试示例（伪代码，适配具体 Renode Python API）
功能：启动仿真、注入 I2C 传感器读数、等待 UART 输出并断言包含预期数据
"""
from renode import Renode  # 视具体绑定而定
import time
import re

r = Renode()
r.execute_script("scripts/init_stm32.resc")  # 载入 RESC 场景
r.start()

# 注入 I2C 传感器数据（通过仿真注入接口）
sensor_payload = [0x01, 0x02, 0x03, 0x04]
r.inject_i2c("sysbus.i2c0", address=0x50, data=sensor_payload)

# 等待 UART 输出并收集
uart_output = r.read_uart("sysbus.uart1", timeout=2.0)
assert re.search(r"sensor: 0x01020304", uart_output), "UART 输出不包含传感器数据"

# 生成检查点（snapshot）
r.create_snapshot("post_sample")

r.stop()
```
说明：上例展示了测试断言与检查点使用的范式，实际 API 名称请参照所用 Renode 版本的 Python binding 文档。

5.3.3 调试桥与 GDB 集成  
- 说明：通过 Renode 可以暴露 GDB server 端口，允许在 IDE（如 VSCode）或命令行 GDB 上进行断点调试、寄存器查看与单步执行，便于定位复杂时序或外设交互问题。

示意 RESC 命令（打开 GDB）
```resc
# 启用 GDB server（默认 3333）
gdbServerStart 3333
```
在本地使用 `arm-none-eabi-gdb` 或 `riscv64-unknown-elf-gdb` 连接到该端口并调试固件。

——

### 7.7 仿真外设注入与故障注入策略

5.4.1 注入类型与目的（表格）

**表 7-10** 仿真外设注入与故障注入策略
<!-- tab:ch7-10 仿真外设注入与故障注入策略 -->

| 注入类型 | 目标 | 常见用途 |
|---:|:---:|:---:|
| 时序偏移注入 | 测试实时性 | 验证系统在延迟/抖动下的鲁棒性 |
| 位翻转/数据错误 | 验证容错 | 验证校验与重传策略 |
| 外设失效（丢失响应） | 验证异常处理 | 检验超时与降级逻辑 |
| 总线争用/带宽限制 | 验证性能极限 | 测量任务延迟增长 |

5.4.2 注入流程（图形优先）
- 推荐流程图：注入场景设计 -> 编写注入脚本 -> 执行仿真并收集指标 -> 自动断言（通过/失败）-> 生成报告并回退检查点。

Mermaid 流程图
```bob
  +----------------+     +-------------------+     +------------------+
  |"设计注入场景" |---->|"实现注入脚本"    |---->|"运行仿真"       |
  |              |     |"(RESC/Python)"    |     |"开始采样"       |
  +----------------+     +-------------------+     +--------+---------+
                                                            |
  +----------------+     +-------------------+              v
  |"回退/重试"    |     |"断言 & 评估"    |     +------------------+
  |"记录失败"    |<-"no"-|"通过?"            |<----|"收集日志"       |
  +----------------+     +--------+----------+     |"trace/指标"     |
                                  | "yes"          +------------------+
                                  v
                         +-------------------+
                         |"保存结果/检查点" |
                         +-------------------+
```


**图 7-7** 该框图展示了仿真外设注入与故障注入策略的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch7-7 该框图展示了仿真外设注入与故障注入策略的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

5.4.3 实施示例：注入 I2C 超时
RESC + Python 混合使用示例伪代码：

- RESC：配置机器、映射 I2C
- Python：在关键时刻禁用 I2C 响应（模拟外设挂起），观察固件的超时处理逻辑并断言

——

### 7.8 工程实例：基于 Renode 的工业物联网（IIoT）采集网关仿真

5.5.1 实例背景（工程价值）
- 场景：工业现场有多路传感器（通过 I2C/ADC）、周期性采样并通过串口转发给上层网关，同时通过以太网或 MQTT 上报云端。固件需保证在外设异常（I2C 时序错误、突发总线延迟）下的鲁棒性，并在采样失败时正确记录错误并重试。  
- 工程价值：通过 Renode 完成端到端仿真，可以在无实物或在硬件不可达条件下验证固件策略、实现自动化回归测试，并进行故障注入实验来评估系统可靠性。

5.5.2 系统架构（图形优先）
Mermaid 架构图（简化）
```bob
  +--------------------------------------------+
  |             "Renode Host"                  |
  |                                            |
  | +----------+  I2C  +-----------+           |
  | |"仿真传感器"|─────→|"MCU"      |           |
  | |"(I2C)"   |       |"Cortex-M" |           |
  | +----------+       +-----+-----+           |
  |                      SPI  |  UART          |
  |                      |    |                |
  |              +-------+    v                |
  |              v       +----------+          |
  |        +---------+   |"Serial"  |          |
  |        |"外部"    |   |"to TCP" |          |
  |        |"Flash"   |   |"Bridge"  |          |
  |        +---------+   +-----+----+          |
  |                            |               |
  +----------------------------+---------------+
                               | MQTT
  +------------------+         v
  |"Python Test"     |   +-----------+
  |"Harness"         |──→|"MQTT"     |
  |                  |   |"Broker"   |
  |"控制/注入/检查"  |   +-----------+
  +------------------+
```


**图 7-8** 上图直观呈现了工程实例：基于 Renode 的工业物联网（IIoT）采集网关仿真的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch7-8 上图直观呈现了工程实例：基于 Renode 的工业物联网（IIoT）采集网关仿真的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

5.5.3 核心设计思路

- MCU 固件模块划分：采样任务（定时器触发）、数据打包与发送模块、错误处理模块（超时/重试/告警）、持久化与回退（外部 flash）。  
- 仿真角度聚焦：准确建模 I2C 读取时序、注入 I2C 超时、验证 UART 输出格式与上报逻辑，以及在出现超时后固件的恢复/重试行为。

5.5.4 关键流程（流程图）
```bob
  "Timer"     "MCU"        "I2C Sensor"    "UART"
    |           |               |              |
    | "tick"    |               |              |
    +──────────→|               |              |
    |           | "I2C read"    |              |
    |           +──────────────→|              |
    |           |     "success?"               |
    |           |<──────────────+              |
    |           |               |              |
    |   "[OK]───+ send pkt"    |              |
    |           +──────────────+─────────────→|
    |           |               |              |
    |  "[FAIL]──+ retry++"     |              |
    |           | "send err"   |              |
    |           +──────────────+─────────────→|
```


**图 7-9** 上图以框图形式描绘了工程实例：基于 Renode 的工业物联网（IIoT）采集网关仿真的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch7-9 上图以框图形式描绘了工程实例：基于 Renode 的工业物联网（IIoT）采集网关仿真的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

5.5.5 核心固件代码（C，示例聚焦中断/采样与 UART 发送）
- 代码风格遵循嵌入式 C 规范（注释、边界检查、错误处理）

```c
/* sample_core.c
 * 功能：定时器 ISR 触发采样，通过 I2C 读取传感器并经 UART 发出
 * 适配：基于 HAL 风格接口抽象（伪代码，便于移植）
 */

#include <stdint.h>
#include <stdbool.h>
#include "hal_timer.h"
#include "hal_i2c.h"
#include "hal_uart.h"
#include "hal_flash.h"

#define SENSOR_I2C_ADDR 0x50
#define SAMPLE_RETRY_MAX 3
#define SAMPLE_BUF_SIZE 8

static uint8_t sample_buffer[SAMPLE_BUF_SIZE];

void timer_isr(void) {
    /* 计时中断：触发采样任务的调度（可设置为 ISR 中直接执行短任务或置位信号量） */
    // 注意：ISR 应尽量短小，重试/IO 操作应在线程上下文或 DSR 中完成
    schedule_sample_task();
}

/* 采样任务（在线程上下文中执行） */
void sample_task(void) {
    int attempt = 0;
    bool success = false;
    while(attempt < SAMPLE_RETRY_MAX && !success) {
        if (hal_i2c_read(SENSOR_I2C_ADDR, sample_buffer, SAMPLE_BUF_SIZE) == HAL_OK) {
            success = true;
            /* 将数据打包并发送到上层（UART） */
            char out[64];
            int len = snprintf(out, sizeof(out), "sensor: 0x%02x%02x%02x%02x\n",
                               sample_buffer[0], sample_buffer[1],
                               sample_buffer[2], sample_buffer[3]);
            hal_uart_write((uint8_t*)out, len);
        } else {
            attempt++;
            if (attempt >= SAMPLE_RETRY_MAX) {
                /* 记录错误并发送告警 */
                const char *err = "sensor read error\n";
                hal_uart_write((uint8_t*)err, strlen(err));
                /* 可选：持久化错误日志 */
                hal_flash_log_error(ERR_SENSOR_TIMEOUT);
            }
            /* 间隔重试（非阻塞等待，使用任务延时接口） */
            task_delay_ms(10);
        }
    }
}
```

代码说明（要点）
- 在 ISR 中仅做最小工作（唤醒/通知任务），避免阻塞外设操作。
- 采样重试在任务上下文处理，支持非阻塞等待与持久化日志。
- UART 输出用于与外部测试脚本断言通信。

5.5.6 Renode 场景脚本（RESC，加载固件、注入 I2C 模拟器并连接 MQTT 代理的简化实现）
```resc
# init_iot_gateway.resc
using sysbus

# 创建并加载平台（基于 STM32F4 平台举例）
mach create "iio-gateway"
machine LoadPlatformDescription @platforms/cpus/stm32f4.repl

# 加载编译好的固件 ELF
sysbus LoadELF @./build/iio_gateway.elf

# 将 uart1 映射为 TCP，供外部测试脚本监听
showAnalyzer sysbus.uart1
connector Connect sysbus.uart1 tcp:127.0.0.1:4001

# 添加虚拟 I2C 传感器设备并配置初始响应
i2c_sensor Create sysbus.i2c0 0x50 4  # 假设语法：Create <i2c> <addr> <bytes>
i2c_sensor SetResponse sysbus.i2c0 0x50 01 02 03 04

# 可选：开启 GDB 用于固件调试
gdbServerStart 3333

# 启动仿真
start
```
说明：i2c_sensor 的具体创建与设置命令依赖于 Renode 外设模型扩展，上述为示意性命令；真实使用请参照本地 Renode 外设模型 API。

5.5.7 Python 测试驱动（注入 I2C 超时并校验固件响应）
```python
# test_iio_gateway.py (伪代码)
from renode import Renode
import time

r = Renode()
r.execute_script("init_iot_gateway.resc")
r.start()

# 验证正常数据流
out = r.read_uart("sysbus.uart1", timeout=1.0)
assert "sensor: 0x01020304" in out

# 注入超时（禁用 I2C 响应）
r.set_i2c_response("sysbus.i2c0", 0x50, response=None)  # 若 API 支持，表示不响应

# 触发下一次采样（可以通过 advance 或者等待定时器）
r.advance_time_ms(10)

# 检查告警输出（重试耗尽后的错误日志）
out = r.read_uart("sysbus.uart1", timeout=2.0)
assert "sensor read error" in out

r.create_snapshot("after_i2c_timeout")
r.stop()
```

5.5.8 时序验证（时序图）
- 在注入超时时，对比“期望时序（重试次数、重试间隔）”与“实际仿真时序”，利用 Renode 的 trace 与 analyzer 导出时间戳做统计。

——

### 7.9 与调试与 CI 集成

5.6.1 GDB / IDE 联动
- 实践要点：在 RESC 中启用 gdbServerStart，并在 IDE 中配置远程 GDB 连接；使用符号化 ELF 以支持源代码级调试与断点回放。

5.6.2 CI / 回归测试流程（表格与流程）
流程示例：代码提交 -> 构建固件 -> 启动 Renode 场景并运行 Python 测试套件 -> 生成测试报告 -> 触发告警或合并。

表：CI 集成要点

**表 7-11** 与调试与 CI 集成
<!-- tab:ch7-11 与调试与 CI 集成 -->

| 步骤 | 关键配置 | 输出 |
|---|---:|:---|
| 构建固件 | 可复现的交叉编译脚本 | 固件 ELF / HEX |
| 启动仿真场景 | RESC 脚本（受版本控制） | 可复现的仿真环境 |
| 自动化测试 | Python 测试用例 + 断言 | PASS/FAIL, trace |
| 报告 | 导出日志与波形（UART, traces） | HTML/JSON 报告 |

5.6.3 报告与可追溯性
- 要保证仿真可复现，需在 CI 中记录：Renode 版本、平台描述、固件 ELF 的 commit hash 与测试脚本版本，以及用于注入的随机种子。

——

### 7.10 本章小结与拓展方向

小结（要点整理）
- Renode 提供强大的系统级仿真能力，适用于研究生层次开展高保真固件验证、时序分析与故障注入研究。  
- 有效使用 RESC 脚本与 Python API，可实现自动化测试流水线与 CI 集成。  
- 仿真中的时钟域、总线争用与中断建模是实现逼真验证的关键；通过检查点与回放机制可保证测试可重复性。

拓展建议
- 深入学习 Renode 自定义设备模型开发（C# / .NET 环境），用于实现研究级外设行为模型；  
- 将 Renode 与形式化工具（如模型检测器）结合，开展协议验证或状态空间探索；  
- 在仿真中集成功耗模型与热模型，开展系统级能耗与热稳定性研究。

——

### 7.11 本章测验

<div id="exam-meta" data-exam-id="chapter5" data-exam-title="第五章 Renode 高级机器人系统仿真编程测验" style="display:none"></div>

<!-- mkdocs-quiz intro -->

<quiz>
1) 在分层架构模式中，HAL（硬件抽象层）的核心作用是：
- [ ] 直接实现业务逻辑，减少代码量
- [ ] 替代操作系统的任务调度功能
- [x] 屏蔽芯片硬件差异，使上层代码在移植时无需修改
- [ ] 提高程序运行速度，减少函数调用开销

正确。HAL 层定义统一接口并由平台相关代码实现，上层只调用接口，换芯片时仅替换 HAL 实现即可。
</quiz>

<quiz>
1) Renode 在系统级仿真中相比 QEMU 的显著优势是下列哪项？
- [ ] 更快的 CPU 仿真性能（指每秒指令数）
- [x] 更灵活的外设模型与脚本化注入能力
- [ ] 更低的内存占用
- [ ] 原生支持所有操作系统内核的仿真

正确。Renode 的核心优势之一是其可脚本化的外设模型和强大的注入/分析能力，便于进行故障注入与系统级测试；QEMU 更侧重于 CPU 仿真性能和通用系统仿真。
</quiz>

<quiz>
2) 在使用 Renode 进行高保真实时性验证时，应关注哪些关键建模要素？
- [x] 时钟域与定时器 tick 精度
- [x] 外设到中断线的硬件延迟与 ISR 执行时间
- [ ] 文件系统的挂载选项（与实时性无直接关系）
- [x] 总线带宽与 DMA 争用

正确。实时性验证依赖于精确的时钟域、外设到中断的延迟和系统总线争用等因素；文件系统挂载选项通常不直接影响嵌入式系统的硬实时性质（除非涉及 I/O 调度）。
</quiz>

<quiz>
3) 说明如何在 Renode 中保证一次故障注入实验的可重复性？
- [x] 固定随机种子，确保随机性可重现
- [x] 使用检查点(snapshot) 在注入前保存系统状态，失败后回退重试
- [x] 在测试记录中保存 Renode 版本、平台描述文件与固件 ELF 的版本信息
- [ ] 使用不同的仿真器每次重复实验

正确。通过固定随机种子可以保证生成的随机事件序列一致；检查点允许在相同初态下重复注入；记录工具与固件版本可确保环境一致，从而达到可重复性要求。
</quiz>

<quiz>
4) 基于本章工程实例，假设在一次 I2C 超时注入测试中，固件未按预期在重试耗尽后发送错误日志，以下哪些是可能的原因？
- [x] 固件逻辑缺陷
- [x] 仿真外设注入未成功
- [x] UART 映射/输出未连接
- [ ] Renode 版本过低

正确。可能原因包括：固件逻辑缺陷（可用 GDB 调试）、仿真外设注入未成功（可用 analyzer/trace 查看）、UART 映射/输出未连接（检查 connector 配置）。
</quiz>

<!-- mkdocs-quiz results -->

---

章节练习题答案与解析均已给出，便于教师批阅或学生自测。建议在课堂实践环节让学生基于提供的 RESC 与 Python 脚本完成实验，并要求提交测试报告（包含仿真日志、检查点、失败重现步骤与改进建议）。

---

参考延伸（便于后续扩展）
- 建议后续章节或附录加入：Renode 自定义外设模型开发实战（包含示例 C# 模型代码）、如何用 Renode 复现复杂总线拓扑（多主、多 DMA）、在 Renode 中集成能耗模型与热模型的研究范例。

本章生成遵循“图形优先、表格次之、文字补充”原则；代码示例聚焦核心功能模块（定时采样 / I2C 读取 / UART 发送 / 注入与断言），并保留扩展点以便在后续课堂上结合真实平台进行实操验证。若需要，本章可进一步拆分为讲授用 PPT 幻灯片、实验指导书与 CI 示例仓库（含可执行 RESC/Python Test Runner），可继续扩展。
