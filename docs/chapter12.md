---
number headings: first-level 2, start-at 12
---

## 12 第 12 章 机器人感知与视觉基础

### 12.1 机器人感知概述

感知是机器人理解外部世界的核心能力。不同类型的传感器提供不同维度的环境信息：

```bob
                          "机器人感知传感器谱系"

  "测距类"                   "视觉类"                  "惯性/接触类"
+-------------+          +-------------+          +-------------+
| "超声波"     |          |"单目相机"    |          | "IMU"        |
| "红外"       |          |"双目相机"    |          | "力/力矩"    |
| "激光雷达"   |          |"深度相机"    |          | "触觉传感器" |
| "(LiDAR)"   |          |"事件相机"    |          | "编码器"     |
+------+------+          +------+------+          +------+------+
       |                        |                        |
       v                        v                        v
  "距离/点云"              "图像/深度图"             "加速度/角速度"
```


**图 12-1** 上图直观呈现了机器人感知概述的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch12-1 上图直观呈现了机器人感知概述的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

本章聚焦**视觉感知**——相机是机器人获取丰富语义信息的核心传感器，也是 Visual SLAM（第 13 章）的基础。

#### 12.1.1 机器人常用视觉传感器

**表 12-1** 机器人常用视觉传感器
<!-- tab:ch12-1 机器人常用视觉传感器 -->

| 传感器类型 | 输出 | 典型产品 | 优缺点 |
|-----------|------|---------|--------|
| **单目相机** | RGB 图像 | USB摄像头、CSI相机 | 成本低，无深度信息 |
| **双目相机** | RGB + 视差图 | Intel RealSense D435、ZED 2 | 可计算深度，计算量大 |
| **RGB-D 相机** | RGB + 深度图 | RealSense D455、Kinect | 直接获取深度，室外受限 |
| **事件相机** | 异步事件流 | DVS346、DAVIS | 超高动态范围，数据稀疏 |

通过上表的对比可以看出，不同方案在传感器类型、输出、典型产品等等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

### 12.2 相机模型与标定

#### 12.2.1 针孔相机模型

相机将三维世界中的点投影到二维图像平面。最基本的模型是**针孔模型**（Pinhole Model）：

```bob
  "世界坐标系"                           "图像平面"
                    
       Z                                  v ^
       ^   P(X,Y,Z)                         |    . p(u,v)
       |  .                                 |   /
       | /                                  |  /
       |/        "焦距 f"                    | /
  O ---+----------[====]------------------○ +--------→ u
       |          "光心"                   "o(cx,cy)"      
       |                                   
       +--------→ X                        
      /
     v Y
```


**图 12-2** 上图以框图形式描绘了针孔相机模型的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch12-2 上图以框图形式描绘了针孔相机模型的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

投影方程（齐次坐标）：

$$
s \begin{bmatrix} u \\ v \\ 1 \end{bmatrix} = \mathbf{K} [\mathbf{R} | \mathbf{t}] \begin{bmatrix} X \\ Y \\ Z \\ 1 \end{bmatrix}
$$

其中相机内参矩阵：

$$
\mathbf{K} = \begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix}
$$

- $f_x, f_y$：焦距（像素单位）
- $(c_x, c_y)$：光心在图像中的坐标

#### 12.2.2 畸变模型

实际镜头存在径向和切向畸变：

**径向畸变**（桶形/枕形）：

$$
x_{distorted} = x(1 + k_1 r^2 + k_2 r^4 + k_3 r^6)
$$
$$
y_{distorted} = y(1 + k_1 r^2 + k_2 r^4 + k_3 r^6)
$$

**切向畸变**（镜头与成像面不完全平行）：

$$
x_{distorted} = x + 2p_1 xy + p_2(r^2 + 2x^2)
$$
$$
y_{distorted} = y + p_1(r^2 + 2y^2) + 2p_2 xy
$$

畸变系数向量：$\mathbf{d} = [k_1, k_2, p_1, p_2, k_3]$

#### 12.2.3 相机标定

使用棋盘格标定板，通过 OpenCV 的 `calibrateCamera` 函数求解内参和畸变系数：

