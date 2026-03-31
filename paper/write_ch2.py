import os

out_dir = r"D:/cyd/Desktop/yolo_web-main/paper"
text_dir = out_dir + r"/lunwen"

# Ensure directories exist
os.makedirs(out_dir, exist_ok=True)
os.makedirs(text_dir, exist_ok=True)

picture_content = """# 研究内容与技术路线图

```mermaid
graph TD
    classDef phase fill:#e1f5fe,stroke:#31708f,stroke-width:2px,color:#000
    classDef step fill:#ffffff,stroke:#0288d1,stroke-width:1px,color:#000
    classDef model fill:#fff3e0,stroke:#0277bd,stroke-width:1.5px,color:#000
    classDef highlight fill:#ffecb3,stroke:#ef6c00,stroke-width:2px,color:#000

    %% Phase 1: 数据准备
    subgraph Phase1 [第一阶段：数据集构建与预处理]
        direction TB
        A1[开源数据集 3SeasonWeedDet10<br/>选取2021与2022年数据]:::step --> A2[数据清洗与异常排查]:::step
        A2 --> A3[格式归一化转换<br/>VOC XML 转 YOLO TXT]:::step
        A3 --> A4[多维度数据增强<br/>HSV色域/形态变换/Mosaic等]:::step
        A4 --> A5[分层随机划分数据集<br/>固定随机种子<br/>划分比例 7:1.5:1.5]:::step
    end

    %% Phase 2: 模型设计
    subgraph Phase2 [第二阶段：检测模型设计与轻量化改进]
        direction TB
        B1[基线模型构建<br/>YOLOv11s架构分析]:::model --> B2[轻量化主干网络改造<br/>引入 MobileNetV3 减小参数量与算力消耗]:::model
        B2 --> B3[注意力机制补偿优化<br/>Neck层 P3/P4/P5 分别嵌入 ECA 模块]:::model
        B3 --> B4((改进目标模型<br/>YOLOv11s-MBV3-ECA)):::highlight
    end

    %% Phase 3: 实验评估
    subgraph Phase3 [第三阶段：模型训练与实验分析]
        direction TB
        C1[控制变量与超参统一规范<br/>Epochs=200, Optimizer=SGD 等]:::step --> C2[核心消融实验验证<br/>Baseline vs MBV3 vs MBV3+ECA]:::step
        C1 --> C3[主流轻量化模型横向对比实验]:::step
        C2 --> C4[多维度指标综合评估<br/>精度: mAP50 / 轻量化: Params, GFLOPs]:::step
        C3 --> C4
        C4 --> C5[模型检测效果可视化与防漏检定性分析]:::step
    end

    %% Phase 4: 系统开发
    subgraph Phase4 [第四阶段：杂草检测系统设计与落地实现]
        direction TB
        D1[最优防漏检模型权重导出与推理封装]:::step --> D2[后端开发: Flask + SQLite<br/>端点管理与推理接口呈现]:::step
        D1 --> D3[前端开发: Vue3 + Element Plus<br/>视图层与路由权限控制]:::step
        D2 --> D4[前后端集成与Socket实时通信]:::step
        D3 --> D4
        D4 --> D5{业务工程闭环:<br/>环境一键部署与系统测试落地}:::highlight
    end

    %% 流程连接逻辑
    A5 ==>|数据支撑| B1
    B4 ==>|网络结构输出| C1
    C5 ==>|最佳权重输出| D1
```
"""

t1_content = """# 图2-x YOLOv11算法网络结构图

```mermaid
graph LR
    classDef main fill:#e3f2fd,stroke:#0288d1,stroke-width:2px
    classDef sub fill:#fff3e0,stroke:#f57c00,stroke-width:1px
    
    Input[输入图像 Input]:::main --> Backbone[Backbone 主干网络<br/>特征提取]:::main
    Backbone --> SPPF[SPPF 空间金字塔池化]:::sub
    SPPF --> Neck[Neck 颈部网络<br/>多尺度特征融合 PANet/FPN]:::main
    Neck --> P3[降采样特征 P3]:::sub
    Neck --> P4[降采样特征 P4]:::sub
    Neck --> P5[降采样特征 P5]:::sub
    
    P3 --> Head[Head 头部网络<br/>Decoupled Head 解耦头]:::main
    P4 --> Head
    P5 --> Head
    
    Head --> Output[预测结果<br/>边界框 + 置信度 + 类别]:::main
```
"""

