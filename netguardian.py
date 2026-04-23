#!/usr/bin/env python3
"""
NetGuardian CLI v1.0 - 网络关键性预测与风险评估工具
基于 VMN (Validity Margin Network) 框架
开发: 小圆 (Xiaoyuan)
"""

import argparse
import sys
import os
import networkx as nx
import numpy as np
import datetime
from pathlib import Path

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡️ 核心声明: 数据隐私保护
# 本工具完全在本地运行，所有计算均不依赖网络请求。
# 您的网络拓扑数据不会上传到任何服务器。
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class VMNAnalyzer:
    """VMN 核心分析器"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.log("初始化 VMN 分析引擎...")

    def log(self, msg):
        if self.verbose:
            print(f"[INFO] {msg}")

    def load_graph(self, filepath):
        """加载网络文件 (支持 CSV, GML, JSON)"""
        self.log(f"正在加载文件: {filepath}")
        ext = Path(filepath).suffix.lower()
        
        try:
            if ext == '.csv':
                # 假设 CSV 是两列: source, target
                G = nx.read_edgelist(filepath, delimiter=',', create_using=nx.Graph())
            elif ext == '.gml':
                G = nx.read_gml(filepath)
            elif ext == '.json':
                G = nx.readwrite.json_graph.node_link_graph(json.load(open(filepath))) # 需 import json
            else:
                raise ValueError(f"不支持的文件格式: {ext}")
            
            self.log(f"加载成功。节点数: {G.number_of_nodes()}, 边数: {G.number_of_edges()}")
            return G
        except Exception as e:
            print(f"❌ 错误: 无法加载文件。原因: {e}")
            sys.exit(1)

    def check_graph_health(self, G):
        """健康检查与扩展性警告"""
        # 1. 基础检查
        if G.number_of_nodes() == 0:
            print("❌ 错误: 网络中没有节点。")
            sys.exit(1)
        
        if not nx.is_connected(G):
            # 寻找最大连通子图
            largest_cc = max(nx.connected_components(G), key=len)
            G = G.subgraph(largest_cc).copy()
            print("⚠️ 警告: 网络不连通。已自动切换到最大连通子图进行分析。")
        
        # 2. 扩展性警告 (检测异质网络)
        degrees = [d for n, d in G.degree()]
        k_mean = np.mean(degrees)
        k_var = np.var(degrees)
        
        # 简单启发式：如果方差极大，可能是无标度网络 (SF)，VMN 公式可能有偏差
        if k_var > (k_mean ** 2): 
            print("⚠️ 警告: 检测到网络度分布高度异质 (可能是无标度网络)。")
            print("   -> 一阶 VMN 公式可能高估临界阈值。建议参考《VMN 论文》中的异质修正项。")

        return G

    def calculate_vmn(self, G):
        """
        计算 VMN 临界阈值
        公式: Vc ≈ <k> / (1 - alpha * C)  <-- 这里用简化版演示，实际可用谱半径
        """
        self.log("计算图属性...")
        
        # 获取基础属性
        avg_degree = np.mean([d for n, d in G.degree()])
        clustering = nx.average_clustering(G)
        
        # 尝试计算谱半径 (最大特征值) - 更精确
        try:
            from scipy.sparse.linalg import eigsh
            adj = nx.adjacency_matrix(G)
            # 计算最大特征值 (幂迭代法更高效)
            eigenvalue, _ = eigsh(adj.astype(float), k=1, which='LM')
            spectral_radius = eigenvalue[0]
            method_used = "谱半径法 (高精度)"
        except Exception:
            # 降级方案
            spectral_radius = avg_degree
            method_used = "平均度近似 (低精度)"

        # VMN 预测逻辑 (基于谱半径或平均度)
        # 对于共识类网络，Vc 通常与平均度或谱半径成正比
        # 确保结果非负
        vmn_threshold = max(0.01, spectral_radius) 
        
        # 如果谱半径异常（如负数，理论上无向图谱半径应非负，但需防御性编程）
        if spectral_radius < 0:
             print("⚠️ 警告: 计算出的谱半径为负，这通常意味着网络结构极其特殊或算法不适用。")
             vmn_threshold = avg_degree # 降级使用平均度 
        
        return {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "avg_degree": round(avg_degree, 2),
            "clustering_coeff": round(clustering, 3),
            "spectral_radius": round(spectral_radius, 4),
            "vmn_threshold": round(vmn_threshold, 4),
            "method": method_used
        }

    def generate_report(self, data, output_path):
        """生成带可解释性文字的 HTML 报告"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>NetGuardian 风险评估报告 - {datetime.date.today()}</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }}
                .card {{ background: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; margin: 15px 0; border-radius: 8px; }}
                .metric {{ font-size: 2em; font-weight: bold; color: #e74c3c; }}
                .explanation {{ background: #e8f6f3; padding: 10px; border-left: 4px solid #1abc9c; margin-top: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                td, th {{ padding: 8px; border-bottom: 1px solid #ddd; text-align: left; }}
                .disclaimer {{ font-size: 0.8em; color: #7f8c8d; margin-top: 30px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛡️ 网络关键性评估报告</h1>
                <p>生成时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
            </div>

            <div class="card">
                <h3>📊 核心指标</h3>
                <table>
                    <tr><td>节点总数</td><td>{data['nodes']}</td></tr>
                    <tr><td>平均连接度</td><td>{data['avg_degree']}</td></tr>
                    <tr><td>聚类系数</td><td>{data['clustering_coeff']}</td></tr>
                    <tr><td>计算方法</td><td>{data['method']}</td></tr>
                </table>
            </div>

            <div class="card">
                <h3>🚨 VMN 临界阈值预测</h3>
                <div class="metric">Vc ≈ {data['vmn_threshold']}</div>
                
                <div class="explanation">
                    <strong>💡 专家解读：</strong><br>
                    预测显示，您的网络临界阈值约为 <b>{data['vmn_threshold']}</b>。
                    这意味着，当外部干预强度或内部传播效率达到这个数值时，网络将发生<strong>相变（Phase Transition）</strong>。
                    <br><br>
                    <ul>
                        <li><b>如果是舆情/病毒网络</b>: 低于此值，信息/病毒将自然消亡；高于此值，将引发全网爆发。</li>
                        <li><b>如果是电力/交通网络</b>: 低于此值，网络保持连通；高于此值（如负载过载），可能导致级联故障崩溃。</li>
                    </ul>
                </div>
            </div>

            <div class="disclaimer">
                <p>本报告由 NetGuardian CLI 生成 | 基于 VMN 理论框架 | 数据未上传云端</p>
            </div>
        </body>
        </html>
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ 报告已生成: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='NetGuardian CLI - 网络关键性预测工具')
    parser.add_argument('file', help='输入网络文件路径 (支持 .csv, .gml)')
    parser.add_argument('-o', '--output', default='risk_report.html', help='输出报告路径 (默认: risk_report.html)')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细调试信息')
    
    args = parser.parse_args()

    print("🚀 启动 NetGuardian v1.0 ...")
    
    analyzer = VMNAnalyzer(verbose=args.verbose)
    G = analyzer.load_graph(args.file)
    G = analyzer.check_graph_health(G)
    results = analyzer.calculate_vmn(G)
    analyzer.generate_report(results, args.output)
    print("🏁 分析完成。")

if __name__ == "__main__":
    main()