```python
import cv2
import numpy as np

# 棋盘格参数
BOARD_SIZE = (9, 6)     # 内角点数
SQUARE_SIZE = 0.025     # 方格边长 25mm

# 世界坐标系中的角点（z=0 平面）
objp = np.zeros((BOARD_SIZE[0] * BOARD_SIZE[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:BOARD_SIZE[0], 0:BOARD_SIZE[1]].T.reshape(-1, 2) * SQUARE_SIZE

obj_points = []  # 世界坐标
img_points = []  # 图像坐标

# 采集多张标定图像
import glob
images = glob.glob('calibration/*.jpg')

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    ret, corners = cv2.findChessboardCorners(gray, BOARD_SIZE, None)
    if ret:
        # 亚像素精化
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        
        obj_points.append(objp)
        img_points.append(corners)

# 标定
ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(
    obj_points, img_points, gray.shape[::-1], None, None
)

print(f"内参矩阵 K:\n{K}")
print(f"畸变系数: {dist}")
print(f"重投影误差: {ret:.4f} 像素")
```

### 12.3 图像特征检测与匹配

视觉 SLAM 和视觉里程计的核心是从图像中提取**可重复检测、可唯一描述**的特征点。

#### 12.3.1 特征点检测

```bob
  "图像"          "检测关键点"        "计算描述子"        "匹配"
+--------+     +------------+     +------------+     +----------+
|   .    |     | "角点/斑点" |     | "128/256维" |     | "暴力匹配"|
|  . .   |---->| "位置提取"  |---->| "向量生成"  |---->| "或 KNN"  |
|   .    |     |            |     |            |     |          |
+--------+     +------------+     +------------+     +----------+
```


**图 12-3** 该框图展示了特征点检测的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch12-3 该框图展示了特征点检测的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

常用特征检测算法：

**表 12-2** 特征点检测
<!-- tab:ch12-2 特征点检测 -->

| 算法 | 类型 | 描述子维度 | 特点 |
|------|------|----------|------|
| **Harris** | 角点 | 无 | 最经典的角点检测，旋转不变 |
| **FAST** | 角点 | 无 | 极快，常配合 BRIEF/ORB 使用 |
| **SIFT** | 斑点 | 128 float | 尺度+旋转不变，计算量大 |
| **SURF** | 斑点 | 64 float | SIFT 的加速版 |
| **ORB** | 角点 | 256 bit | FAST+BRIEF，开源免费，实时性好 |

上表对特征点检测中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

#### 12.3.2 ORB 特征

ORB（Oriented FAST and Rotated BRIEF）是 ORB-SLAM 系列的核心特征，兼顾速度和鲁棒性：

1. **检测**：使用 FAST 角点检测，在图像金字塔（多尺度）上进行
2. **方向**：计算关键点邻域的质心方向（intensity centroid），实现旋转不变性
3. **描述**：使用旋转后的 BRIEF 二进制描述子（256 bit），匹配时用汉明距离

```python
import cv2

# ORB 特征检测与匹配
orb = cv2.ORB_create(nfeatures=500)

img1 = cv2.imread('frame_001.jpg', cv2.IMREAD_GRAYSCALE)
img2 = cv2.imread('frame_002.jpg', cv2.IMREAD_GRAYSCALE)

# 检测关键点和描述子
kp1, des1 = orb.detectAndCompute(img1, None)
kp2, des2 = orb.detectAndCompute(img2, None)

# 暴力匹配（汉明距离）
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
matches = bf.match(des1, des2)
matches = sorted(matches, key=lambda x: x.distance)

print(f"检测到 {len(kp1)} 和 {len(kp2)} 个关键点")
print(f"匹配到 {len(matches)} 对特征")
print(f"最佳匹配距离: {matches[0].distance}")
```

#### 12.3.3 特征匹配与外点剔除

匹配中常有错误匹配（outlier），使用 RANSAC 算法估计基础矩阵的同时剔除外点：

```python
# 提取匹配点坐标
pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])

# RANSAC 估计基础矩阵，同时剔除外点
F, mask = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC, 1.0, 0.99)
inlier_matches = [m for m, flag in zip(matches, mask.ravel()) if flag]

print(f"RANSAC 后内点数: {len(inlier_matches)} / {len(matches)}")
```

### 12.4 立体视觉与深度估计

#### 12.4.1 双目视觉原理

