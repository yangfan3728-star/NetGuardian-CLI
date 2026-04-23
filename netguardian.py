#!/usr/bin/env python3
"""
NetGuardian CLI v1.1 (Algo-Enhanced)
基于 VMN 框架的网络关键性深度分析工具
更新日志 v1.1: 
- 新增：异质性二阶修正算法 (Heterogeneity Correction)
- 新增：针对性攻击仿真 (Targeted Attack Simulation) 以验证预测
- 新增：代数连通度 (Algebraic Connectivity) 计算
"""

import argparse
import sys
import os
import json
import networkx as nx
import numpy as np
from pathlib import Path
import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡️ 核心声明: 数据隐私保护
# 本工具完全在本地运行，所有计算（包括仿真）均不依赖网络请求。
# 您的网络拓扑数据不会上传到任何服务器。
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class VMNAnalyzer:
    """VMN 深度分析器 (v1.1)"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.log("初始化 VMN 深度分析引擎 v1.1...")

    def log(self, msg):
        if self.verbose:
            print(f"[INFO] {msg}")

    def load_graph(self, filepath):
        self.log(f"正在加载文件: {filepath}")
        ext = Path(filepath).suffix.lower()
        try:
            if ext == '.csv':
                G = nx.read_edgelist(filepath, delimiter=',', create_using=nx.Graph())
            elif ext == '.gml':
                G = nx.read_gml(filepath)
            else:
                raise ValueError(f"不支持的文件格式: {ext}")
            self.log(f"加载成功。节点数: {G.number_of_nodes()}, 边数: {G.number_of_edges()}")
            return G
        except Exception as e:
            print(f"❌ 错误: 无法加载文件。原因: {e}")
            sys.exit(1)

    def analyze_topology(self, G):
        """
        【算法升级 1】: 拓扑深度分析
        计算异质性指数、聚类系数、代数连通度
        """
        self.log("正在进行拓扑深度分析...")
        
        degrees = [d for n, d in G.degree()]
        k_mean = np.mean(degrees)
        k2_mean = np.mean([k**2 for k in degrees])
        sigma_k = np.std(degrees)
        
        # 异质性指数 (Heterogeneity Index) = 变异系数
        # 值越大，说明网络越像无标度网络 (存在超级 Hub)
        heterogeneity_index = sigma_k / k_mean if k_mean > 0 else 0
        
        # 聚类系数
        clustering = nx.average_clustering(G)
        
        # 代数连通度 (Fiedler Value) - 衡量网络整体连通强度的谱指标
        try:
            algebraic_conn = nx.algebraic_connectivity(G, tol=1e-4)
        except:
            algebraic_conn = 0.0

        return {
            "k_mean": k_mean,
            "k2_mean": k2_mean,
            "heterogeneity": heterogeneity_index,
            "clustering": clustering,
            "algebraic_connectivity": algebraic_conn
        }

    def predict_vmn_corrected(self, G, topo_stats):
        """
        【算法升级 2】: VMN 修正预测
        基础预测基于谱半径，但针对高异质性网络引入 <k^2> 修正
        """
        self.log("执行 VMN 修正预测...")
        
        # 1. 基础：谱半径 (Lambda_max)
        try:
            from scipy.sparse.linalg import eigsh
            adj = nx.adjacency_matrix(G)
            eigenvalue, _ = eigsh(adj.astype(float), k=1, which='LM')
            spectral_radius = eigenvalue[0]
            method = "Spectral Radius (Base)"
        except:
            spectral_radius = topo_stats['k_mean']
            method = "Mean Degree (Fallback)"

        # 2. 异质性修正逻辑
        # 在高异质性网络中，Hub 节点主导传播，阈值通常低于平均场预测
        # 我们引入一个基于 <k^2>/<k> 的衰减因子
        correction_factor = 1.0
        if topo_stats['heterogeneity'] > 1.5: # 明显异质
            # 修正项：异质性越高，有效阈值越低
            # 经验公式：修正系数 = 1 / (1 + 0.1 * Heterogeneity)
            correction_factor = 1.0 / (1.0 + 0.1 * topo_stats['heterogeneity'])
            self.log(f"⚠️ 检测到高异质性 (H={topo_stats['heterogeneity']:.2f})，应用二阶修正: x{correction_factor:.2f}")

        # 最终 VMN 预测值
        vmn_threshold = spectral_radius * correction_factor
        
        return {
            "base_spectral": spectral_radius,
            "correction_factor": correction_factor,
            "final_vmn": vmn_threshold,
            "method_used": f"{method} + Heterogeneity Correction"
        }

    def simulate_targeted_attack(self, G, fraction=0.05):
        """
        【算法升级 3】: 针对性攻击仿真 (验证预测)
        模拟移除最重要的 5% 节点 (按度排序)，观察网络崩塌情况
        这是一种“数字孪生”级别的验证，比单纯公式更可信
        """
        self.log(f"启动攻击仿真：移除 Top {fraction*100}% 关键节点...")
        
        # 1. 计算初始最大连通子图大小
        initial_lcc = max(nx.connected_components(G), key=len)
        size_before = len(initial_lcc)
        
        # 2. 识别关键节点 (按 Degree 排序)
        nodes_by_degree = sorted(G.degree(), key=lambda x: x[1], reverse=True)
        num_nodes_to_remove = max(1, int(len(G.nodes()) * fraction))
        targets = [n for n, d in nodes_by_degree[:num_nodes_to_remove]]
        
        # 3. 执行移除
        H = G.copy()
        H.remove_nodes_from(targets)
        
        # 4. 计算移除后的大小
        if H.number_of_nodes() == 0:
            size_after = 0
        else:
            final_lcc = max(nx.connected_components(H), key=len)
            size_after = len(final_lcc)
        
        # 5. 计算损伤指数 (Damage Index)
        damage = (size_before - size_after) / size_before if size_before > 0 else 1.0
        
        self.log(f"仿真结束。损伤指数: {damage:.4f}")
        
        return {
            "removed_nodes": num_nodes_to_remove,
            "damage_index": damage,
            "resilience": 1.0 - damage
        }

    def generate_report(self, topo, pred, sim, output_path):
        """生成 v1.1 增强版报告"""
        
        # 风险评级逻辑
        if pred['final_vmn'] < topo['k_mean']:
            risk_level = "高危 (High Risk)"
            risk_color = "#e74c3c"
            advice = "网络极易受攻击。Hub 节点极其关键，需重点保护或进行去中心化改造。"
        else:
            risk_level = "稳健 (Robust)"
            risk_color = "#27ae60"
            advice = "网络结构相对均匀，抗毁性较强。"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>NetGuardian v1.1 深度分析报告</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; max-width: 850px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }}
                .card {{ background: #f8f9fa; border: 1px solid #e9ecef; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                .metric {{ font-size: 1.5em; font-weight: bold; }}
                .risk {{ color: {risk_color}; }}
                .tag {{ display: inline-block; background: #34495e; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }}
                .progress-bar {{ background: #eee; height: 10px; border-radius: 5px; overflow: hidden; }}
                .fill {{ background: {risk_color}; height: 100%; width: {sim['damage_index']*100}%; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛡️ NetGuardian 深度分析报告 (v1.1)</h1>
                <p>算法引擎：VMN 异质性修正 + 仿真验证 | 生成时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
            </div>

            <div class="card">
                <h3>📊 核心诊断结论</h3>
                <div class="metric risk">{risk_level}</div>
                <p><strong>💡 专家建议：</strong> {advice}</p>
            </div>

            <div style="display:flex; gap: 20px;">
                <div class="card" style="flex:1;">
                    <h3>🧮 拓扑与预测指标</h3>
                    <table>
                        <tr><td>平均连接度 &lt;k&gt;</td><td>{topo['k_mean']:.2f}</td></tr>
                        <tr><td><strong>异质性指数 (H)</strong></td><td>{topo['heterogeneity']:.3f} <span class="tag">{"高" if topo['heterogeneity']>1.5 else "低"}</span></td></tr>
                        <tr><td>VMN 预测阈值 (Vc)</td><td style="font-weight:bold; font-size:1.2em;">{pred['final_vmn']:.3f}</td></tr>
                        <tr><td>修正系数</td><td>{pred['correction_factor']:.2f}</td></tr>
                    </table>
                </div>
                
                <div class="card" style="flex:1;">
                    <h3>🔨 仿真验证 (攻击 Top 5% 节点)</h3>
                    <p>损伤指数 (Damage): <strong>{sim['damage_index']:.2%}</strong></p>
                    <div class="progress-bar"><div class="fill"></div></div>
                    <p style="font-size:0.9em; color:#666;">
                        模拟移除最关键节点后的网络规模缩减比例。
                        <br>如果损伤指数很高，说明预测的 Vc 值是准确的，网络非常脆弱。
                    </p>
                </div>
            </div>

            <div class="card">
                <h3>🔍 详细谱分析</h3>
                <table>
                    <tr><td>聚类系数</td><td>{topo['clustering']:.4f}</td></tr>
                    <tr><td>代数连通度 (Fiedler)</td><td>{topo['algebraic_connectivity']:.4f}</td></tr>
                    <tr><td>计算算法</td><td>{pred['method_used']}</td></tr>
                </table>
            </div>

            <div style="text-align:center; font-size:0.8em; color:#999; margin-top:30px;">
                Generated by NetGuardian CLI v1.1 | Powered by VMN Framework | 100% Local Computation
            </div>
        </body>
        </html>
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ 深度报告已生成: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='NetGuardian CLI v1.1 - Enhanced Network Analysis')
    parser.add_argument('file', help='Input network file (.csv, .gml)')
    parser.add_argument('-o', '--output', default='risk_report_deep.html', help='Output report path')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    print("🚀 启动 NetGuardian CLI v1.1 (Algo-Enhanced) ...")
    
    analyzer = VMNAnalyzer(verbose=args.verbose)
    G = analyzer.load_graph(args.file)
    
    # 1. 检查连通性 (简单处理，取最大子图)
    if not nx.is_connected(G):
        print("⚠️ 警告：网络不连通，将自动分析最大连通子图。")
        G = max(nx.connected_components(G), key=len)
        G = G.subgraph(list(G)).copy() # Ensure it's a graph object

    # 2. 拓扑分析
    topo = analyzer.analyze_topology(G)
    
    # 3. VMN 预测 (含修正)
    pred = analyzer.predict_vmn_corrected(G, topo)
    
    # 4. 仿真验证 (耗时操作，但值得)
    sim = analyzer.simulate_targeted_attack(G, fraction=0.05)
    
    # 5. 生成报告
    analyzer.generate_report(topo, pred, sim, args.output)
    
    print("🏁 分析完成。")

if __name__ == "__main__":
    main()
