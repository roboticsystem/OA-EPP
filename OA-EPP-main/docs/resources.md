# 参考资料 — 研究生课程《机器人系统》

本页面为研究生课程《机器人系统》的推荐学习资料、工具和实验参考。包含教材、经典论文、开源实现、开发板、仿真与测量工具，以及项目与阅读建议。课程侧重硬件与软件协同设计、实时与低功耗系统、嵌入式操作系统与驱动开发、以及系统安全性与验证。

## 推荐主教材

- 《嵌入式系统设计》 —— 教材（根据授课计划选定具体版本）
- Jonathan W. Valvano, "Embedded Systems: Introduction to ARM Cortex-M Microcontrollers"（英文）
- Andrew N. Sloss, Dominic Symes, Chris Wright, "ARM System Developer's Guide"（参考）

## 参考教材与读物

- Jean J. Labrosse, "MicroC/OS-II"（内核与实时系统参考）
- Richard H. Barr, "Real-Time Systems: Theory and Practice"（实时理论）
- Michael Barr, Anthony Massa, "Programming Embedded Systems in C and C++"（实践指南）
- 《现代嵌入式系统与接口技术》（中文参考书目，选章学习）

## 经典论文与技术报告（建议阅读）

- Real-time scheduling: Liu & Layland, "Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment"（1973）
- Priority inversion与锁协议：Sha, Rajkumar, and Lehoczky
- 嵌入式安全与可信启动相关技术白皮书与RFC

（课程中会分配若干论文讨论任务，需按周阅读并撰写要点）

## 开源操作系统与项目（实验与上机练习）

- FreeRTOS — 轻量级实时内核，适合RTOS基础实验
- Zephyr Project — 支持多平台的现代嵌入式OS
- Linux kernel（Embedded/Linux）— 设备树、驱动与内核模块开发
- RT-Thread / NuttX — 国内外流行的嵌入式RTOS示例
- PlatformIO / Arduino Core — 快速原型开发

## 工具链与开发环境

- GNU Arm Embedded Toolchain（arm-none-eabi-gcc）
- OpenOCD（调试、烧写）
- GDB / arm-none-eabi-gdb（远程调试）
- CMake、Make、Ninja（构建系统）
- VS Code + Cortex-Debug / PlatformIO 插件（IDE推荐）
- CI/CD: Git + GitHub Actions（自动化构建与回归测试）

## 常用开发板与硬件平台

- STM32 系列（F4/H7 等）—— 课程实验主力平台
- Raspberry Pi / BeagleBone — 嵌入式 Linux 实验与视觉/网络任务
- ESP32 — 无线通信与低功耗 IoT 项目
- NVIDIA Jetson Nano — 深度学习与加速任务（选配）
- 常用外围：I2C/SPI/ADC/DAC/USART 外设模块、传感器与电机驱动板

## 仿真、建模与验证工具

- QEMU（ARM 仿真）
- gem5（体系结构仿真，选读）
- MATLAB/Simulink（控制系统建模与联动仿真）
- 单元测试/模拟：Unity、CMock、Fake drivers

## 调试与测量设备

- JTAG/SWD 调试器（ST-Link, J-Link）
- 逻辑分析仪（Saleae / 兼容设备）
- 示波器、信号发生器、万用表
- 协议分析工具（CAN/LIN/USB/SPI/I2C）

## 实验与项目建议（可选方向）

- RTOS 移植与调度器实现
- 嵌入式 Linux 驱动编写与设备树实践
- 能耗优化与低功耗设计（睡眠策略、动态频率调整）
- 安全启动、固件完整性验证与 OTA 设计
- 实时控制系统（传感器采集、滤波、控制回路）
- 无线传感网络与边缘计算节点

## 期刊与会议（检索与投稿参考）

- IEEE Transactions on Embedded Computing Systems (TECS)
- ACM Transactions on Embedded Computing Systems (TECS)
- EMSOFT, RTSS, ECRTS, RTAS 等会议论文

## 在线课程与学习资源

- Coursera / edX 上的嵌入式系统与实时系统课程
- 官方文档：ARM、STM、FreeRTOS、Zephyr 项目网站
- 学术资源：IEEE Xplore、ACM Digital Library、arXiv、Google Scholar

## 代码规范、测试与安全

- 推荐遵循 MISRA C / CERT C（视项目要求）
- 单元测试、持续集成、代码审查为必备实践
- 固件签名、加密存储与访问控制为安全课程重点

## 阅读顺序与学习建议

1. 熟悉 C 语言与嵌入式基础（寄存器、外设、中断）
2. 学习 ARM 架构与常用外设驱动实现
3. 进入 RTOS 与内核编程（从 FreeRTOS/Zephyr 到 Linux）
4. 完成若干上机实验，再做一个综合期末项目

## 获取资料与版权说明

- 课程推荐书籍可通过学校图书馆或正版渠道获取
- 课堂和实验中引用的论文、代码库请遵守原作者许可协议

## 联系与助教资源

如需资料复印、论文获取或硬件借用，请联系课程助教与教师（课堂公告栏将发布联系方式与办公时间）。

---

```bob
     .---.
    /-o-/--
 .-/ / /->
( *  \/
 '-.  \
    \ /
     '
```

（本文件由课程组维护，后续将根据教学安排与学期目标更新。）