两个水平排列的相机同时拍摄同一场景，通过**视差**（disparity）计算深度：

```bob
  "左相机"         "基线 b"         "右相机"
     O_L ─────────────────────── O_R
      \            |              /
       \           | "深度 Z"     /
        \          |            /
         \         |           /
          \        |          /
           \       |         /
            \      |        /
             \     |       /
              \    |      /
               *───+────*
            "P(X,Y,Z)"
            
  "视差" d = u_L - u_R
  "深度" Z = f·b / d
```


**图 12-4** 上图直观呈现了双目视觉原理的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch12-4 上图直观呈现了双目视觉原理的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

深度计算公式：

$$
Z = \frac{f \cdot b}{d} = \frac{f \cdot b}{u_L - u_R}
$$

其中 $b$ 为基线（两相机光心的距离），$f$ 为焦距，$d$ 为视差。

#### 12.4.2 立体匹配算法


**表 12-3** 从左右图像中寻找对应点，计算每个像素的视差：
<!-- tab:ch12-3 从左右图像中寻找对应点，计算每个像素的视差： -->

| 算法 | 类型 | 特点 |
|------|------|------|
| **BM** | 块匹配 | 速度快，适合实时；精度一般 |
| **SGBM** | 半全局匹配 | 精度好，计算适中；OpenCV 推荐 |
| **ELAS** | 概率匹配 | 高精度，支持稀疏/稠密 |
| **RAFT-Stereo** | 深度学习 | 最高精度，需 GPU |

通过上表的对比可以看出，不同方案在算法、类型、特点等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

```python
import cv2
import numpy as np

# SGBM 立体匹配
left = cv2.imread('left.jpg', cv2.IMREAD_GRAYSCALE)
right = cv2.imread('right.jpg', cv2.IMREAD_GRAYSCALE)

# 参数配置
stereo = cv2.StereoSGBM_create(
    minDisparity=0,
    numDisparities=64,       # 视差搜索范围（必须是16的倍数）
    blockSize=9,              # 匹配块大小
    P1=8 * 3 * 9**2,        # 视差平滑惩罚项
    P2=32 * 3 * 9**2,
    disp12MaxDiff=1,
    uniquenessRatio=10,
    speckleWindowSize=100,
    speckleRange=32
)

# 计算视差图
disparity = stereo.compute(left, right).astype(np.float32) / 16.0

# 视差 → 深度
f = 500.0   # 焦距 (像素)
b = 0.12    # 基线 12cm
depth = np.where(disparity > 0, f * b / disparity, 0)

print(f"深度范围: {depth[depth > 0].min():.2f} - {depth[depth > 0].max():.2f} m")
```

#### 12.4.3 RGB-D 相机

RGB-D 相机（如 Intel RealSense）直接输出深度图，免去立体匹配计算：

- **结构光**（D435/D455）：投射红外点阵，通过变形计算深度
- **ToF**（L515/Azure Kinect）：测量红外光飞行时间

ROS2 中读取 RGB-D 数据：

```python
# ROS2 RGB-D 订阅器
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class RGBDSubscriber(Node):
    def __init__(self):
        super().__init__('rgbd_subscriber')
        self.bridge = CvBridge()
        
        self.rgb_sub = self.create_subscription(
            Image, '/camera/color/image_raw', self.rgb_callback, 10)
        self.depth_sub = self.create_subscription(
            Image, '/camera/depth/image_rect_raw', self.depth_callback, 10)
    
    def rgb_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        # 处理 RGB 图像...
    
    def depth_callback(self, msg):
        depth_image = self.bridge.imgmsg_to_cv2(msg, 'passthrough')
        # depth_image: uint16, 单位 mm
        depth_meters = depth_image.astype(np.float32) / 1000.0
        # 处理深度图像...
```

### 12.5 三维点云处理

#### 12.5.1 点云基础

三维点云是三维空间中点的集合，每个点至少包含 $(x, y, z)$ 坐标，可附加颜色、法向量等信息。

