import json
import streamlit as st
from pipeline import run_pipeline
from utils import load_topology

# 页面基本配置
st.set_page_config(page_title="NetIntent-Agent", page_icon="🌐", layout="wide")

# 全局高定自定义 CSS (Dark Mode Glassmorphism 风格)
st.markdown("""
<style>
    .main-title {
        background: -webkit-linear-gradient(45deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5em !important;
        font-weight: 900;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    .sub-title {
        color: #A0AAB2;
        font-size: 1.2em;
        margin-top: -10px;
        margin-bottom: 2em;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 242, 254, 0.4);
        color: white;
    }
    .section-header {
        font-size: 1.5em;
        color: #00f2fe;
        border-bottom: 1px solid #333;
        padding-bottom: 10px;
        margin-top: 30px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 头部标题
st.markdown('<p class="main-title">NetIntent-Agent 🌐</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">面向智能体互联网的意图驱动网络自治运维系统</p>', unsafe_allow_html=True)

# 示例数据
examples = [
    "禁止学生网段访问管理服务器，但允许教师网段访问。",
    "保证客户端到服务器的延迟低于50ms。"
]

# ===== 布局开始 =====
col_left, col_right = st.columns([2, 1])

with col_left:
    # 区域 1：自然语言输入区
    st.markdown('<div class="section-header">💬 自然语言输入区</div>', unsafe_allow_html=True)
    def update_text(text):
        st.session_state.user_input_key = text

    if "user_input_key" not in st.session_state:
        st.session_state.user_input_key = examples[0]
        
    user_input = st.text_area("请输入您的网络控制意图：", key="user_input_key", height=120)
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        st.button("📌 访问控制示例", on_click=update_text, args=(examples[0],))
    with col_btn2:
        st.button("📌 低延迟自愈示例", on_click=update_text, args=(examples[1],))
    with col_btn3:
        run_clicked = st.button("🚀 一键执行网络自愈闭环", type="primary", use_container_width=True)

with col_right:
    # 区域 2：网络拓扑展示区
    st.markdown('<div class="section-header">🕸️ 网络拓扑展示区</div>', unsafe_allow_html=True)
    st.info("当前系统网络环境拓扑概览")
    # 尝试加载真实拓扑，若失败则展示占位符
    try:
        topo_data = load_topology()
        with st.expander("📄 查看详细拓扑 JSON", expanded=False):
            st.json(topo_data)
    except Exception:
        st.warning("暂未获取到拓扑数据，使用默认配置。")

    # 可视化字符拓扑 (对应文档中的拓扑结构)
    st.code('''
[访问控制]
student_host ---- s1 ---- s2 ---- admin_server
teacher_host ----/

[链路自愈]
client_host ---- s3 ---- s4 ---- server
               \       /
                -- s5 --
    ''', language="text")

# 分割线
st.divider()

# ===== 核心执行流程展示 =====
if run_clicked:
    with st.spinner("🧠 智能体集群正在规划与执行..."):
        try:
            # 调用成员1的接口
            result = run_pipeline(user_input)
            
            # 顶部状态横幅
            if result.get("final_status") == "success":
                st.success("✅ 网络策略配置与验证成功闭环！")
            else:
                st.error(f"❌ 流程执行失败或未达成目标：{result.get('final_status')}")

            # 布局下半部分为三列
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                # 区域 3：Agent 执行日志区
                st.markdown('<div class="section-header">🧠 Agent执行日志区</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown("**Intent Agent 解析意图:**")
                    st.json(result.get("intent", {}))
                    
                    st.markdown("**Planner Agent 策略规划:**")
                    st.json(result.get("policy", {}))
                    
                    with st.expander("查看完整步骤日志", expanded=False):
                        for log_item in result.get("logs", []):
                            st.text(f"[{log_item.get('step', 'N/A')}]")
                            st.json(log_item)

            with col_b:
                # 区域 4：生成命令展示区
                st.markdown('<div class="section-header">⚡ 生成命令展示区</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    exec_res = result.get("execute_result", {})
                    status = exec_res.get("execute_status", "unknown")
                    
                    if status == "success":
                        st.success("命令下发状态：成功")
                    else:
                        st.warning(f"命令下发状态：{status}")
                        
                    st.markdown("**实际执行的底层命令:**")
                    cmd = exec_res.get("executed_command") or exec_res.get("command") or "No command found"
                    st.code(cmd, language="bash")
                    
                    if "message" in exec_res:
                        st.info(f"反馈: {exec_res['message']}")

            with col_c:
                # 区域 5：验证结果展示区 (包含重规划)
                st.markdown('<div class="section-header">🔍 验证与重规划区</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    verify_res = result.get("verify_result", {})
                    v_status = verify_res.get("verify_status", "unknown")
                    
                    if v_status == "success":
                        st.success("验证通过！目标已达成。")
                    else:
                        st.error("验证失败！触发自愈流程。")
                        
                    st.markdown("**遥测验证数据:**")
                    st.json({
                        "test_tool": verify_res.get("test_tool", "N/A"),
                        "expected": verify_res.get("expected", "N/A"),
                        "actual": verify_res.get("actual", "N/A")
                    })
                    
                    replan_res = result.get("replan_result")
                    if verify_res.get("need_replan") and replan_res:
                        st.markdown("---")
                        st.markdown("**🔄 触发重规划与自愈:**")
                        st.warning("检测到新生成的备用策略！")
                        
                        replan_exec_res = replan_res.get("execute_result", {})
                        replan_cmd = replan_exec_res.get("executed_command") or replan_exec_res.get("command") or "未获取到备用命令"
                        st.code(replan_cmd, language="bash")
                        
        except Exception as e:
            st.error(f"系统异常: {str(e)}")
            st.exception(e)
