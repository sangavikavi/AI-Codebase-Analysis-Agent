import os
import json
import time
import requests
import streamlit as st
import streamlit.components.v1 as components
from styles import CUSTOM_CSS, render_mermaid

# Backend Base URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page Configuration
st.set_page_config(
    page_title="Multi-Agent Codebase Analysis & Documentation System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Session State Initialization
if "token" not in st.session_state:
    st.session_state.token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_role" not in st.session_state:
    st.session_state.user_role = "user"
if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = None
if "active_project_name" not in st.session_state:
    st.session_state.active_project_name = None


def get_headers():
    """Return authorization bearer headers if logged in."""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


# ==========================================
# AUTHENTICATION SCREEN
# ==========================================
if not st.session_state.token:
    st.markdown("<h1 style='text-align: center; color: #3b82f6;'>🤖 Multi-Agent Codebase Analysis</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 1.1rem;'>Transform any codebase into role-specific SDE & PM documentation, Mermaid diagrams, and RAG intelligence.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Create Account"])

        with auth_tab1:
            with st.form("login_form"):
                login_email = st.text_input("Email Address", value="admin@example.com")
                login_password = st.text_input("Password", type="password", value="adminpassword123")
                login_submitted = st.form_submit_button("Sign In", use_container_width=True)

                if login_submitted:
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/api/auth/login",
                            json={"email": login_email, "password": login_password},
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.token = data["access_token"]
                            st.session_state.user_email = data["email"]
                            st.session_state.user_role = data["role"]
                            st.success("Signed in successfully!")
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Login failed."))
                    except Exception as e:
                        st.error(f"Error connecting to backend: {str(e)}")

        with auth_tab2:
            with st.form("signup_form"):
                reg_email = st.text_input("Work Email Address")
                reg_password = st.text_input("Password (min 6 chars)", type="password")
                reg_role = st.selectbox("Role", ["user", "admin"])
                reg_submitted = st.form_submit_button("Create Account", use_container_width=True)

                if reg_submitted:
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/api/auth/register",
                            json={"email": reg_email, "password": reg_password, "role": reg_role},
                            timeout=10,
                        )
                        if resp.status_code == 201:
                            st.success("Account created! Please sign in using the Sign In tab.")
                        else:
                            st.error(resp.json().get("detail", "Registration failed."))
                    except Exception as e:
                        st.error(f"Error connecting to backend: {str(e)}")
    st.stop()


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_email}")
    role_color = "#3b82f6" if st.session_state.user_role == "admin" else "#10b981"
    st.markdown(f"<span style='background: {role_color}22; color: {role_color}; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.8rem;'>ROLE: {st.session_state.user_role.upper()}</span>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)

    nav_options = [
        "📂 Projects Dashboard",
        "➕ Create Project",
        "⚡ Live Analysis & Control",
        "📄 Documentation & Reports",
        "💬 Codebase RAG Q&A",
    ]
    if st.session_state.user_role == "admin":
        nav_options.append("🛡️ Admin Dashboard")

    selected_view = st.radio("Navigation", nav_options, label_visibility="collapsed")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.token = None
        st.session_state.user_email = None
        st.session_state.active_project_id = None
        st.rerun()


# ==========================================
# 1. PROJECTS DASHBOARD
# ==========================================
if selected_view == "📂 Projects Dashboard":
    st.markdown("## 📂 Projects Dashboard")
    st.markdown("View and manage your analyzed software repositories.")

    try:
        resp = requests.get(f"{BACKEND_URL}/api/projects", headers=get_headers(), timeout=10)
        if resp.status_code == 200:
            projects = resp.json()
            if not projects:
                st.info("No projects created yet. Click '➕ Create Project' in the sidebar to analyze your first repository!")
            else:
                for proj in projects:
                    with st.container():
                        col_info, col_stats, col_act = st.columns([3, 2, 2])
                        with col_info:
                            st.markdown(f"### {proj['name']}")
                            st.caption(f"ID: `{proj['id']}` • Created: {proj['created_at'][:10]}")
                            st.markdown(f"**Stack:** `{proj['detected_stack'] or 'Detecting...'}`")

                        with col_stats:
                            badge_cls = f"badge-{proj['status']}"
                            st.markdown(f"<span class='status-badge {badge_cls}'>{proj['status'].upper()}</span>", unsafe_allow_html=True)
                            st.progress(proj["progress_percentage"] / 100.0)
                            st.caption(f"{proj['progress_percentage']:.0f}% • Files: {proj['total_files']} • Endpoints: {proj['endpoint_count']}")

                        with col_act:
                            if st.button("🚀 Open Workspace", key=f"open_{proj['id']}", use_container_width=True):
                                st.session_state.active_project_id = proj["id"]
                                st.session_state.active_project_name = proj["name"]
                                st.success(f"Loaded '{proj['name']}'! Navigating to Live Analysis...")
                                time.sleep(0.5)
                                st.rerun()
                        st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        else:
            st.error("Failed to load projects.")
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")


# ==========================================
# 2. CREATE PROJECT
# ==========================================
elif selected_view == "➕ Create Project":
    st.markdown("## ➕ Create & Analyze New Project")
    st.markdown("Upload a ZIP codebase or provide a public GitHub repository URL.")

    upload_mode = st.radio("Ingestion Source", ["📦 ZIP Codebase Archive", "🐙 Public GitHub URL"], horizontal=True)

    with st.form("create_project_form"):
        project_name = st.text_input("Project Name", placeholder="e.g. My Fast Commerce API")

        # Personas selector
        personas = st.multiselect(
            "Target Persona Documentation",
            options=["sde", "pm"],
            default=["sde", "pm"],
            format_func=lambda x: "SDE (Technical Architecture, API Schemas, DB Models)" if x == "sde" else "PM (Business Features, User Flows, Roadmap)",
        )

        st.markdown("#### ⚙️ Multi-Agent Configuration")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            depth = st.selectbox("Analysis Depth", ["Quick", "Standard", "Deep"], index=1)
            verbosity = st.selectbox("Documentation Verbosity", ["Low", "Medium", "High"], index=1)
        with col_c2:
            include_owasp = st.checkbox("Include OWASP API Security & Best Practices Research", value=True)
            include_diagrams = st.checkbox("Generate 4 Types of Mermaid System Diagrams", value=True)

        zip_file = None
        github_url = None

        if upload_mode == "📦 ZIP Codebase Archive":
            zip_file = st.file_uploader("Upload Codebase ZIP (Max 100MB)", type=["zip"])
        else:
            github_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/owner/repository")

        submit_btn = st.form_submit_button("🚀 Start Multi-Agent Analysis", use_container_width=True)

        if submit_btn:
            if not project_name.strip():
                st.error("Please enter a valid project name.")
            elif not personas:
                st.error("Please select at least one persona (SDE or PM).")
            else:
                config_data = {
                    "depth": depth,
                    "verbosity": verbosity,
                    "feature_toggles": {
                        "include_owasp": include_owasp,
                        "include_diagrams": include_diagrams,
                    },
                    "diagram_preferences": ["architecture", "flowchart", "sequence", "er"],
                }

                if upload_mode == "📦 ZIP Codebase Archive":
                    if not zip_file:
                        st.error("Please upload a ZIP file.")
                    else:
                        with st.spinner("Uploading and validating codebase package..."):
                            files = {"file": (zip_file.name, zip_file.getvalue(), "application/zip")}
                            data = {
                                "name": project_name,
                                "personas": json.dumps(personas),
                                "config": json.dumps(config_data),
                            }
                            resp = requests.post(f"{BACKEND_URL}/api/projects/upload", data=data, files=files, headers=get_headers())
                            if resp.status_code == 201:
                                proj_info = resp.json()
                                st.session_state.active_project_id = proj_info["project_id"]
                                st.session_state.active_project_name = project_name
                                # Launch analysis task in background
                                requests.post(f"{BACKEND_URL}/api/projects/{proj_info['project_id']}/start", headers=get_headers())
                                st.success("Project created and analysis started!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(resp.json().get("detail", "Error creating project from ZIP."))
                else:
                    if not github_url or not github_url.strip():
                        st.error("Please provide a valid GitHub URL.")
                    else:
                        with st.spinner("Validating and cloning GitHub repository..."):
                            payload = {
                                "name": project_name,
                                "github_url": github_url.strip(),
                                "personas": personas,
                                "config": config_data,
                            }
                            resp = requests.post(f"{BACKEND_URL}/api/projects/github", json=payload, headers=get_headers())
                            if resp.status_code == 201:
                                proj_info = resp.json()
                                st.session_state.active_project_id = proj_info["project_id"]
                                st.session_state.active_project_name = project_name
                                requests.post(f"{BACKEND_URL}/api/projects/{proj_info['project_id']}/start", headers=get_headers())
                                st.success("GitHub repository cloned and analysis started!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(resp.json().get("detail", "Error creating project from GitHub."))


# ==========================================
# 3. LIVE ANALYSIS & CONTROL
# ==========================================
elif selected_view == "⚡ Live Analysis & Control":
    if not st.session_state.active_project_id:
        st.warning("No active project selected. Select a project in '📂 Projects Dashboard' or create a new one.")
        st.stop()

    proj_id = st.session_state.active_project_id
    st.markdown(f"## ⚡ Live Analysis & Steering: *{st.session_state.active_project_name or proj_id}*")

    # Fetch latest project details
    proj_resp = requests.get(f"{BACKEND_URL}/api/projects/{proj_id}", headers=get_headers())
    if proj_resp.status_code != 200:
        st.error("Failed to load project details.")
        st.stop()
    proj = proj_resp.json()

    # Progress & Stage Header
    col_p1, col_p2, col_p3 = st.columns([4, 2, 2])
    with col_p1:
        st.progress(proj["progress_percentage"] / 100.0)
        st.caption(f"Stage: **{proj['current_stage']}** • Progress: **{proj['progress_percentage']:.0f}%**")
    with col_p2:
        badge_cls = f"badge-{proj['status']}"
        st.markdown(f"Status: <span class='status-badge {badge_cls}'>{proj['status'].upper()}</span>", unsafe_allow_html=True)
    with col_p3:
        # Pause / Resume interactive controls
        if proj["status"] == "analyzing":
            if st.button("⏸️ Pause Analysis", use_container_width=True):
                requests.post(f"{BACKEND_URL}/api/projects/{proj_id}/pause", headers=get_headers())
                st.warning("Pause requested...")
                time.sleep(0.5)
                st.rerun()
        elif proj["status"] in ["paused", "created"]:
            if st.button("▶️ Resume / Run", use_container_width=True):
                requests.post(f"{BACKEND_URL}/api/projects/{proj_id}/resume", headers=get_headers())
                st.info("Resuming analysis...")
                time.sleep(0.5)
                st.rerun()

    tab_feed, tab_chat = st.tabs(["📡 Structured Activity Feed", "💬 Interactive Chat & Context Steering"])

    with tab_feed:
        st.markdown("#### Live Agent Activity Log")
        events_resp = requests.get(f"{BACKEND_URL}/api/projects/{proj_id}/events", headers=get_headers())
        if events_resp.status_code == 200:
            events = events_resp.json()
            if not events:
                st.info("No activity events logged yet.")
            else:
                for ev in reversed(events):
                    ev_type = ev.get("event_type", "info")
                    st.markdown(
                        f"""<div class='feed-item {ev_type}'>
                            <b>[{ev['stage']}]</b> ({ev['percentage']:.0f}%) — {ev['message']}
                            <br><small style='color: #64748b;'>{ev['timestamp'][:19].replace('T', ' ')}</small>
                        </div>""",
                        unsafe_allow_html=True,
                    )

    with tab_chat:
        st.markdown("#### Chat with Analysis Agents & Inject Context Directives")
        st.caption("Guarded interactions: Ask questions about current analysis progress OR provide directives (e.g. *'focus on payments'*, *'/admin is deprecated'*).")

        # Display Chat History
        chats_resp = requests.get(f"{BACKEND_URL}/api/projects/{proj_id}/chat", headers=get_headers())
        if chats_resp.status_code == 200:
            chats = chats_resp.json()
            for c in chats:
                with st.chat_message(c["role"]):
                    st.write(c["content"])

        # Chat Input
        user_msg = st.chat_input("Ask about progress or provide architecture context...")
        if user_msg:
            with st.chat_message("user"):
                st.write(user_msg)
            with st.spinner("Processing inquiry with guardrails..."):
                resp = requests.post(
                    f"{BACKEND_URL}/api/projects/{proj_id}/chat",
                    json={"message": user_msg},
                    headers=get_headers(),
                )
                if resp.status_code == 200:
                    ans = resp.json()["response"]
                    with st.chat_message("agent"):
                        st.write(ans)
                    st.rerun()
                else:
                    st.error("Error communicating with agent chat.")


# ==========================================
# 4. DOCUMENTATION & REPORTS
# ==========================================
elif selected_view == "📄 Documentation & Reports":
    if not st.session_state.active_project_id:
        st.warning("No active project selected. Select a project in '📂 Projects Dashboard'.")
        st.stop()

    proj_id = st.session_state.active_project_id
    st.markdown(f"## 📄 Multi-Persona Documentation: *{st.session_state.active_project_name or proj_id}*")

    # Export Buttons Row
    col_e1, col_e2, col_sp = st.columns([2, 2, 4])
    with col_e1:
        st.download_button(
            label="📥 Export Markdown (.md)",
            data=requests.get(f"{BACKEND_URL}/api/projects/{proj_id}/export/markdown", headers=get_headers()).content,
            file_name=f"{st.session_state.active_project_name or proj_id}_docs.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_e2:
        st.download_button(
            label="📕 Export PDF (.pdf)",
            data=requests.get(f"{BACKEND_URL}/api/projects/{proj_id}/export/pdf", headers=get_headers()).content,
            file_name=f"{st.session_state.active_project_name or proj_id}_docs.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    tab_sde, tab_pm, tab_diagrams = st.tabs(["💻 SDE Technical Specification", "📊 PM Business Architecture", "📐 Mermaid System Diagrams"])

    with tab_sde:
        sde_res = requests.get(f"{BACKEND_URL}/api/projects/{proj_id}/reports/sde", headers=get_headers())
        if sde_res.status_code == 200:
            st.markdown(sde_res.json()["content_markdown"])
        else:
            st.info("SDE report is not generated yet. Start or complete the analysis pipeline first.")

    with tab_pm:
        pm_res = requests.get(f"{BACKEND_URL}/api/projects/{proj_id}/reports/pm", headers=get_headers())
        if pm_res.status_code == 200:
            st.markdown(pm_res.json()["content_markdown"])
        else:
            st.info("PM report is not generated yet. Start or complete the analysis pipeline first.")

    with tab_diagrams:
        diag_res = requests.get(f"{BACKEND_URL}/api/projects/{proj_id}/reports/diagrams", headers=get_headers())
        if diag_res.status_code == 200:
            diagrams = diag_res.json().get("diagrams_json", [])
            for d in diagrams:
                st.markdown(f"### {d.get('title')} (`{d.get('type')}`)")
                components.html(render_mermaid(d.get("code", "")), height=460, scrolling=True)
                with st.expander("View Raw Mermaid Code"):
                    st.code(d.get("code"), language="mermaid")
                st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)
        else:
            st.info("Mermaid diagrams not generated yet.")


# ==========================================
# 5. CODEBASE RAG Q&A
# ==========================================
elif selected_view == "💬 Codebase RAG Q&A":
    if not st.session_state.active_project_id:
        st.warning("No active project selected. Select a project in '📂 Projects Dashboard'.")
        st.stop()

    proj_id = st.session_state.active_project_id
    st.markdown(f"## 💬 Grounded Codebase RAG Q&A: *{st.session_state.active_project_name or proj_id}*")
    st.caption("Ask questions about architecture, endpoints, or business logic. All answers cite verified code lines and respond in under 3 seconds.")

    col_q1, col_q2 = st.columns([1, 3])
    with col_q1:
        qa_persona = st.selectbox("Answer Persona", ["sde", "pm"], format_func=lambda x: "SDE (Technical)" if x == "sde" else "PM (Business Impact)")

    with st.form("rag_qa_form"):
        user_query = st.text_input("Enter Question", placeholder="e.g. How is user authentication implemented?")
        qa_submit = st.form_submit_button("Search & Answer", use_container_width=True)

        if qa_submit and user_query.strip():
            with st.spinner("Searching indexed code chunks and generating citation-grounded answer..."):
                t0 = time.time()
                resp = requests.post(
                    f"{BACKEND_URL}/api/projects/{proj_id}/qa",
                    json={"question": user_query.strip(), "persona": qa_persona},
                    headers=get_headers(),
                )
                t_total = (time.time() - t0) * 1000

                if resp.status_code == 200:
                    data = resp.json()
                    st.markdown("### Answer")
                    st.markdown(data["answer"])
                    st.caption(f"⚡ Latency: **{data['response_time_ms']:.1f}ms** (UI roundtrip: {t_total:.1f}ms) • Persona: **{data['persona'].upper()}**")

                    if data.get("citations"):
                        st.markdown("#### 🔍 Grounded Code Citations")
                        for i, cit in enumerate(data["citations"]):
                            with st.expander(f"📍 Citation {i+1}: {cit['file_path']} (Lines {cit['start_line']}-{cit['end_line']})"):
                                st.code(cit["snippet"])
                else:
                    st.error("Error executing codebase Q&A.")


# ==========================================
# 6. ADMIN DASHBOARD
# ==========================================
elif selected_view == "🛡️ Admin Dashboard":
    if st.session_state.user_role != "admin":
        st.error("Admin privileges required.")
        st.stop()

    st.markdown("## 🛡️ Administrative & Observability Dashboard")

    # Analytics Metrics Cards
    try:
        analytics_res = requests.get(f"{BACKEND_URL}/api/admin/analytics", headers=get_headers())
        if analytics_res.status_code == 200:
            an = analytics_res.json()
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"<div class='metric-card'><div class='metric-label'>Total Users</div><div class='metric-value'>{an['total_users']}</div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='metric-card'><div class='metric-label'>Total Projects</div><div class='metric-value'>{an['total_projects']}</div></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='metric-card'><div class='metric-label'>Active Analyses</div><div class='metric-value'>{an['active_analyses']}</div></div>", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<div class='metric-card'><div class='metric-label'>Completion Rate</div><div class='metric-value'>{an['completion_rate_percent']:.1f}%</div></div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

    tab_users, tab_projects, tab_traces, tab_errors = st.tabs(["👥 User Management", "📁 All Projects", "🔭 Langfuse Traces", "⚠️ System Errors"])

    with tab_users:
        users_res = requests.get(f"{BACKEND_URL}/api/admin/users", headers=get_headers())
        if users_res.status_code == 200:
            users = users_res.json()
            for u in users:
                col_u1, col_u2, col_u3 = st.columns([3, 2, 2])
                with col_u1:
                    st.write(f"**{u['email']}** (ID: {u['id']})")
                with col_u2:
                    st.caption(f"Role: `{u['role']}` • Projects: {u['project_count']}")
                with col_u3:
                    if u["id"] != 1 and st.button(f"Delete User #{u['id']}", key=f"del_u_{u['id']}"):
                        requests.delete(f"{BACKEND_URL}/api/admin/users/{u['id']}", headers=get_headers())
                        st.success(f"Deleted user #{u['id']}")
                        time.sleep(0.5)
                        st.rerun()

    with tab_projects:
        projs_res = requests.get(f"{BACKEND_URL}/api/admin/projects", headers=get_headers())
        if projs_res.status_code == 200:
            all_projs = projs_res.json()
            for p in all_projs:
                col_p1, col_p2, col_p3 = st.columns([3, 2, 2])
                with col_p1:
                    st.write(f"**{p['name']}** (`{p['detected_stack']}`)")
                with col_p2:
                    st.caption(f"Status: `{p['status']}` • Progress: {p['progress_percentage']:.0f}%")
                with col_p3:
                    if st.button(f"Delete Project", key=f"del_p_{p['id']}"):
                        requests.delete(f"{BACKEND_URL}/api/admin/projects/{p['id']}", headers=get_headers())
                        st.success(f"Deleted project {p['id']}")
                        time.sleep(0.5)
                        st.rerun()

    with tab_traces:
        st.markdown("#### Langfuse Execution Traces")
        traces_res = requests.get(f"{BACKEND_URL}/api/admin/traces", headers=get_headers())
        if traces_res.status_code == 200:
            traces = traces_res.json().get("traces", [])
            if not traces:
                st.info("No LLM execution traces recorded yet.")
            else:
                for tr in traces:
                    with st.expander(f"Trace: {tr['agent_name']} — {tr['tokens']} tokens ({tr['latency_sec']}s, ${tr['cost_usd']:.6f})"):
                        st.json(tr)

    with tab_errors:
        err_res = requests.get(f"{BACKEND_URL}/api/admin/error-logs", headers=get_headers())
        if err_res.status_code == 200:
            errs = err_res.json()
            if not errs:
                st.success("Clean health: Zero unhandled system errors recorded.")
            else:
                for er in errs:
                    st.error(f"[{er['stage']}] {er['message']} ({er['timestamp']})")