```bob
  "点云数据结构"
  
  +--------+--------+--------+-------+-------+-------+
  |  x_1   |  y_1   |  z_1   |  r_1  |  g_1  |  b_1  |
  +--------+--------+--------+-------+-------+-------+
  |  x_2   |  y_2   |  z_2   |  r_2  |  g_2  |  b_2  |
  +--------+--------+--------+-------+-------+-------+
  |  ...   |  ...   |  ...   |  ...  |  ...  |  ...  |
  +--------+--------+--------+-------+-------+-------+
  |  x_N   |  y_N   |  z_N   |  r_N  |  g_N  |  b_N  |
  +--------+--------+--------+-------+-------+-------+
  
  "典型点云大小：LiDAR 一帧约 10 万点"
```


**图 12-5** 上图以框图形式描绘了点云基础的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch12-5 上图以框图形式描绘了点云基础的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

#### 12.5.2 点云处理常用操作

```python
import open3d as o3d
import numpy as np

# 读取点云

pcd = o3d.io.read_point_cloud("scene.pcd")

# 1. 下采样（体素滤波）—— 降低数据量
pcd_down = pcd.voxel_down_sample(voxel_size=0.02)  # 2cm 体素

# 2. 统计离群点移除
pcd_clean, ind = pcd_down.remove_statistical_outlier(
    nb_neighbors=20, std_ratio=2.0)

# 3. 法向量估计
pcd_clean.estimate_normals(
    search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))

# 4. 平面分割（RANSAC）
plane_model, inliers = pcd_clean.segment_plane(
    distance_threshold=0.01, ransac_n=3, num_iterations=1000)
[a, b, c, d] = plane_model
print(f"检测到平面: {a:.2f}x + {b:.2f}y + {c:.2f}z + {d:.2f} = 0")

# 分离地面和物体
ground = pcd_clean.select_by_index(inliers)
objects = pcd_clean.select_by_index(inliers, invert=True)

# 5. 聚类分割（DBSCAN）
labels = np.array(objects.cluster_dbscan(eps=0.05, min_points=10))
n_clusters = labels.max() + 1
print(f"检测到 {n_clusters} 个物体簇")
```

#### 12.5.3 点云配准（ICP）

**ICP**（Iterative Closest Point）算法将两帧点云对齐，是 3D SLAM 的核心组件：

```bob
  "源点云"         "ICP 迭代"        "对齐后"
    .  .             .               . .
   . .  .    ──→    . . ──→   ──→   . . .
  .  . .           . .  .           . . .
        "目标点云"     "逐步收敛"      "重合"
```


**图 12-6** 该框图展示了点云配准（ICP）的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch12-6 该框图展示了点云配准（ICP）的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

```python
# ICP 点云配准
source = o3d.io.read_point_cloud("frame_001.pcd")
target = o3d.io.read_point_cloud("frame_002.pcd")

# 初始变换猜测（可从IMU/里程计获取）

init_transform = np.eye(4)

# Point-to-Plane ICP（比 Point-to-Point 更精确）
result = o3d.pipelines.registration.registration_icp(
    source, target, max_correspondence_distance=0.05,
    init=init_transform,
    estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPlane()
)

print(f"变换矩阵:\n{result.transformation}")
print(f"内点比例: {result.fitness:.2%}")
print(f"RMSE: {result.inlier_rmse:.4f} m")
```

### 12.6 视觉里程计（VO）

视觉里程计通过连续图像帧之间的运动估计，计算相机（机器人）的位姿变化。

#### 12.6.1 特征点法 VO

```bob
  "帧 t-1"          "帧 t"
+----------+     +----------+
|  .  .    |     |    .  .  |     "匹配特征点"
|    .   . | ──→ | .    .   | ──→ "估计本质矩阵 E"
| .    .   |     |   .    . |     "恢复 R, t"
+----------+     +----------+     "三角化得3D点"
```


**图 12-7** 上图直观呈现了特征点法 VO 的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch12-7 上图直观呈现了特征点法 VO 的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

流程：

1. 在帧 $t-1$ 和帧 $t$ 中检测 ORB 特征并匹配
2. 使用对极约束估计**本质矩阵** $\mathbf{E}$
3. 从 $\mathbf{E}$ 分解出旋转 $\mathbf{R}$ 和平移 $\mathbf{t}$

4. 三角化匹配点获得 3D 地图点
5. 累积运动得到轨迹