t2_content = """# 图2-x 深度可分离卷积原理图

```mermaid
graph TD
    classDef input fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef process fill:#e0f7fa,stroke:#01579b,stroke-width:1.5px
    classDef output fill:#fce4ec,stroke:#006064,stroke-width:2px

    Input[标准输入特征图<br/>DF x DF x M]:::input
    
    subgraph Depthwise_Conv[第一步: 逐通道卷积 Depthwise]
        direction LR
        A1[通道 1] --> F1[滤波器 1<br/>DK x DK x 1] --> O1[输出通道 1]
        A2[通道 2] --> F2[滤波器 2<br/>DK x DK x 1] --> O2[输出通道 2]
        A3[通道 M] --> F3[滤波器 M<br/>DK x DK x 1] --> O3[输出通道 M]
    end
    
    Input --> A1
    Input --> A2
    Input --> A3
    
    Mid[中间特征图<br/>DF x DF x M]:::output
    O1 --> Mid
    O2 --> Mid
    O3 --> Mid
    
    subgraph Pointwise_Conv[第二步: 逐点卷积 Pointwise]
        direction LR
        P1[1x1 卷积核 1<br/>1 x 1 x M]
        P2[1x1 卷积核 N<br/>1 x 1 x M]
    end
    
    Mid --> P1
    Mid --> P2
    
    Out[最终输出特征图<br/>DF x DF x N]:::output
    P1 --> Out
    P2 --> Out
```
"""

t3_content = """# 图2-x ECA注意力机制模块结构图

```mermaid
graph LR
    classDef input fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef process fill:#fff3e0,stroke:#e65100,stroke-width:1.5px
    classDef output fill:#e8eaf6,stroke:#006064,stroke-width:2px

    Input(输入特征图 X<br/>C x H x W):::input --> GAP[全局平均池化 GAP<br/>Spatial Squeeze]:::process
    GAP --> FC(通道特征1D向量<br/>C x 1 x 1):::output
    
    FC --> Conv1D[1D 卷积<br/>核大小 k]:::process
    Conv1D --> Sigmoid[Sigmoid 激活函数]:::process
    
    Sigmoid --> Weight(通道权重向量 /omega<br/>C x 1 x 1):::output
    
    Input --> Multiply(( /otimes <br/>逐元素相乘 )):::process
    Weight --> Multiply
    
    Multiply --> Output(输出特征图 Y<br/>C x H x W):::input
```
"""

