# 🛡️ NetGuardian CLI v1.0 (网络守护者)
> 基于 VMN (Validity Margin Network) 框架的企业级网络关键性预测工具。

## 🚀 核心能力
*   **🔮 临界阈值预测**: 秒级计算出网络的相变临界点（Vc），无需昂贵仿真。
*   **🛡️ 100% 本地运行**: **隐私优先**。所有计算均在本地完成，绝不上传任何拓扑数据。
*   **📊 智能诊断**: 自动检测网络连通性、异质性，并给出偏差警告。
*   **📝 业务报告**: 自动生成带有通俗解读的 HTML 报告，方便向非技术决策者汇报。

## 📦 快速开始

### 1. 环境准备
需要 Python 3.8+ 以及 `networkx`, `scipy`, `numpy`。
```bash
pip install networkx scipy numpy
```

### 2. 运行分析
准备您的网络拓扑文件（支持 `.csv` 或 `.gml`）。
```bash
python netguardian.py my_network.csv -o report.html --verbose
```

### 3. 查看报告
打开 `report.html`，您将看到：
*   **网络基础指标**（节点数、平均度、聚类系数）。
*   **预测阈值 (Vc)** 及其**业务解读**。

## 🔧 高级选项
*   `-o, --output`: 指定报告输出路径 (默认 `risk_report.html`)。
*   `-v, --verbose`: 开启详细日志模式，查看中间计算步骤。

## 📜 隐私与免责
*   本工具不收集、不传输任何用户数据。
*   对于极度异质的网络（如无标度网络），建议结合仿真进行二次验证。

---
*Created by Xiaoyuan (小圆) | Powered by VMN Theory*