```python
import cv2
import numpy as np

class MonocularVO:
    def __init__(self, K):
        self.K = K  # 相机内参
        self.orb = cv2.ORB_create(1000)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.prev_frame = None
        self.prev_kp = None
        self.prev_des = None
        self.pose = np.eye(4)  # 累积位姿
    
    def process_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kp, des = self.orb.detectAndCompute(gray, None)
        
        if self.prev_frame is not None and des is not None and self.prev_des is not None:
            matches = self.bf.match(self.prev_des, des)
            matches = sorted(matches, key=lambda x: x.distance)[:100]
            
            if len(matches) > 10:
                pts1 = np.float32([self.prev_kp[m.queryIdx].pt for m in matches])
                pts2 = np.float32([kp[m.trainIdx].pt for m in matches])
                
                # 估计本质矩阵
                E, mask = cv2.findEssentialMat(
                    pts1, pts2, self.K, method=cv2.RANSAC, prob=0.999, threshold=1.0)
                
                # 恢复 R, t
                _, R, t, mask = cv2.recoverPose(E, pts1, pts2, self.K)
                
                # 构建变换矩阵并累积
                T = np.eye(4)
                T[:3, :3] = R
                T[:3, 3] = t.flatten()
                self.pose = self.pose @ np.linalg.inv(T)
        
        self.prev_frame = gray
        self.prev_kp = kp
        self.prev_des = des
        
        return self.pose[:3, 3]  # 返回当前位置
```

#### 12.6.2 直接法 VO

与特征点法不同，直接法不提取特征，而是直接最小化像素灰度误差：

$$
\min_{\mathbf{T}} \sum_{i} \left\| I_2(\pi(\mathbf{T} \cdot \mathbf{P}_i)) - I_1(\pi(\mathbf{P}_i)) \right\|^2
$$

**表 12-4** 直接法 VO
<!-- tab:ch12-4 直接法 VO -->

| 方法 | 优点 | 缺点 |
|------|------|------|
| **特征点法** | 对光照变化鲁棒，匹配可靠 | 特征提取耗时，纹理弱区域失效 |
| **直接法** | 利用所有像素信息，纹理弱区域可用 | 对光照变化敏感，需要好的初值 |

上表对直接法 VO 中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

### 12.7 目标检测与语义感知

#### 12.7.1 从几何到语义

传统机器人感知只关注"哪里有障碍物"（几何信息），现代机器人还需要理解"这是什么"（语义信息）。

```bob
  "几何感知"                              "语义感知"
+--------------------+              +--------------------+
|                    |              |   "椅子"            |
|    "障碍物"   .    |              |      .    "桌子"    |
|    .  .   .        |     ──→     |   "人" .   .        |
|       .            |              |      "门"           |
+--------------------+              +--------------------+
  "只知道有东西"                       "知道是什么"
```


**图 12-8** 上图以框图形式描绘了从几何到语义的系统架构，清晰呈现了各模块之间的连接关系与信号流向。
<!-- fig:ch12-8 上图以框图形式描绘了从几何到语义的系统架构，清晰呈现了各模块之间的连接关系与信号流向。 -->

#### 12.7.2 YOLO 目标检测

YOLO（You Only Look Once）是实时目标检测的代表算法：

```python

from ultralytics import YOLO
import cv2

# 加载预训练模型
model = YOLO('yolov8n.pt')  # nano 模型，适合边缘设备

# 推理
cap = cv2.VideoCapture(0)
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    results = model(frame)
    
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].int().tolist()
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            label = f"{model.names[cls]} {conf:.2f}"
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    cv2.imshow('Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

#### 12.7.3 语义分割


**表 12-5** 语义分割为每个像素分配类别标签，比目标检测提供更精细的信息：
<!-- tab:ch12-5 语义分割为每个像素分配类别标签，比目标检测提供更精细的信息： -->

| 任务 | 输出 | 典型模型 | 应用场景 |
|------|------|---------|---------|
| 目标检测 | 边界框 + 类别 | YOLOv8, RT-DETR | 物体识别 |
| 语义分割 | 每像素类别 | DeepLabV3, SegFormer | 可通行区域分析 |
| 实例分割 | 每像素类别+实例ID | Mask R-CNN, SAM | 精细抓取规划 |
| 全景分割 | 语义+实例 | Panoptic-DeepLab | 场景完整理解 |

通过上表的对比可以看出，不同方案在任务、输出、典型模型等等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

#### 12.7.4 在机器人中的应用

语义感知与几何感知结合，形成**语义地图**：

1. 目标检测 → SLAM 中的语义地标（"这个点是椅子"）
2. 语义分割 → 可通行区域判断（"地面可走，墙不可走"）
3. 3D 语义 → 场景图（Scene Graph）构建，支持自然语言交互

### 12.8 视觉惯性里程计（VIO）

将视觉里程计（VO）与 IMU 融合，结合了视觉的长期稳定性和 IMU 的高频短期精度，是现代手机和无人机定位的核心方案。

#### 12.8.1 VIO 架构

```bob
  "相机"                           "IMU"
 (15-30 Hz)                     (200-1000 Hz)
    |                                |
    v                                v