chapter2_content = """# 第二章 相关理论与技术基础

## 2.1 田间杂草视觉检测核心理论

### 2.1.1 目标检测的核心任务与评价体系
目标检测（Object Detection）是计算机视觉领域的核心任务，旨在对图像或视频中的多个目标进行精准定位和正确分类。在杂草检测任务中，算法既需要框出杂草的物理位置（Bounding Box），还需要识别出框内植物的类别。

为衡量检测算法在农业场景下的性能，本文采用一系列标准的评价指标。首先，基于预测框与真实框（Ground Truth）的交并比（Intersection over Union, IoU）来判断预测框的准确度，其计算公式为：
$$IoU = \\frac{A \\cap B}{A \\cup B}$$
其中，$A$ 为真实框的面积，$B$ 为预测框的面积。当 $IoU$ 大于设定的阈值时，将其定义为真正例（True Positive, $TP$）；若小于阈值则为假正例（False Positive, $FP$）；若真实目标未被检测到，则定义为假反例（False Negative, $FN$）。

基于上述定义，引入精确率（Precision, $P$）和召回率（Recall, $R$）：
$$P = \\frac{TP}{TP + FP}$$
$$R = \\frac{TP}{TP + FN}$$
精确率评估了预测为正样本中实际为正样本的比例，召回率则评估了所有正样本中被正确预测出来的比例。

综合精确率和召回率构成的 $P-R$ 曲线面积即为平均精度（Average Precision, $AP$），进而计算出所有类别的平均精度均值（Mean Average Precision, $mAP$）：
$$AP = \\int_{0}^{1} P(R) dR$$
$$mAP = \\frac{1}{N} \\sum_{i=1}^{N} AP_i$$
其中，$N$ 表示目标类别的总数。在论文的实验评估中，$mAP@0.5$（IoU阈值为0.5时的mAP）将作为衡量模型精度的主导标准。

### 2.1.2 农业田间场景杂草检测的技术难点
受限于田间的非结构化环境，杂草检测任务面临显著的技术难点。
首先是**目标形态的相似性**。杂草与农作物的幼苗期在颜色特征和叶片纹理上高度相似，这极易导致模型误判。
其次是**目标尺度微小及密集遮挡**。很多情况下杂草目标在监控画面中像素占比极小，且植物叶片常相互交叉叠压。这种复杂的空间关系对模型的特征提取能力提出了极高的要求。
最后是**环境光照的不确定性**。多云、直射光以及阴影等光照变化，常引起图像色域畸变，削弱了目标原本的表征特性，这也是对基于深度学习的视觉模型的严峻考验。

---

## 2.2 YOLO 系列目标检测算法原理

### 2.2.1 YOLO 算法的发展与核心思想
YOLO（You Only Look Once）是一阶（One-stage）目标检测算法的代表，它的核心思想是将目标定位和分类任务统一转化为一个端到端的回归问题。相较于两阶算法（如Faster R-CNN），YOLO不仅剔除了生成候选区域的繁琐步骤，还在保证较高精度的基础上极大提升了推理速度，奠定了工业界实时目标检测领域的标准。
自YOLOv1提出网格回归范式起，该系列经过多次迭代：YOLOv3引入了多尺度预测（FPN），YOLOv5引入了Darknet53及残差连接，YOLOv8进行了锚框无关（Anchor-free）与解耦头（Decoupled-Head）的革新。

### 2.2.2 YOLOv11 算法的网络结构与技术特性
作为YOLO系列的最新版本，YOLOv11在网络架构上进行了深度优化。其结构主要分为三部分：特征提取主干网络（Backbone）、特征融合网络（Neck）以及预测输出头（Head）。

**[此处可插入图：t1.md YOLOv11算法网络结构图]**

Backbone承担着从原图中逐层提取各级别语义信息的任务并融合了SPPF以扩展感受野；Neck采用PANet和FPN的组合，致力于聚合深层语义和浅层纹理信息；Head部分则延用了轻量化的解耦头设计，将分类与边框回归任务剥离，减轻了梯度传播过程中的相互干扰。YOLOv11s（Small）版本在架构上较精简，为本文进一步构建适用于硬件资源受限场景的轻量化农业视觉系统提供了优秀的基准。

---

## 2.3 轻量化网络核心技术

### 2.3.1 深度可分离卷积原理
为了降低模型在计算设备（如边缘计算设备）上的计算消耗，必须对标准卷积进行改造。深度可分离卷积（Depthwise Separable Convolution）将标准卷积分解为两步：逐通道卷积（Depthwise Convolution）和逐点卷积（Pointwise Convolution）。

**[此处可插入图：t2.md 深度可分离卷积原理图]**

逐通道卷积对每个输入通道应用唯一的卷积核进行空间滤波，逐点卷积随后使用1×1的卷积核进行通道间信息的融合。
假设输入特征图尺寸为 $D_F \\times D_F \\times M$，输出通道数为 $N$，卷积核尺寸为 $D_K \\times D_K$。则标准卷积的计算量为：
$$Flops_{std} = D_K \\times D_K \\times M \\times N \\times D_F \\times D_F$$
而深度可分离卷积的计算量为：
$$Flops_{dsc} = D_K \\times D_K \\times M \\times D_F \\times D_F + M \\times N \\times D_F \\times D_F$$
两者的计算量比值为：
$$\\frac{Flops_{dsc}}{Flops_{std}} = \\frac{1}{N} + \\frac{1}{D_K^2}$$
通常使用 $3 \\times 3$ 卷积核时，计算量和参数量可下降约8至9倍，是轻量化网络设计的基石。

### 2.3.2 MobileNetV3 轻量化网络结构与特性
MobileNetV3 是由Google提出的极具代表性的轻量级骨干网络，其集成了前代网络的深度可分离卷积和反残差结构。
MobileNetV3的核心模块（Bneck）利用了神经架构搜索（NAS）技术自适应寻找最佳的通道数扩张比。同时，它引入了更为高效的非线性激活函数 h-swish：
$$h\\_swish(x) = x \\frac{ReLU6(x + 3)}{6}$$
在本文研究中，我们将YOLOv11s庞大的CSPDarknet主干网络替换为MobileNetV3结构。在极大缩减整体参数量（Params）与浮点运算力（GFLOPs）的同时，保留了模型对基础植物特征提取的效率。

---

## 2.4 注意力机制核心原理

### 2.4.1 通道注意力机制的核心思想
在深度卷积网络中，不同维度的特征通道包含着对最终预测不同贡献权重的信息。通道注意力机制旨在通过数学建模赋予模型“聚焦重点”的能力，抑制诸如土壤、光斑等背景噪音，增强植物叶片边缘等核心特征。最经典的通道注意力机制如 SE（Squeeze-and-Excitation）模块，由全局平均池化和全连接层组成，但其使用了两次全连接层引起的降维操作对通道间相关性的建模会造成信息折损。

### 2.4.2 ECA 高效通道注意力模块的原理与优势
为了克服SE模块降维引起的信息损失问题，ECA（Efficient Channel Attention）模块提出了一种无降维的局部跨通道交互策略。

**[此处可插入图：t3.md ECA注意力机制模块结构图]**

ECA模块首先对输入空间图执行全局平均池化（GAP），提取单一通道的向量表达 $y \\in \\mathbb{R}^C$。随后，直接运用一维卷积核为 $k$ 的 1D 卷积来捕获局部通道间的交互，并通过 Sigmoid 函数 $\\sigma$ 计算得到通道注意力权重 $\\omega$。公式定义为：
$$\\omega = \\sigma(1D\\_Conv_k(y))$$
其中，1D卷积核的感受野（大小 $k$）可以根据通道数 $C$ 自适应动态确定：
$$k = \\psi(C) = \\left| \\frac{\\log_2(C)}{\\gamma} + \\frac{b}{\\gamma} \\right|_{odd}$$
（式中常数 $\\gamma=2, b=1$， $|\\cdot|_{odd}$ 表示取最近的奇数）。
由于未涉及全连接层与降维，ECA在几乎不增加网络参数的条件下显著提升了模型特征聚合的灵敏度。本文将ECA模块引入到网络的颈部（Neck）P3、P4、P5层中，从而有效补偿因为采用轻量化MobileNetV3主干带来的部分精度流失。

---

## 2.5 系统开发相关技术

### 2.5.1 后端技术：Flask 框架与 Socket 通信
Flask 是一个由 Python 编写的轻量级后端 Web 框架。在其支持下，YOLO模型的推理服务能够以HTTP接口的形式封装和暴漏出去。为了实现实时的进度检测或者视频流推演，系统通常辅以 Socket.IO 技术，它能够在服务端与客户端之间维持一个长连接全双工的通信信道，保障识别事件及进度日志毫无延迟地推送至前端面板。

### 2.5.2 前端技术：Vue3 与 Element Plus
Vue3 是当下前端领域广泛响应的渐进式 JavaScript 框架，因结合了 Composition API，极其适合复杂工业级界面的组件状态管理及响应式变动。为了迅速搭建出用户体验良好、数据展示直观的人机交互界面，系统选用 Element Plus 组件库，完成各类大盘显示、图片上传区以及数据分析图表视图的组装工作，从而极大地分离了前后端的耦合逻辑。

### 2.5.3 数据存储：SQLite 数据库
受限于单机桌面环境与边缘部署场景中往往不宜额外部署沉重的外部数据库服务，本项目采用 SQLite。作为零配置轻量级关系型数据库，SQLite 使得系统能够直接利用本地文件建立数据表，高效实现诸如历史记录调阅、账号鉴权以及业务状态留存的数据持久化服务。
"""

try:
    with open(f'{out_dir}/picture.md', 'w', encoding='utf-8') as f:
        f.write(picture_content)
    with open(f'{out_dir}/t1.md', 'w', encoding='utf-8') as f:
        f.write(t1_content)
    with open(f'{out_dir}/t2.md', 'w', encoding='utf-8') as f:
        f.write(t2_content)
    with open(f'{out_dir}/t3.md', 'w', encoding='utf-8') as f:
        f.write(t3_content)
    with open(f'{text_dir}/第二章_正文.md', 'w', encoding='utf-8') as f:
        f.write(chapter2_content)
    print("Files created successfully.")
except Exception as e:
    print("Error:", e)
