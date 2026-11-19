"""工艺矿物学磨矿分析系统 - 经典版"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="工艺矿物学磨矿分析系统 · 经典版",
    page_icon="⚒",
    layout="centered",
    initial_sidebar_state="collapsed",
)

from core.mineral_data import *
from core.bond import *
from core.kinetics import *
from core.liberation import *

st.markdown("""
<style>
.block-container {max-width:860px;padding-top:1.25rem;padding-bottom:2rem}
.main-header {font-size:1.8rem;font-weight:700;color:#1a1a2e;margin-bottom:0.5rem}
.sub-header {font-size:1.2rem;font-weight:500;color:#16213e;margin-bottom:1rem}
.stat-card {background:#f0f2f6;border-radius:8px;padding:1rem;text-align:center;border:1px solid #e0e0e0}
.stat-value {font-size:1.8rem;font-weight:700;color:#1a1a2e}
.stat-label {font-size:0.85rem;color:#555}
.highlight-box {background:#e8f4f8;border-left:4px solid #2196F3;padding:1rem;border-radius:4px;margin:0.5rem 0}
.warning-box {background:#fff3e0;border-left:4px solid #FF9800;padding:1rem;border-radius:4px;margin:0.5rem 0}
.success-box {background:#e8f5e9;border-left:4px solid #4CAF50;padding:1rem;border-radius:4px;margin:0.5rem 0}
@media (max-width:640px) {
  .block-container {padding:0.8rem 0.75rem 1.5rem}
  .main-header {font-size:1.5rem}
  .stat-card {padding:0.75rem 0.4rem}
  .stat-value {font-size:1.4rem}
}
</style>
""", unsafe_allow_html=True)

if "mineral_composition" not in st.session_state:
    st.session_state.mineral_composition = []
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

st.sidebar.markdown("# ⚒ 磨矿分析系统")
st.sidebar.caption("经典版 v1.0")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "功能菜单",
    [
        "📋 矿物组成输入",
        "📊 磨矿参数分析",
        "📈 动力学模拟",
        "🔬 筛析数据分析",
        "📑 结果报告",
    ],
)

# === PAGE 1: 矿物组成输入 ===
if page == "📋 矿物组成输入":
    st.markdown("<div class='main-header'>矿物组成输入</div>", unsafe_allow_html=True)
    st.markdown("选择或自定义矿物，输入含量和嵌布粒度参数")
    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.markdown("<div class='sub-header'>添加矿物</div>", unsafe_allow_html=True)
        use_preset = st.toggle("从矿物数据库选择", value=True)
        if use_preset:
            mineral_name = st.selectbox("选择矿物", DEFAULT_MINERAL_NAMES)
            m = get_mineral(mineral_name)
            if m:
                st.info(f"密度 {m.density}g/cm3 | 硬度 {m.hardness} | Wi {m.bond_wi}kWh/t | 嵌布 {m.typical_grain_size[0]:g}-{m.typical_grain_size[1]:g}um | 嵌布类型 {m.texture}")
                st.caption(f"参数来源：{m.source}。{m.note}")
                content = st.number_input("含量 (%)", 0.0, 100.0, 10.0, 0.5)
                gs = st.slider("嵌布粒度 (um)", int(m.typical_grain_size[0]), int(m.typical_grain_size[1]),
                    int((m.typical_grain_size[0]+m.typical_grain_size[1])/2))
                mt = m.mineral_type; bw = m.bond_wi
        else:
            with st.form("cf"):
                mineral_name = st.text_input("矿物名称", "自定义矿物")
                ca, cb = st.columns(2)
                with ca:
                    density = st.number_input("密度", 0.0, 20.0, 3.0, 0.1)
                    bw = st.number_input("Bond Wi", 0.0, 50.0, 12.0, 0.5)
                with cb:
                    hardness = st.number_input("硬度", 0.0, 10.0, 5.0, 0.5)
                    gs = st.number_input("嵌布粒度", 1, 2000, 100, 5)
                content = st.number_input("含量 (%)", 0.0, 100.0, 10.0, 0.5)
                mt = st.selectbox("类型", ["valuable","gangue"], format_func=lambda x: {"valuable":"目的矿物","gangue":"脉石"}[x])
                if st.form_submit_button("添加"):
                    if not mineral_name.strip() or density <= 0 or bw <= 0 or gs <= 0 or not 0 < content <= 100:
                        st.error("请检查矿物名称、密度、Bond Wi、嵌布粒度和含量。")
                    else:
                        add_custom_mineral(mineral_name, density, hardness, bw, gs, gs, mt)
                        st.rerun()
        if st.button("添加到矿物列表", type="primary", width="stretch"):
            if not mineral_name.strip() or bw <= 0 or gs <= 0 or not 0 < content <= 100:
                st.error("请检查矿物名称、Bond Wi、嵌布粒度和含量。")
            elif mineral_name in [m["name"] for m in st.session_state.mineral_composition]: st.warning(f"{mineral_name} 已在列表中")
            else:
                texture = m.texture if use_preset else "simple"
                st.session_state.mineral_composition.append({"name":mineral_name,"content":content,"grain_size":gs,"mineral_type":mt,"bond_wi":bw,"texture":texture})
                st.rerun()
    with col2:
        st.markdown("<div class='sub-header'>当前矿物组成</div>", unsafe_allow_html=True)
        if st.session_state.mineral_composition:
            display_rows = []
            for m in st.session_state.mineral_composition:
                display_rows.append({"矿物":m["name"],"含量(%)":m["content"],"嵌布(um)":m["grain_size"],"Wi":m["bond_wi"],"类型":{"valuable":"目的矿物","gangue":"脉石"}[m["mineral_type"]]})
            edited_df = st.data_editor(display_rows, width="stretch", hide_index=True, column_config={
                "类型": st.column_config.SelectboxColumn("类型", options=["目的矿物", "脉石"]),
                "矿物": st.column_config.TextColumn("矿物", disabled=True),
                "含量(%)": st.column_config.NumberColumn("含量(%)", disabled=True),
                "嵌布(um)": st.column_config.NumberColumn("嵌布(um)", disabled=True),
                "Wi": st.column_config.NumberColumn("Wi", disabled=True),
            })
            for i in range(len(edited_df)):
                new_cn = edited_df[i]["类型"]
                new_val = "valuable" if new_cn == "目的矿物" else "gangue"
                if st.session_state.mineral_composition[i]["mineral_type"] != new_val:
                    st.session_state.mineral_composition[i]["mineral_type"] = new_val
            df = pd.DataFrame(st.session_state.mineral_composition)
            df["类型"] = df["mineral_type"].map({"valuable":"目的矿物","gangue":"脉石"})
            fig = px.pie(df, values="content", names="name", title="矿物组成", color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, width="stretch")
            with st.expander("删除矿物"):
                to_rm = st.selectbox("选择要删除的", [m["name"] for m in st.session_state.mineral_composition])
                if st.button("删除"):
                    st.session_state.mineral_composition = [m for m in st.session_state.mineral_composition if m["name"] != to_rm]; st.rerun()
        else:
            st.info("左侧添加矿物后显示在此处")
        total = sum(m["content"] for m in st.session_state.mineral_composition)
        valuable = [m for m in st.session_state.mineral_composition if m["mineral_type"] == "valuable"]
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("总含量", f"{total:.1f}%")
        col_b.metric("目的矿物数", len(valuable))
        if st.session_state.mineral_composition and total > 0:
            col_c.metric("平均Wi", f"{sum(m['bond_wi']*m['content'] for m in st.session_state.mineral_composition)/total:.1f}")
        if st.button("清空所有", width="stretch"):
            st.session_state.mineral_composition = []; st.session_state.analysis_done = False; st.rerun()
        # 含量校验与归一化
        if st.session_state.mineral_composition and abs(total - 100) > 0.05:
            if total > 100:
                st.warning(f"矿物总含量 {total:.1f}% 已超过 100%，计算结果会偏大")
            else:
                st.info(f"矿物总含量 {total:.1f}%，剩余 {100-total:.1f}% 未指定")
            if st.button("自动归一化到 100%", width="stretch", type="secondary"):
                factor = 100.0 / total
                for m in st.session_state.mineral_composition:
                    m["content"] = round(m["content"] * factor, 1)
                st.rerun()


# === PAGE 2: 磨矿参数分析 ===
elif page == "\U0001f4ca \u78e8\u77ff\u53c2\u6570\u5206\u6790":
    st.markdown("<div class='main-header'>\u78e8\u77ff\u53c2\u6570\u5206\u6790</div>", unsafe_allow_html=True)
    from core.liberation import liberation_degree
    from core.bond import bond_energy, reduction_ratio

    mineral_composition = st.session_state.get("mineral_composition", [])
    valuable = [m for m in mineral_composition if m.get("mineral_type") == "valuable"]

    st.markdown("<div class='sub-header'>\u5165\u78e8\u53c2\u6570</div>", unsafe_allow_html=True)
    col_in1, col_in2, col_in3, col_in4 = st.columns(4)
    with col_in1: f80 = st.number_input("F80 (um)", 100, 50000, 10000, 500)
    with col_in2: target_p80 = st.number_input("\u76ee\u6807 P80 (um)", 5, 500, 74, 5)
    with col_in3: mill_type = st.selectbox("\u78e8\u673a\u7c7b\u578b", ["\u7403\u78e8\u673a","\u68d2\u78e8\u673a","\u81ea\u78e8\u673a"])
    with col_in4: target_liberation = st.slider("\u76ee\u6807\u89e3\u79bb\u5ea6 (%)", 50, 100, 85, 5)

    col_wi, col_batch = st.columns([1, 1])
    with col_wi:
        st.markdown("<div class='sub-header'>\u77ff\u7269\u53c2\u6570</div>", unsafe_allow_html=True)
        if mineral_composition:
            total_c = sum(m["content"] for m in mineral_composition) or 1
            avg_wi = sum(m["bond_wi"]*m["content"] for m in mineral_composition) / total_c
            st.info("\u52a0\u6743\u5e73\u5747Wi: %.1f | %s" % (avg_wi, classify_grindability(avg_wi)))
            if valuable:
                vg_sizes = [m["grain_size"] for m in valuable]
                st.info("\u76ee\u7684\u77ff\u7269\u5d4c\u5e03: %d-%dum" % (min(vg_sizes), max(vg_sizes)))
        else:
            avg_wi = st.number_input("Bond Wi (kWh/t)", 5.0, 50.0, 14.2, 0.5)
            st.caption("\u672a\u6dfb\u52a0\u77ff\u7269\u7ec4\u6210\uff0c\u4f7f\u7528\u624b\u52a8\u8f93\u5165\u7684 Wi")

    with col_batch:
        st.markdown("<div class='sub-header'>\u5b9e\u9a8c\u5ba4\u6279\u78e8\u53c2\u6570</div>", unsafe_allow_html=True)
        grind_time_input = st.number_input("\u78e8\u77ff\u65f6\u95f4 (min)", 1, 300, 15, 5, help="\u8f93\u5165\u6279\u78e8\u5b9e\u9a8c\u7684\u78e8\u77ff\u65f6\u95f4")
        kk_preview = estimate_k_from_wi(avg_wi, mill_type)
        p80_preview = f80 * np.exp(-kk_preview * grind_time_input * 1.8)
        predicted_p80 = max(round(p80_preview, 0), 5)
        time_to_target_preview = round(-np.log(target_p80/f80) / (kk_preview * 1.8) if kk_preview > 0 else 999, 1)
        st.caption("\u8f93\u5165\u65f6\u95f4 %.0f min \u2192 P80 \u2248 %d um | \u76ee\u6807 P80=%d um \u9700 %.1f min" % (grind_time_input, predicted_p80, target_p80, time_to_target_preview))

    st.markdown("---")
    if st.button("\u5f00\u59cb\u5206\u6790", type="primary", width="stretch"):
        if target_p80 >= f80:
            st.error("目标 P80 必须小于 F80。")
        elif avg_wi <= 0 or grind_time_input <= 0:
            st.error("Bond Wi 和磨矿时间必须大于 0。")
        else:
            st.session_state.analysis_done = False
            with st.spinner("\u8ba1\u7b97\u4e2d..."):
                kk = estimate_k_from_wi(avg_wi, mill_type)
                pred_p80 = max(f80 * np.exp(-kk * grind_time_input * 1.8), 5)
                time_to_target = round(-np.log(target_p80/f80) / (kk * 1.8) if kk > 0 else 999, 1)

                energy = bond_energy(avg_wi, f80, target_p80)
                rr = round(f80 / target_p80, 2) if target_p80 > 0 else 0
                curve = next(iter(simulate_grinding_curve(avg_wi, f80, [grind_time_input], mill_type).values()))

                st.session_state.results = {
                    "predicted_p80": round(pred_p80, 1),
                    "time_to_target": time_to_target,
                    "energy_per_ton": round(energy, 2),
                    "reduction_ratio": rr,
                    "kinetics_k": kk,
                    "sim_results": {round(float(grind_time_input), 4): curve},
                    "params": {"f80":f80, "target_p80":target_p80, "mill_type":mill_type, "avg_wi":round(avg_wi,1), "target_liberation":target_liberation, "grind_time":grind_time_input}
                }
                st.session_state.analysis_done = True
                st.rerun()

    if st.session_state.get("analysis_done", False):
        r = st.session_state.results; p = r["params"]
        pred = r["predicted_p80"]

        st.markdown("---")
        ca, cb, cc, cd = st.columns(4)
        ca.markdown("<div class='stat-card'><div class='stat-value'>%d</div><div class='stat-label'>\u8f93\u5165\u65f6\u95f4 P80 (um)</div></div>" % pred, unsafe_allow_html=True)
        cb.markdown("<div class='stat-card'><div class='stat-value'>%.1f</div><div class='stat-label'>\u8fbe\u76ee\u6807\u65f6\u95f4 (min)</div></div>" % r["time_to_target"], unsafe_allow_html=True)
        cc.markdown("<div class='stat-card'><div class='stat-value'>%.2f</div><div class='stat-label'>\u6bd4\u80fd\u8017 (kWh/t)</div></div>" % r["energy_per_ton"], unsafe_allow_html=True)
        cd.markdown("<div class='stat-card'><div class='stat-value'>%.1f</div><div class='stat-label'>\u7834\u788e\u6bd4 R</div></div>" % r["reduction_ratio"], unsafe_allow_html=True)

        if pred > p["target_p80"]:
            st.warning("\u23f0 \u8f93\u5165\u78e8\u77ff\u65f6\u95f4 %d min \u4ec5\u80fd\u78e8\u81f3 P80=%d um\uff0c\u672a\u8fbe\u5230\u76ee\u6807 P80=%d um\u3002\u9700\u5c06\u65f6\u95f4\u589e\u81f3\u7ea7 %.1f min\u3002" % (p["grind_time"], pred, p["target_p80"], r["time_to_target"]))
        else:
            st.success("\u2713 \u8f93\u5165\u65f6\u95f4 %d min \u5df2\u8fbe\u5230\u76ee\u6807 P80=%d um\u3002" % (p["grind_time"], p["target_p80"]))

        st.markdown("---")

        # Liberation check
        if mineral_composition and valuable:
            try:
                st.markdown("---")
                st.markdown("<div class='sub-header'>\u89e3\u79bb\u5ea6\u76ee\u6807\u6821\u9a8c</div>", unsafe_allow_html=True)
                tc = sum(m["content"] for m in mineral_composition) or 1
                for m in valuable:
                    gs = m.get("grain_size", 100)
                    tex = m.get("texture", "simple")
                    ratio = m["content"] / tc
                    lib = liberation_degree(gs, p["target_p80"], mineral_ratio=ratio, texture=tex) * 100
                    if lib < p["target_liberation"]:
                        st.warning("%s\u5728P80=%dum\u65f6\u89e3\u79bb\u5ea6\u4ec5%.1f%%，\u4f4e\u4e8e\u76ee\u6807%d%%。" % (m["name"], p["target_p80"], lib, p["target_liberation"]))
                    else:
                        st.success("%s\u5728P80=%dum\u65f6\u89e3\u79bb\u5ea6\u4e3a%.1f%%，\u8fbe\u5230\u76ee\u6807%d%%。" % (m["name"], p["target_p80"], lib, p["target_liberation"]))
            except Exception as e:
                st.caption("\u89e3\u79bb\u6821\u9a8c\u65e0\u6548: %s" % e)
        if mineral_composition:
            st.markdown("---")
            st.markdown("<div class='sub-header'>\u89e3\u79bb\u5ea6\u9884\u6d4b</div>", unsafe_allow_html=True)
            from core.liberation import liberation_degree, get_liberation_summary
            tc = sum(m["content"] for m in mineral_composition) or 1
            pred_libs = {}
            for m in mineral_composition:
                gs = m.get("grain_size", 100)
                tex = m.get("texture", "simple")
                ratio = m["content"] / tc
                lib = liberation_degree(gs, p["target_p80"], mineral_ratio=ratio, texture=tex) * 100
                pred_libs[m["name"]] = round(lib, 1)
            tex = max([m.get("texture","simple") for m in mineral_composition], default="simple")
            st.markdown("<div class='highlight-box'>%s</div>" % get_liberation_summary(tex), unsafe_allow_html=True)
            st.caption("\u4ee5\u76ee\u6807 P80=%d um \u8ba1\u7b97" % p["target_p80"])
            dl = pd.DataFrame([{"\u77ff\u7269":k, "\u89e3\u79bb\u5ea6(%)":v} for k,v in pred_libs.items()])
            st.dataframe(dl, width="stretch", hide_index=True)
# === PAGE 3: 动力学模拟 ===
elif page == "📈 动力学模拟":
    st.markdown("<div class='main-header'>磨矿动力学模拟</div>", unsafe_allow_html=True)
    from core.kinetics import simulate_grinding_curve, estimate_k_from_wi
    from core.liberation import liberation_degree

    mineral_composition = st.session_state.get("mineral_composition", [])
    valuable = [m for m in mineral_composition if m.get("mineral_type") == "valuable"]

    ca, cb, cc, cd = st.columns(4)
    with ca:
        if mineral_composition:
            total_c = sum(m.get("content",0) for m in mineral_composition) or 1
            avg_wi = sum(m.get("bond_wi",12)*m.get("content",0) for m in mineral_composition) / total_c
        else:
            avg_wi = 14.2
        swi = st.number_input("Bond Wi (kWh/t)", 5.0, 50.0, round(avg_wi,1), 0.5)
    with cb: sf80 = st.number_input("F80 (um)", 100, 50000, 10000, 500)
    with cc: sp80 = st.number_input("目标 P80 (um)", 5, 500, 74, 5)
    with cd: smill = st.selectbox("磨机类型", ["球磨机","棒磨机","自磨机"])

    cta, ctb = st.columns([1, 1])
    with cta:
        sim_tmin = st.number_input("模拟起始时间 (min)", 0.0, 100.0, 0.0, 0.5)
    with ctb:
        sim_tmax = st.number_input("模拟结束时间 (min)", 1.0, 600.0, 10.0, 0.5)

    if st.button("运行模拟", type="primary", width="stretch"):
            if sim_tmax <= sim_tmin:
                st.error("结束时间需大于起始时间。")
            else:
                kk = estimate_k_from_wi(swi, smill)
                sim_t = np.arange(sim_tmin, sim_tmax + 0.0001, 0.05)
                sim_res = simulate_grinding_curve(swi, sf80, sim_t, smill)
                st.session_state.sim = {"k": kk, "results": sim_res, "f80": sf80, "target_p80": sp80, "wi": swi,
                                        "max_time": sim_tmax, "tmin": sim_tmin, "tmax": sim_tmax}

    if "sim" in st.session_state:
        sd = st.session_state["sim"]
        sim_res = sd["results"]
        kk = sd["k"]

        st.markdown("---")
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.markdown("<div class='sub-header'>P80 随时间变化</div>", unsafe_allow_html=True)
            y_max = st.slider("Y轴最大显示范围", min_value=100, max_value=10000, value=100, step=100)
            times = sorted(sim_res.keys()); p80s = [sim_res[t]["p80"] for t in times]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=times, y=p80s, mode="lines", name="当前P80", line=dict(color="#2196F3", width=3)))
            fig.add_trace(go.Scatter(x=[min(times), max(times)], y=[sd["target_p80"], sd["target_p80"]],
                                     mode="lines", name="目标P80=%dum" % sd["target_p80"],
                                     line=dict(color="red", width=2, dash="dash")))
            target_p80 = float(sd["target_p80"])
            fig.add_annotation(x=10.42, y=min(100, target_p80 + 8), text="目标P80=%dum" % sd["target_p80"],
                               showarrow=False, font=dict(color="red", size=12), xanchor="right")
            t_target = -np.log(target_p80 / sd["f80"]) / (kk * 1.8) if kk > 0 and target_p80 < sd["f80"] else None
            if t_target is not None and t_target >= min(times) and t_target <= max(times):
                fig.add_vline(x=t_target, line_dash="dot", line_color="gray")
                fig.add_trace(go.Scatter(x=[t_target], y=[target_p80], mode="markers",
                                         marker=dict(size=13, color="#FF9800", symbol="circle",
                                                      line=dict(width=2, color="#FFFFFF")),
                                         name="达到目标", showlegend=False, hoverinfo="x+y"))
                fig.add_annotation(x=t_target, y=95, text="达到目标时间：%.2f min" % t_target,
                                   showarrow=False, font=dict(size=13, color="#D32F2F"),
                                   xanchor="center", yanchor="top")
            fig.add_annotation(x=max(times), y=p80s[-1], text="当前P80", showarrow=False,
                              font=dict(size=12, color="#2196F3"), xanchor="left", yanchor="middle")
            fig.update_layout(xaxis_title="时间(min)", yaxis_title="P80(um)", height=430,
                              margin=dict(l=20,r=20,t=20,b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
            fig.update_yaxes(range=[0, y_max])
            fig.update_xaxes(range=[0, 10.5], tick0=0, dtick=1)
            st.plotly_chart(fig, width="stretch")
            st.caption("默认视图已截断初始粗颗粒，请拖动滑块查看全局或细节。")
            target_times = [(t, v["p80"]) for t, v in sim_res.items() if v["p80"] <= sd["target_p80"]]
            if target_times:
                st.success("达到目标P80<=%dum 约需 %.1f min" % (sd["target_p80"], target_times[0][0]))
            else:
                st.warning("当前模拟范围（%dmin）内未达到目标P80=%dum，预计需约 %.1f min。" % (sd.get("max_time",60), sd["target_p80"], -np.log(sd["target_p80"]/sd["f80"])/(sd["k"] * 1.8) if sd["k"] > 0 and sd["target_p80"] < sd["f80"] else 999))

        with col2:
            st.markdown("<div class='sub-header'>参数</div>", unsafe_allow_html=True)
            st.markdown("<div style='background:#f0f2f6;padding:1rem;border-radius:8px;'>Wi: %.1f kWh/t<br>k: %.4f min<sup>-1</sup><br>F80: %d um<br>P80目标: %d um</div>" % (sd["wi"], kk, sd["f80"], sd["target_p80"]), unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("<div class='sub-header'>解离度随时间变化</div>", unsafe_allow_html=True)
        sel_t = st.slider(
            "当前时间 (min)",
            min_value=float(min(times)),
            max_value=float(max(times)),
            value=float(times[len(times) // 2]),
            step=0.05,
        )
        sel_key = min(sim_res, key=lambda k: abs(k - sel_t))
        st.caption("t=%g min 时 P80=%d um" % (sel_key, sim_res[sel_key]["p80"]))

        if valuable:
            total_content = sum(m.get("content", 0) for m in mineral_composition) or 1
            valuable_content = sum(m.get("content", 0) for m in valuable) or 1
            liberation_series = {}
            weighted_liberation = [0.0] * len(times)

            for m in valuable:
                content = m.get("content", 0)
                mineral_ratio = content / total_content
                texture = m.get("texture", "simple")
                grain_size = m.get("grain_size", 100)
                values = [
                    liberation_degree(
                        grain_size,
                        sim_res[t]["p80"],
                        mineral_ratio=mineral_ratio,
                        texture=texture,
                    ) * 100
                    for t in times
                ]
                liberation_series[m["name"]] = values
                for idx, value in enumerate(values):
                    weighted_liberation[idx] += value * content

            weighted_liberation = [value / valuable_content for value in weighted_liberation]
            fig_lib = go.Figure()
            if len(valuable) > 1:
                fig_lib.add_trace(go.Scatter(
                    x=times,
                    y=weighted_liberation,
                    mode="lines",
                    name="含量加权平均",
                    line=dict(color="#263238", width=3),
                ))

            line_colors = ["#1E88E5", "#FB8C00", "#43A047", "#8E24AA", "#E53935", "#00ACC1", "#FDD835"]
            for idx, (name, values) in enumerate(liberation_series.items()):
                color = "#1E88E5" if "萤石" in name else line_colors[idx % len(line_colors)]
                fig_lib.add_trace(go.Scatter(
                    x=times,
                    y=values,
                    mode="lines",
                    name=name,
                    line=dict(color=color, width=3),
                ))

            analysis_result = st.session_state.get("results") or {}
            target_liberation = analysis_result.get("params", {}).get("target_liberation")
            if target_liberation is not None:
                fig_lib.add_hline(
                    y=target_liberation,
                    line_dash="dash",
                    line_color="#D32F2F",
                    annotation_text="目标解离度 %d%%" % target_liberation,
                    annotation_position="top left",
                )

            selected_idx = min(range(len(times)), key=lambda i: abs(times[i] - sel_key))
            fig_lib.add_vline(x=times[selected_idx], line_dash="dot", line_color="#FF9800")
            fig_lib.add_trace(go.Scatter(
                x=[times[selected_idx]],
                y=[weighted_liberation[selected_idx]],
                mode="markers",
                name="当前时间",
                showlegend=False,
                marker=dict(size=12, color="#FF9800", line=dict(width=2, color="#FFFFFF")),
            ))
            fig_lib.update_layout(
                xaxis_title="时间(min)",
                yaxis_title="解离度(%)",
                height=430,
                margin=dict(l=20, r=20, t=20, b=20),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            )
            fig_lib.update_yaxes(range=[0, 100], dtick=10)
            fig_lib.update_xaxes(range=[min(times), max(times)])
            st.plotly_chart(fig_lib, width="stretch")
            st.caption(
                "t=%g min 时含量加权平均解离度为 %.1f%%"
                % (times[selected_idx], weighted_liberation[selected_idx])
            )
        elif mineral_composition:
            st.info("矿物组成中尚无目的矿物，暂无法计算解离度。")
        else:
            st.info("未添加矿物组成，暂无法计算解离度。")

        st.markdown("---")
        st.markdown("<div class='sub-header'>粒度分布曲线</div>", unsafe_allow_html=True)
        sel = st.multiselect("选择对比时间点", sorted(sim_res.keys()), default=[sorted(sim_res.keys())[0], sorted(sim_res.keys())[len(sim_res)//2], sorted(sim_res.keys())[-1]])
        if sel:
            fig = go.Figure()
            for t in sel:
                d = sim_res[t]
                fig.add_trace(go.Scatter(x=d["sieve"], y=d["passing"], mode="lines+markers", name="t=%gmin P80=%dum" % (t, d["p80"])))
            fig.update_layout(xaxis_title="粒度(um)", yaxis_title="通过率(%)", xaxis_type="log", height=450)
            fig.update_xaxes(tickvals=[10,38,74,100,150,200,300,500,1000,2000])
            st.plotly_chart(fig, width="stretch")

        if mineral_composition:
            st.markdown("---")
            st.markdown("<div class='sub-header'>解离分析建议</div>", unsafe_allow_html=True)
            from core.liberation import recommend_grind_strategy
            rec = recommend_grind_strategy(mineral_composition, target_liberation=0.85)
            if "error" not in rec:
                st.markdown("<div class='highlight-box'><b>推荐磨矿细度:</b> P80=%d um<br><b>嵌布类型:</b> %s<br><b>最大理论解离度:</b> %d%%</div>" % (rec["recommended_p80"], rec["texture_description"], rec["max_possible_liberation"]), unsafe_allow_html=True)
            else:
                st.info(rec["error"])
# === PAGE 4: 筛析数据分析 ===
elif page == "🔬 筛析数据分析":
    st.markdown("<div class='main-header'>筛析数据导入与 RR 拟合</div>", unsafe_allow_html=True)
    st.markdown("上传实验筛析数据，自动拟合 Rosin-Rammler 参数，计算 P80/F80")

    tab1, tab2 = st.tabs(["📤 导入数据", "📈 拟合结果"])

    with tab1:
        st.markdown("<div class='sub-header'>上传筛析数据</div>", unsafe_allow_html=True)
        st.markdown("CSV 格式：第一列为筛孔尺寸(um)，第二列为累计通过率(%)，可包含表头行")

        uploaded_file = st.file_uploader("选择 CSV 文件", type=["csv", "txt"], label_visibility="collapsed")
        st.markdown("或手动输入")
        paste_data = st.text_area("粘贴数据",
            placeholder="粒度(um), 累计通过率(%)\n1000, 95.2\n500, 82.1\n200, 63.5\n100, 42.3\n74, 28.6\n45, 15.2\n38, 10.8",
            height=200, label_visibility="collapsed")

        col_a, col_b = st.columns([1, 3])
        with col_a:
            fit_btn = st.button("拟 合", type="primary", width="stretch")

        if fit_btn:
            csv_text = None
            if uploaded_file is not None:
                csv_text = uploaded_file.getvalue().decode("utf-8")
            elif paste_data.strip():
                csv_text = paste_data

            if csv_text:
                try:
                    sizes, passing = read_sieve_csv(csv_text)
                    if len(sizes) < 3 or np.any(sizes <= 0) or np.any((passing < 0) | (passing > 100)):
                        st.error("筛析数据至少需要 3 个有效点，粒度和通过率必须有效。")
                    else:
                        result = fit_rosin_rammler(sizes, passing)

                        if isinstance(result, dict) and result["n"] > 0 and result["r_squared"] > 0:
                            st.session_state.sieve_result = result
                            st.session_state.sieve_raw = (sizes, passing)
                            st.rerun()
                        else:
                            st.error("拟合失败：数据点太少（至少需要 3 个有效点），或粒度分布不符合 RR 模型")
                except Exception as e:
                    st.error(f"解析数据出错: {e}")
            else:
                st.info("请先上传 CSV 或粘贴数据")

        # 示例数据
        with st.expander("查看示例数据格式"):
            st.code("粒度,通过率\n1000,95.2\n500,82.1\n200,63.5\n100,42.3\n74,28.6\n45,15.2\n38,10.8", language="csv")
            if st.button("加载示例数据", width="stretch"):
                example = "粒度,通过率\n1000,95.2\n500,82.1\n200,63.5\n100,42.3\n74,28.6\n45,15.2\n38,10.8"
                sizes, passing = read_sieve_csv(example)
                result = fit_rosin_rammler(sizes, passing)
                if isinstance(result, dict) and result["n"] > 0:
                    st.session_state.sieve_result = result
                    st.session_state.sieve_raw = (sizes, passing)
                    st.rerun()

    with tab2:
        if "sieve_result" not in st.session_state:
            st.info("← 请先在「导入数据」标签页上传筛析数据并点击拟合")
            st.stop()

        r = st.session_state.sieve_result
        sizes_raw, passing_raw = st.session_state.sieve_raw

        # 参数卡片
        ca, cb, cc, cd = st.columns(4)
        ca.markdown(f"<div class='stat-card'><div class='stat-value'>{r['n']}</div><div class='stat-label'>均匀性指数 n</div></div>", unsafe_allow_html=True)
        cb.markdown(f"<div class='stat-card'><div class='stat-value'>{r['d63']}</div><div class='stat-label'>特征粒度 d63(um)</div></div>", unsafe_allow_html=True)
        cc.markdown(f"<div class='stat-card'><div class='stat-value'>{r['r_squared']}</div><div class='stat-label'>拟合优度 R²</div></div>", unsafe_allow_html=True)
        cd.markdown(f"<div class='stat-card'><div class='stat-value'>{r['p80']}</div><div class='stat-label'>P80(um)</div></div>", unsafe_allow_html=True)

        # 拟合图
        st.markdown("---")
        st.markdown("<div class='sub-header'>粒度分布拟合</div>", unsafe_allow_html=True)

        col1, col2 = st.columns([1.5, 1])

        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=sizes_raw, y=passing_raw, mode="markers",
                name="实验数据", marker=dict(size=8, color="#2196F3", symbol="circle")))
            fig.add_trace(go.Scatter(x=r["fitted_curve"]["sieve"], y=r["fitted_curve"]["passing"],
                mode="lines", name="RR 拟合", line=dict(color="#FF5722", width=2, dash="dash")))
            fig.add_hline(y=80, line_dash="dot", line_color="green",
                annotation_text=f"P80={r['p80']}um")
            fig.update_layout(
                xaxis_title="粒度 (um)", yaxis_title="累计通过率 (%)",
                xaxis_type="log", height=420,
                margin=dict(l=20, r=20, t=20, b=20))
            fig.update_xaxes(tickvals=[10, 38, 45, 74, 100, 150, 200, 300, 500, 1000, 2000])
            st.plotly_chart(fig, width="stretch")

        with col2:
            st.markdown("<div class='sub-header'>拟合参数</div>", unsafe_allow_html=True)
            st.markdown(f"**RR 模型:** R(d) = exp(-(d/{r['d63']})<sup>{r['n']}</sup>)")
            st.markdown(f"**P80** = {r['p80']} um")
            st.markdown(f"**P50** = {r['p50']} um")
            st.markdown(f"**P20** = {r['p20']} um")
            st.markdown(f"**F80** ≈ {r['f80']} um (外推)")

            # RR 线性回归图
            st.markdown("---")
            st.markdown("<div class='sub-header'>RR 线性回归</div>", unsafe_allow_html=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=r["regression"]["x"], y=r["regression"]["y"],
                mode="markers", name="数据点", marker=dict(size=6, color="#4CAF50")))
            fig2.add_trace(go.Scatter(x=r["regression"]["x"], y=r["regression"]["y_fit"],
                mode="lines", name="拟合线", line=dict(color="#FF5722", width=2)))
            fig2.update_layout(
                xaxis_title="ln(d)", yaxis_title="ln(-ln(1-R))", height=280,
                margin=dict(l=20, r=20, t=10, b=20), showlegend=False)
            st.plotly_chart(fig2, width="stretch")
            st.caption(f"斜率 n = {r['n']} | R² = {r['r_squared']}")

        # 与动力学模拟对比
        if st.session_state.get("analysis_done", False) and "sim_results" in st.session_state.results:
            st.markdown("---")
            st.markdown("<div class='sub-header'>与动力学模拟对比</div>", unsafe_allow_html=True)
            sim = st.session_state.results["sim_results"]
            sim_times = sorted(sim.keys())
            target_p80 = st.session_state.results["params"]["target_p80"]

            closest_t = min(sim_times, key=lambda t: abs(sim[t]["p80"] - r["p80"]))

            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=r["fitted_curve"]["sieve"], y=r["fitted_curve"]["passing"],
                mode="lines", name=f"实测拟合 (P80={r['p80']}um)",
                line=dict(color="#2196F3", width=3)))
            fig3.add_trace(go.Scatter(x=sim[closest_t]["sieve"], y=sim[closest_t]["passing"],
                mode="lines", name=f"模拟 t={closest_t}min (P80={sim[closest_t]['p80']}um)",
                line=dict(color="#FF5722", width=2, dash="dash")))
            fig3.update_layout(
                xaxis_title="粒度 (um)", yaxis_title="累计通过率 (%)",
                xaxis_type="log", height=400,
                margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig3, width="stretch")
            st.info(f"模拟曲线对应磨矿时间 t={closest_t}min，P80={sim[closest_t]['p80']}um。"
                    f"实测 P80={r['p80']}um，差异可作为模型校准参考。")

# === 结果报告 ===
elif page == "📑 结果报告":
    st.markdown("<div class='main-header'>分析结果报告</div>", unsafe_allow_html=True)
    if not st.session_state.get("analysis_done", False):
        st.warning("请先完成磨矿参数分析")
        st.stop()

    r = st.session_state.results
    p = r["params"]
    ca, cb = st.columns(2)
    with ca:
        st.markdown("<div style='background:#f0f2f6;padding:1rem;border-radius:8px;'><h4>矿物组成</h4>", unsafe_allow_html=True)
        for mineral in st.session_state.mineral_composition:
            mineral_type = {"valuable": "目的", "gangue": "脉石"}.get(mineral["mineral_type"], "")
            st.markdown(
                f"- {mineral['name']} {mineral['content']}% | 嵌布 {mineral['grain_size']} um "
                f"| Wi {mineral['bond_wi']} | {mineral_type}"
            )
        st.markdown("</div>", unsafe_allow_html=True)
    with cb:
        st.markdown("<div style='background:#f0f2f6;padding:1rem;border-radius:8px;'><h4>工艺参数</h4>", unsafe_allow_html=True)
        st.markdown(
            f"F80: {p['f80']} um | 目标 P80: {p['target_p80']} um<br>"
            f"加权 Wi: {p['avg_wi']} kWh/t | {classify_grindability(p['avg_wi'])}<br>"
            f"{p['mill_type']} | 批磨时间: {p['grind_time']} min",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f"<div class='highlight-box'><h3>分析结果</h3>"
        f"预测 P80: {r['predicted_p80']} um<br>"
        f"达目标时间: {r['time_to_target']:.1f} min<br>"
        f"比能耗: {r['energy_per_ton']:.2f} kWh/t<br>"
        f"破碎比: {r['reduction_ratio']:.2f}</div>",
        unsafe_allow_html=True,
    )

    report_lines = [
        "# 工艺矿物学磨矿分析报告（经典版）",
        "",
        "## 矿物组成",
        *[
            f"- {mineral['name']}: {mineral['content']}%，嵌布 {mineral['grain_size']} um，Wi {mineral['bond_wi']}"
            for mineral in st.session_state.mineral_composition
        ],
        "",
        "## 工艺参数",
        f"- F80: {p['f80']} um",
        f"- 目标 P80: {p['target_p80']} um",
        f"- 加权 Bond Wi: {p['avg_wi']} kWh/t",
        f"- 磨机类型: {p['mill_type']}",
        f"- 批磨时间: {p['grind_time']} min",
        "",
        "## 结果",
        f"- 预测 P80: {r['predicted_p80']} um",
        f"- 达目标时间: {r['time_to_target']:.1f} min",
        f"- 比能耗: {r['energy_per_ton']:.2f} kWh/t",
        f"- 破碎比: {r['reduction_ratio']:.2f}",
    ]
    st.download_button(
        "下载 Markdown 报告",
        data="\n".join(report_lines).encode("utf-8"),
        file_name="磨矿分析报告_经典版.md",
        mime="text/markdown",
        width="stretch",
    )