+--------+                    +-----------+
|"特征"   |                    | "预积分"   |
|"提取"   |                    | "(第9章)"  |
+----+---+                    +-----+-----+
     |                              |
     +-------------+----------------+
                   |
                   v
            +------+------+
            |  "紧耦合"    |
            |  "优化/滤波" |
            +------+------+
                   |
                   v
            "位姿 + 速度 + IMU偏置"
```


**图 12-9** 该框图展示了 VIO 架构的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。
<!-- fig:ch12-9 该框图展示了 VIO 架构的核心结构，读者可以从中把握各功能单元的层次划分与协作方式。 -->

**表 12-6** VIO 架构
<!-- tab:ch12-6 VIO 架构 -->

| VIO 方案 | 类型 | 特点 |
|----------|------|------|
| **MSCKF** | 滤波（EKF） | 计算高效，适合移动端 |
| **VINS-Mono** | 优化（滑动窗口） | 精度高，开源，支持回环 |
| **ORB-SLAM3** | 优化（关键帧） | 支持单目/双目/RGB-D+IMU |
| **Basalt** | 优化 | TUM 出品，精度和速度兼顾 |

上表对 VIO 架构中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

### 12.9 视觉感知在 ROS2 中的集成

#### 12.9.1 image_transport

ROS2 中图像传输使用 `image_transport` 包，支持压缩传输以节省带宽：

**表 12-7** image_transport
<!-- tab:ch12-7 image_transport -->

| Transport | 压缩率 | 延迟 | 适用场景 |
|-----------|--------|------|---------|
| raw | 1x | 最低 | 本机通信 |
| compressed | 10-50x | 低 | WiFi 网络 |
| theora | 50-100x | 中 | 视频流 |

通过上表的对比可以看出，不同方案在 Transport、压缩率、延迟等等方面各有优劣，实际选型时应结合具体应用场景综合权衡。

#### 12.9.2 常用视觉相关 ROS2 包

**表 12-8** 常用视觉相关 ROS2 包
<!-- tab:ch12-8 常用视觉相关 ROS2 包 -->

| 包名 | 功能 | 输入/输出 |
|------|------|----------|
| `image_pipeline` | 去畸变、立体处理、深度转点云 | Image → PointCloud2 |
| `vision_opencv` | OpenCV 与 ROS 消息互转 | cv_bridge |
| `image_proc` | 去畸变、颜色转换 | Image → Image |
| `depth_image_proc` | 深度图转点云 | Image + CameraInfo → PointCloud2 |
| `darknet_ros` | YOLO 检测 | Image → BoundingBoxes |

上表对常用视觉相关 ROS2 包中各方案的特性进行了横向对比，便于读者根据实际需求选择最合适的技术路线。

### 12.10 小结与习题

本章介绍了机器人视觉感知的核心技术，从相机模型、特征检测、立体视觉到目标检测和视觉里程计。这些内容为第 13 章 SLAM 和第 14 章导航提供了感知层的理论基础。

```bob
+--------+     +--------+     +--------+     +--------+     +--------+
|"相机"   |     |"特征"   |     |"立体"   |     |"点云"   |     |"语义"   |
|"模型"   |---->|"检测"   |---->|"视觉"   |---->|"处理"   |---->|"感知"   |
+--------+     +--------+     +--------+     +--------+     +--------+
     |                              |               |              |
     v                              v               v              v
 "标定"                          "深度图"        "3D SLAM"      "语义地图"
 "(第12.2节)"                   "(第12.4节)"    "(第13章)"     "(第16章)"
