"""
NetGuardian Web App - Streamlit 前端原型
v0.1 MVP

连接核心引擎：../netguardian.py
"""
import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import sys
import os
import tempfile

# 🔗 将父目录加入路径以导入 CLI 引擎
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from netguardian import VMNAnalyzer

# 页面配置
st.set_page_config(layout="wide", page_title="NetGuardian SaaS", page_icon="🛡️")

st.title("🛡️ NetGuardian 平台 (Beta)")
st.caption("基于 VMN 框架的**零数据上传**企业级网络分析工具。")

# 侧边栏：控制面板
with st.sidebar:
    st.header("📂 数据上传")
    uploaded_file = st.file_uploader("拖拽或点击上传 .csv 或 .gml", type=["csv", "gml"])
    
    if uploaded_file is not None:
        st.success("✅ 文件已就绪")
        
        # 保存到临时文件供引擎读取
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        if st.button("🚀 开始深度分析", type="primary"):
            analyze_network(tmp_path)
            os.remove(tmp_path)

def analyze_network(filepath):
    """
    调用 NetGuardian Core Engine 进行分析并渲染 UI
    """
    with st.spinner('🧠 VMN 引擎正在运算中...'):
        try:
            analyzer = VMNAnalyzer(verbose=False)
            
            # 1. 加载
            G = analyzer.load_graph(filepath)
            
            # 2. 预处理 (处理不连通)
            if not nx.is_connected(G):
                G = G.subgraph(max(nx.connected_components(G), key=len)).copy()

            # 3. 执行分析
            topo = analyzer.analyze_topology(G)
            pred = analyzer.predict_vmn_corrected(G, topo)
            
            # v1.2: 获取鲁棒性曲线数据 (这里计算到 20% 移除率)
            curve_data = analyzer.generate_robustness_curve(G, max_fraction=0.2)
            
            # 渲染仪表盘
            render_dashboard(topo, pred, curve_data, G)

        except Exception as e:
            st.error(f"❌ 分析失败: {str(e)}")

def render_dashboard(topo, pred, curve_data, G):
    """渲染可视化仪表盘"""
    
    # --- 核心指标卡片 ---
    st.subheader("📊 核心诊断指标")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("临界阈值 (Vc)", f"{pred['final_vmn']:.3f}", delta="越低越危险")
    col2.metric("异质性指数 (H)", f"{topo['heterogeneity']:.3f}", help="越高说明 Hub 节点越突出")
    col3.metric("攻击损伤率", f"{100 - curve_data[-1][1]:.1f}%", help="移除 Top 5% 核心节点后")
    col4.metric("节点总数", G.number_of_nodes())

    # --- 可视化区域 ---
    st.subheader("🕸️ 网络拓扑与脆弱性可视化")
    
    tab1, tab2 = st.tabs(["网络结构图", "鲁棒性曲线 (v1.2)"])
    
    with tab1:
        # 绘制网络图
        fig, ax = plt.subplots(figsize=(8, 5))
        pos = nx.spring_layout(G, k=0.5)
        
        # 根据度大小调整节点颜色
        degrees = [d for n, d in G.degree()]
        nx.draw(G, pos, ax=ax, node_size=[d * 15 for d in degrees], 
                node_color=degrees, cmap=plt.cm.Reds, 
                with_labels=False, alpha=0.8)
        st.pyplot(fig)
        st.caption("节点越大越红，代表连接度越高（潜在 Hub）。")

    with tab2:
        st.subheader("📉 鲁棒性衰减曲线")
        st.caption("横轴：移除节点比例 (%) | 纵轴：网络最大连通成分剩余比例 (%)")
        
        # 准备绘图数据
        df_curve = pd.DataFrame(curve_data, columns=["移除比例 (%)", "连通性剩余 (%)"])
        st.line_chart(df_curve.set_index("移除比例 (%)"))
        
        # 简单分析曲线
        drop_rate = (100 - df_curve.iloc[-1]["连通性剩余 (%)"]) / df_curve.iloc[-1]["移除比例 (%)"] if df_curve.iloc[-1]["移除比例 (%)"] > 0 else 0
        if drop_rate > 3.0:
            st.warning("⚠️ **曲线陡峭**：网络在失去少量节点后迅速崩溃 (Phase Transition 明显)。")
        else:
            st.success("✅ **曲线平缓**：网络具有较好的抗毁冗余。")

    # --- 建议 ---
    st.divider()
    st.subheader("💡 专家建议")
    if sim['damage_index'] > 0.2:
        st.error("🚨 **高危预警**：网络对关键节点移除非常敏感！建议增加冗余连接或进行去中心化改造。")
    elif topo['heterogeneity'] > 1.0:
        st.warning("⚠️ **结构不均**：存在显著的 Hub 节点，建议监控高连接度节点的负载。")
    else:
        st.success("✅ **结构稳健**：网络表现出良好的随机性和抗毁性。")

if __name__ == "__main__":
    st.info("👈 请在左侧上传网络数据文件以开始分析。")