```


**图 12-10** 上图直观呈现了小结与习题的组成要素与数据通路，有助于理解系统整体的工作机理。
<!-- fig:ch12-10 上图直观呈现了小结与习题的组成要素与数据通路，有助于理解系统整体的工作机理。 -->

#### 习题

??? question "12-1 相机标定精度"
    采集至少 15 张不同角度的棋盘格标定图像，完成相机标定。重投影误差控制在什么范围内才算合格？畸变系数 $k_1, k_2$ 分别对应什么类型的畸变？

??? question "12-2 ORB 特征"
    对同一场景在不同光照条件下（强光/弱光/侧光）拍摄图像，测试 ORB 特征的匹配正确率。与 SIFT 对比，ORB 在什么条件下表现更差？

??? question "12-3 双目深度计算"
    已知相机焦距 $f = 500$ px，基线 $b = 12$ cm。如果视差 $d = 10$ px，对应深度是多少？视差精度为 $\pm 0.5$ px 时，深度估计的不确定性有多大？

??? question "12-4 ICP 配准"
    使用 Open3D 对两帧有重叠的点云进行 ICP 配准。讨论：（1）初始猜测对 ICP 收敛的影响；（2）Point-to-Point 和 Point-to-Plane ICP 的区别。

??? question "12-5 综合设计"
    设计一个基于 ROS2 的视觉里程计节点：（1）订阅相机话题，提取 ORB 特征；（2）帧间匹配估计运动；（3）发布 `/visual_odom` TF 变换和里程计消息。讨论单目 VO 的尺度模糊问题及其解决方案。


---

### 12.11 本章测验

<div id="exam-meta" data-exam-id="chapter12" data-exam-title="第十二章 机器人感知与视觉基础测验" style="display:none"></div>

<!-- mkdocs-quiz intro -->

<quiz>
1) 针孔相机模型中，内参矩阵 K 包含哪些参数？
- [x] 焦距 $f_x, f_y$ 和主点坐标 $c_x, c_y$
- [ ] 相机的位置和姿态
- [ ] 畸变系数 $k_1, k_2, p_1, p_2$
- [ ] 图像分辨率和帧率

内参矩阵 $K = \begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix}$ 描述像素坐标与归一化相机坐标的映射关系。畸变系数独立于 K，外参（位置和姿态）属于外参矩阵 [R|t]。
</quiz>

<quiz>
2) 双目立体视觉中，深度 Z 与视差 d 的关系是什么？
- [x] $Z = f \cdot B / d$（深度与视差成反比）
- [ ] $Z = f \cdot d / B$（深度与视差成正比）
- [ ] $Z = B / (f \cdot d)$
- [ ] $Z = f + B + d$

双目深度公式 $Z = f \cdot B / d$，其中 $f$ 是焦距，$B$ 是基线长度，$d$ 是左右图像对应点的视差。视差越小，目标越远，因此深度与视差成反比。
</quiz>

<quiz>
3) ORB 特征由哪两部分组成？
- [x] FAST 角点检测器 + BRIEF 描述子（带方向）
- [ ] Harris 角点 + SIFT 描述子
- [ ] Canny 边缘 + HOG 描述子
- [ ] SURF 检测器 + LBP 描述子

ORB = Oriented FAST + Rotated BRIEF。FAST 提供快速角点检测，rBRIEF 在 BRIEF 基础上增加旋转不变性。ORB 计算速度远快于 SIFT/SURF，且无专利限制，广泛用于实时视觉 SLAM。
</quiz>

<quiz>
4) 以下哪项技术不属于视觉里程计（VO）的范畴？
- [x] 回环检测与全局位姿图优化
- [ ] 帧间特征匹配估计相对运动
- [ ] 直接法基于像素灰度值估计相机运动
- [ ] 关键帧选择与局部 BA 优化

VO 关注相邻帧间的相对运动估计（前端），不涉及全局一致性。回环检测和位姿图优化是 SLAM 的后端功能，负责消除累积漂移（参见第 13 章）。
</quiz>

<!-- mkdocs-quiz results -->

---
