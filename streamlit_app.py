"""
=============================================================================
ClinicCare — Streamlit Dashboard with Gemini AI
=============================================================================

A self-contained Streamlit web application that:
1. Connects to the ClinicCare backend REST API
2. Shows appointment management dashboards
3. Uses the ML service for no-show risk predictions
4. Uses Google Gemini AI for:
   - Patient no-show risk explanation (why is this patient at risk?)
   - Smart appointment summary generation
   - AI health advice chatbot for patients

DEPLOYMENT:
  Local:       streamlit run streamlit_app.py
  Cloud:       Deploy to Streamlit Community Cloud (share.streamlit.io)
               Set GEMINI_API_KEY and BACKEND_URL in Streamlit Secrets

ENVIRONMENT VARIABLES / STREAMLIT SECRETS:
  GEMINI_API_KEY  — your Google AI Studio API key
  BACKEND_URL     — backend API URL (default: http://localhost:4000)
  ML_URL          — ML service URL   (default: http://localhost:5001)
=============================================================================
"""

import os
import json
import requests
import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Streamlit Cloud secrets or environment variables
BACKEND_URL   = st.secrets.get("BACKEND_URL",   os.getenv("BACKEND_URL",   "http://localhost:4000"))
ML_URL        = st.secrets.get("ML_URL",        os.getenv("ML_URL",        "http://localhost:5001"))
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

st.set_page_config(
    page_title="ClinicCare — Healthcare Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .risk-high   { color:#dc2626; font-weight:700; }
    .risk-medium { color:#d97706; font-weight:700; }
    .risk-low    { color:#16a34a; font-weight:700; }
    .metric-card { background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:16px; text-align:center; }
    .stAlert { border-radius: 8px; }
    div[data-testid="stSidebarNav"] { display:none; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# API helpers
# ─────────────────────────────────────────────────────────────────────────────

def api_get(path, token=None, params=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = requests.get(f"{BACKEND_URL}{path}", headers=headers, params=params, timeout=10)
        if r.ok:
            return r.json(), None
        return None, r.json().get("error", f"HTTP {r.status_code}")
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend. Make sure the backend is running on " + BACKEND_URL
    except Exception as e:
        return None, str(e)

def api_post(path, body, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=body, headers=headers, timeout=10)
        if r.ok:
            return r.json(), None
        return None, r.json().get("error", f"HTTP {r.status_code}")
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend."
    except Exception as e:
        return None, str(e)

def api_patch(path, body, token):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    try:
        r = requests.patch(f"{BACKEND_URL}{path}", json=body, headers=headers, timeout=10)
        if r.ok:
            return r.json(), None
        return None, r.json().get("error", f"HTTP {r.status_code}")
    except Exception as e:
        return None, str(e)

def ml_predict(payload):
    try:
        r = requests.post(f"{ML_URL}/predict", json=payload, timeout=5)
        return r.json() if r.ok else None
    except:
        return None

# ─────────────────────────────────────────────────────────────────────────────
# Gemini AI helper
# ─────────────────────────────────────────────────────────────────────────────

def gemini_generate(prompt: str, system: str = "") -> str:
    """Call Google Gemini API and return the text response."""
    key = GEMINI_API_KEY
    if not key:
        return "⚠️ Gemini API key not configured. Add GEMINI_API_KEY to your environment or Streamlit secrets."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    body = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
        "safetySettings": [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    }
    try:
        r = requests.post(url, json=body, timeout=20)
        if r.ok:
            candidates = r.json().get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"]
            return "No response from Gemini."
        err = r.json().get("error", {})
        return f"Gemini error: {err.get('message', r.text[:200])}"
    except requests.exceptions.Timeout:
        return "Gemini request timed out."
    except Exception as e:
        return f"Gemini error: {e}"

# ─────────────────────────────────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────────────────────────────────

if "token" not in st.session_state:
    st.session_state.token   = None
    st.session_state.user    = None
    st.session_state.profile = None

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — auth + navigation
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🏥 ClinicCare")
    st.caption("Healthcare Appointment System")
    st.divider()

    if not st.session_state.token:
        # Login form
        st.subheader("Sign In")
        email    = st.text_input("Email",    value="admin@clinic.com",  key="login_email")
        password = st.text_input("Password", value="Admin@123", type="password", key="login_pass")

        if st.button("Sign In", use_container_width=True, type="primary"):
            data, err = api_post("/api/auth/login", {"email": email, "password": password})
            if err:
                st.error(err)
            else:
                st.session_state.token   = data["token"]
                st.session_state.user    = data["user"]
                st.session_state.profile = data.get("profile")
                st.rerun()

        st.divider()
        st.caption("Demo accounts:")
        st.code("admin@clinic.com / Admin@123\ndr.adams@clinic.com / Doctor@123\nalice@example.com / Patient@123", language=None)

    else:
        u = st.session_state.user
        st.success(f"Signed in as\n**{u['name']}**\n_{u['role'].title()}_")
        if st.button("Sign Out", use_container_width=True):
            for k in ["token", "user", "profile"]:
                st.session_state[k] = None
            st.rerun()

        st.divider()

        # Navigation
        role = u["role"]
        if role == "admin":
            pages = ["Dashboard", "Appointments", "Patients", "Doctors", "Reminders", "Reports", "AI Assistant"]
        elif role == "doctor":
            pages = ["My Schedule", "Risk Analysis", "AI Assistant"]
        else:
            pages = ["My Dashboard", "Book Appointment", "My Appointments", "AI Assistant"]

        page = st.radio("Navigate", pages, key="nav_page")

    st.divider()
    st.caption(f"Backend: `{BACKEND_URL}`")
    if GEMINI_API_KEY:
        st.caption("🤖 Gemini AI: Connected")
    else:
        st.caption("⚠️ Gemini AI: No API key")

# ─────────────────────────────────────────────────────────────────────────────
# Not logged in
# ─────────────────────────────────────────────────────────────────────────────

if not st.session_state.token:
    st.title("Welcome to ClinicCare 🏥")
    st.info("Please sign in using the sidebar to access the application.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 👤 Patients")
        st.write("Book and manage appointments, view no-show risk and reminders.")
    with col2:
        st.markdown("### 👨‍⚕️ Doctors")
        st.write("View your schedule, patient risk levels, and appointment notes.")
    with col3:
        st.markdown("### ⚙️ Admins")
        st.write("Full dashboard, analytics, reports, and AI-powered insights.")

    st.caption("⚠️ No-show predictions are academic/demo only. Not medically validated.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# Helper UI components
# ─────────────────────────────────────────────────────────────────────────────

def risk_badge(risk, level):
    if risk is None:
        return "N/A"
    pct = round(risk * 100)
    cls = {"high": "risk-high", "medium": "risk-medium", "low": "risk-low"}.get(level, "")
    label = {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"}.get(level, level or "")
    return f'<span class="{cls}">{label} {pct}%</span>'

def status_color(s):
    return {"upcoming":"🔵","completed":"🟢","cancelled":"⚫","no-show":"🔴"}.get(s,"⚪") + f" {s}"

# ─────────────────────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────────────────────

token = st.session_state.token
user  = st.session_state.user
role  = user["role"]

# ══════════════════════════════════════════════════════
# ADMIN — Dashboard
# ══════════════════════════════════════════════════════
if role == "admin" and page == "Dashboard":
    st.title("Admin Dashboard")

    stats, err = api_get("/api/appointments/stats", token)
    if err:
        st.error(err)
        st.stop()

    # KPI row 1
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Total Appointments", stats["total"])
    c2.metric("Today",     stats["todayC"])
    c3.metric("Upcoming",  stats["upcoming"])
    c4.metric("Completed", stats["completed"])
    c5.metric("No-shows",  stats["noShows"], delta=f"-{stats['noShowRate']}% rate", delta_color="inverse")
    c6.metric("Cancelled", stats["cancelled"])

    st.divider()

    # KPI row 2 — risk
    r1,r2,r3 = st.columns(3)
    r1.metric("🔴 High Risk",   stats["highRisk"],  help="Upcoming appointments with high no-show risk")
    r2.metric("🟡 Medium Risk", stats["medRisk"])
    r3.metric("🟢 Low Risk",    stats["lowRisk"])

    st.divider()

    # Charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📅 Appointments — Last 30 Days")
        if stats["weekly"]:
            df_w = pd.DataFrame(stats["weekly"])
            df_w["date"] = pd.to_datetime(df_w["date"])
            df_w = df_w.set_index("date")
            st.bar_chart(df_w["count"])
        else:
            st.info("No appointment data for the last 30 days.")

    with col_right:
        st.subheader("🏥 Appointments by Department")
        if stats["byDept"]:
            df_d = pd.DataFrame(stats["byDept"])
            st.bar_chart(df_d.set_index("department")["count"])
        else:
            st.info("No department data.")

    st.subheader("👨‍⚕️ Appointment Load by Doctor")
    if stats["byDoctor"]:
        df_doc = pd.DataFrame(stats["byDoctor"])
        st.dataframe(df_doc[["doctor_name","department","appointment_count","no_shows"]].rename(
            columns={"doctor_name":"Doctor","department":"Department","appointment_count":"Total","no_shows":"No-shows"}
        ), use_container_width=True, hide_index=True)

    # AI Summary
    st.divider()
    st.subheader("🤖 AI Dashboard Summary")
    if st.button("Generate AI Summary with Gemini", type="primary"):
        with st.spinner("Asking Gemini..."):
            prompt = f"""
You are a healthcare analytics assistant. Summarise the following clinic appointment statistics
in 3-4 concise bullet points for a clinic manager. Highlight anything that needs attention.

Statistics:
- Total appointments: {stats['total']}
- Today: {stats['todayC']}
- Upcoming: {stats['upcoming']}
- Completed: {stats['completed']}
- No-shows: {stats['noShows']} ({stats['noShowRate']}% rate)
- Cancelled: {stats['cancelled']} ({stats['cancellationRate']}% rate)
- High no-show risk appointments: {stats['highRisk']}
- Medium risk: {stats['medRisk']}, Low risk: {stats['lowRisk']}
- Appointments by department: {json.dumps(stats.get('byDept', []))}

Be concise, professional, and actionable.
"""
            reply = gemini_generate(prompt, system="You are a concise healthcare analytics assistant.")
            st.markdown(reply)


# ══════════════════════════════════════════════════════
# ADMIN — Appointments
# ══════════════════════════════════════════════════════
elif role == "admin" and page == "Appointments":
    st.title("Appointments Management")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        status_filter = st.selectbox("Status", ["all","upcoming","completed","no-show","cancelled"])
    with col_f2:
        date_filter = st.date_input("Date", value=None, key="appt_date_filter")
    with col_f3:
        search = st.text_input("Search patient/doctor")

    params = {}
    if status_filter != "all": params["status"] = status_filter
    if date_filter: params["date"] = str(date_filter)

    appts, err = api_get("/api/appointments", token, params)
    if err:
        st.error(err)
    else:
        if search:
            appts = [a for a in appts if
                     search.lower() in (a.get("patient_name","") or "").lower() or
                     search.lower() in (a.get("doctor_name","") or "").lower() or
                     search.lower() in (a.get("medical_id","") or "").lower()]

        st.caption(f"{len(appts)} appointment(s)")

        for a in appts[:50]:
            with st.expander(f"{status_color(a['status'])}  {a['appointment_date']} {a['appointment_time']}  |  {a.get('patient_name','?')}  →  {a.get('doctor_name','?')}"):
                col1, col2, col3 = st.columns(3)
                col1.write(f"**Patient:** {a.get('patient_name')}\n\n**Medical ID:** {a.get('medical_id')}")
                col2.write(f"**Doctor:** {a.get('doctor_name')}\n\n**Dept:** {a.get('department_name')}")
                risk_html = risk_badge(a.get("noshow_risk"), a.get("risk_level"))
                col3.markdown(f"**Risk:** {risk_html}", unsafe_allow_html=True)
                if a.get("reason"): st.write(f"**Reason:** {a['reason']}")

                if a["status"] == "upcoming":
                    c1, c2, c3 = st.columns(3)
                    if c1.button("Mark Complete", key=f"comp_{a['id']}"):
                        _, e = api_patch(f"/api/appointments/{a['id']}", {"status":"completed"}, token)
                        if e: st.error(e)
                        else: st.success("Marked completed"); st.rerun()
                    if c2.button("Mark No-show", key=f"ns_{a['id']}"):
                        _, e = api_patch(f"/api/appointments/{a['id']}", {"status":"no-show"}, token)
                        if e: st.error(e)
                        else: st.rerun()

                    # AI risk explanation
                    if a.get("noshow_risk") is not None and st.button("🤖 Explain Risk with Gemini", key=f"ai_{a['id']}"):
                        with st.spinner("Asking Gemini..."):
                            prompt = f"""
A patient has an upcoming medical appointment with a no-show risk score of {a['noshow_risk']:.0%} ({a.get('risk_level','').upper()} RISK).

Context:
- Patient: {a.get('patient_name')}
- Doctor: {a.get('doctor_name')} ({a.get('department_name')})
- Date: {a['appointment_date']} at {a['appointment_time']}
- Reason for visit: {a.get('reason','Not specified')}

In 2-3 sentences, explain in plain language:
1. What this risk score means
2. What the clinic could do to reduce this patient's no-show risk

Do NOT give medical advice. Focus on appointment management only.
"""
                            reply = gemini_generate(prompt)
                            st.info(reply)


# ══════════════════════════════════════════════════════
# ADMIN — Patients
# ══════════════════════════════════════════════════════
elif role == "admin" and page == "Patients":
    st.title("Patient Registry")
    patients, err = api_get("/api/patients", token)
    if err:
        st.error(err)
    else:
        search = st.text_input("Search by name, email, or medical ID")
        if search:
            patients = [p for p in patients if
                        search.lower() in (p.get("name","") or "").lower() or
                        search.lower() in (p.get("email","") or "").lower() or
                        search in (p.get("medical_id","") or "")]

        df = pd.DataFrame([{
            "Name": p.get("name"), "Medical ID": p.get("medical_id"),
            "Email": p.get("email"), "Age": p.get("age"), "Gender": p.get("gender"),
            "Total Appts": p.get("total_appointments",0),
            "No-shows": p.get("no_shows",0),
            "No-show %": f"{round(p.get('no_shows',0)/max(p.get('total_appointments',1),1)*100)}%"
        } for p in patients])
        st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════
# ADMIN — Doctors
# ══════════════════════════════════════════════════════
elif role == "admin" and page == "Doctors":
    st.title("Doctors & Departments")
    docs, err = api_get("/api/doctors", token)
    if err:
        st.error(err)
    else:
        for doc in docs:
            with st.expander(f"👨‍⚕️  {doc.get('name')}  —  {doc.get('department_name')}"):
                c1, c2 = st.columns(2)
                c1.write(f"**Specialization:** {doc.get('specialization')}\n\n**Qualification:** {doc.get('qualification')}")
                c2.write(f"**Email:** {doc.get('email')}\n\n**Available:** {doc.get('available_days')}")
                if doc.get("bio"): st.caption(doc["bio"])


# ══════════════════════════════════════════════════════
# ADMIN — Reminders (Agentic Workflow)
# ══════════════════════════════════════════════════════
elif role == "admin" and page == "Reminders":
    st.title("Appointment Reminders")
    st.info("🤖 **Agentic AI Workflow** — Click the button to run the automated reminder pipeline: fetch upcoming appointments → check risk → simulate SMS/email → record result.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Run Reminder Workflow", type="primary", use_container_width=True):
            with st.spinner("Processing reminders..."):
                result, err = api_post("/api/notifications/trigger", {}, token)
            if err:
                st.error(err)
            else:
                st.success(f"✅ Processed: {result['processed']} | Sent: {result['sent']} | Failed: {result['failed']}")
                st.rerun()

    # Stats
    stats, _ = api_get("/api/notifications/stats", token)
    if stats:
        with col2:
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total",     stats["total"])
            c2.metric("Scheduled", stats["scheduled"])
            c3.metric("Sent",      stats["sent"])
            c4.metric("Failed",    stats["failed"])

    notifs, err = api_get("/api/notifications", token)
    if err:
        st.error(err)
    elif notifs:
        df = pd.DataFrame([{
            "Type":      n["type"].upper(),
            "Patient":   n.get("patient_name"),
            "Date":      n.get("appointment_date"),
            "Time":      n.get("appointment_time"),
            "Doctor":    n.get("doctor_name"),
            "Status":    n["status"],
            "Sent At":   n.get("sent_at","—") or "—",
            "Message":   (n.get("message","") or "")[:60] + "...",
        } for n in notifs])
        st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════
# ADMIN — Reports
# ══════════════════════════════════════════════════════
elif role == "admin" and page == "Reports":
    st.title("Reports & Analytics")

    tab1, tab2, tab3 = st.tabs(["Appointment Report", "No-show Analysis", "Trends"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1: from_date = st.date_input("From", value=None, key="rpt_from")
        with c2: to_date   = st.date_input("To",   value=None, key="rpt_to")
        with c3: status_rpt = st.selectbox("Status", ["","upcoming","completed","no-show","cancelled"], key="rpt_status")

        if st.button("Generate Report", type="primary"):
            params = {}
            if from_date: params["from"] = str(from_date)
            if to_date:   params["to"]   = str(to_date)
            if status_rpt: params["status"] = status_rpt
            rpt, err = api_get("/api/reports/appointments", token, params)
            if err:
                st.error(err)
            else:
                st.metric("Total", rpt["total"])
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**By Status**")
                    df_s = pd.DataFrame(list(rpt["byStatus"].items()), columns=["Status","Count"])
                    st.bar_chart(df_s.set_index("Status"))
                with col2:
                    st.write("**By Doctor**")
                    df_d = pd.DataFrame(list(rpt["byDoctor"].items()), columns=["Doctor","Count"])
                    st.bar_chart(df_d.set_index("Doctor"))

                if rpt["rows"]:
                    df_rows = pd.DataFrame([{
                        "Date": r["appointment_date"], "Patient": r.get("patient_name"),
                        "Doctor": r.get("doctor_name"), "Department": r.get("department"),
                        "Status": r["status"], "Risk": r.get("risk_level","N/A"),
                    } for r in rpt["rows"][:100]])
                    st.dataframe(df_rows, use_container_width=True, hide_index=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1: from2 = st.date_input("From", value=None, key="ns_from")
        with c2: to2   = st.date_input("To",   value=None, key="ns_to")
        if st.button("Analyse No-shows"):
            params2 = {}
            if from2: params2["from"] = str(from2)
            if to2:   params2["to"]   = str(to2)
            ns, err = api_get("/api/reports/no-show", token, params2)
            if err:
                st.error(err)
            else:
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Total",         ns["total"])
                c2.metric("No-shows",      ns["noShows"])
                c3.metric("No-show Rate",  f"{ns['noShowRate']}%")
                c4.metric("Cancel Rate",   f"{ns['cancellationRate']}%")
                if ns.get("byDayOfWeek"):
                    days = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
                    df_dow = pd.DataFrame([{"Day":days[int(d["dow"])],"Total":d["total"],"No-shows":d["no_shows"]} for d in ns["byDayOfWeek"]])
                    st.bar_chart(df_dow.set_index("Day"))
                if ns.get("topNoShow"):
                    st.write("**Top No-show Patients**")
                    st.dataframe(pd.DataFrame(ns["topNoShow"]), use_container_width=True, hide_index=True)

    with tab3:
        trends, err = api_get("/api/reports/trends", token)
        if err:
            st.error(err)
        elif trends:
            if trends.get("monthly"):
                df_m = pd.DataFrame(trends["monthly"])
                df_m = df_m.set_index("month")
                st.subheader("Monthly Trends")
                st.line_chart(df_m[["total","completed","no_shows","cancelled"]])


# ══════════════════════════════════════════════════════
# DOCTOR — My Schedule
# ══════════════════════════════════════════════════════
elif role == "doctor" and page == "My Schedule":
    st.title(f"My Schedule — {user['name']}")

    col1, col2 = st.columns(2)
    with col1: date_f = st.date_input("Filter by date", value=None)
    with col2: status_f = st.selectbox("Status", ["all","upcoming","completed","no-show","cancelled"])

    params = {}
    if date_f: params["date"] = str(date_f)
    if status_f != "all": params["status"] = status_f

    appts, err = api_get("/api/appointments", token, params)
    if err:
        st.error(err)
    else:
        today_str = str(date.today())
        today_appts = [a for a in appts if a["appointment_date"] == today_str]
        upcoming    = [a for a in appts if a["status"] == "upcoming"]
        high_risk   = [a for a in upcoming if a.get("risk_level") == "high"]

        c1,c2,c3 = st.columns(3)
        c1.metric("Today's Appointments", len(today_appts))
        c2.metric("Total Upcoming", len(upcoming))
        c3.metric("⚠️ High Risk", len(high_risk))

        if high_risk:
            st.warning(f"⚠️ {len(high_risk)} high-risk appointment(s) — consider sending extra reminders.")

        for a in appts[:40]:
            with st.expander(f"{status_color(a['status'])}  {a['appointment_date']} {a['appointment_time']}  |  {a.get('patient_name')}"):
                col1, col2 = st.columns(2)
                col1.write(f"**Patient:** {a.get('patient_name')}\n\n**Medical ID:** {a.get('medical_id')}\n\n**Age/Gender:** {a.get('age')}/{a.get('gender')}")
                risk_html = risk_badge(a.get("noshow_risk"), a.get("risk_level"))
                col2.markdown(f"**No-show Risk:** {risk_html}", unsafe_allow_html=True)
                if a.get("reason"): st.write(f"**Reason:** {a['reason']}")

                if a["status"] == "upcoming":
                    bc1, bc2 = st.columns(2)
                    if bc1.button("Mark Complete", key=f"doc_comp_{a['id']}"):
                        _, e = api_patch(f"/api/appointments/{a['id']}", {"status":"completed"}, token)
                        if e: st.error(e)
                        else: st.rerun()
                    if bc2.button("Mark No-show", key=f"doc_ns_{a['id']}"):
                        _, e = api_patch(f"/api/appointments/{a['id']}", {"status":"no-show"}, token)
                        if e: st.error(e)
                        else: st.rerun()


# ══════════════════════════════════════════════════════
# DOCTOR — Risk Analysis
# ══════════════════════════════════════════════════════
elif role == "doctor" and page == "Risk Analysis":
    st.title("Patient Risk Analysis")
    st.write("Run an on-demand no-show risk prediction for any patient.")

    with st.form("risk_form"):
        c1, c2 = st.columns(2)
        age        = c1.number_input("Age", 1, 100, 45)
        gender     = c2.selectbox("Gender", ["female","male","unknown"])
        specialty  = c1.selectbox("Specialty", ["General Practice","Cardiology","Dermatology","Orthopedics","Neurology","Pediatrics","Oncology","Psychiatry"])
        appt_hour  = c2.slider("Appointment Hour", 8, 17, 10)
        dow        = c1.selectbox("Day of Week", [("Monday",1),("Tuesday",2),("Wednesday",3),("Thursday",4),("Friday",5),("Saturday",6),("Sunday",0)], format_func=lambda x: x[0])
        total_appts = c1.number_input("Total Past Appointments", 0, 50, 5)
        prev_ns    = c2.number_input("Previous No-shows", 0, 20, 1)
        prev_cancel = c1.number_input("Previous Cancellations", 0, 20, 0)
        submitted = st.form_submit_button("Predict Risk", type="primary")

    if submitted:
        payload = {
            "age": age, "gender": gender, "specialty": specialty,
            "appointment_hour": appt_hour, "day_of_week": dow[1],
            "total_appointments": total_appts,
            "previous_no_shows": prev_ns, "previous_cancellations": prev_cancel,
        }
        result = ml_predict(payload)
        if result:
            risk_pct = round(result["noshow_risk"] * 100)
            col1, col2 = st.columns(2)
            col1.metric("No-show Risk Score", f"{risk_pct}%")
            col2.metric("Risk Level", result["risk_label"])
            st.progress(result["noshow_risk"], text=f"{risk_pct}% risk")

            if result["risk_level"] == "high":
                st.error("HIGH RISK — Recommend sending an additional reminder or calling the patient.")
            elif result["risk_level"] == "medium":
                st.warning("MEDIUM RISK — A standard 24h reminder is recommended.")
            else:
                st.success("LOW RISK — Patient is likely to attend.")

            # AI explanation
            if st.button("🤖 Explain with Gemini"):
                with st.spinner("Asking Gemini..."):
                    prompt = f"""
A patient risk profile has been assessed. Explain this in simple, non-clinical terms.

Risk score: {risk_pct}% ({result['risk_label']})
Features: age={age}, gender={gender}, specialty={specialty}, appointment hour={appt_hour}:00,
previous no-shows={prev_ns} out of {total_appts} appointments ({round(prev_ns/max(total_appts,1)*100)}% rate),
previous cancellations={prev_cancel}.

In 2-3 short sentences, explain:
1. What this score means
2. Which factor(s) most likely contributed to this risk
3. One concrete action the clinic can take

Do NOT give medical advice. Be brief and actionable.
"""
                    st.info(gemini_generate(prompt))
        else:
            st.error("ML service unavailable. Make sure the ML service is running on " + ML_URL)


# ══════════════════════════════════════════════════════
# PATIENT — My Dashboard
# ══════════════════════════════════════════════════════
elif role == "patient" and page == "My Dashboard":
    st.title(f"Welcome, {user['name'].split()[0]}! 👋")

    profile = st.session_state.profile
    if profile:
        st.caption(f"Medical ID: `{profile.get('medical_id')}`")

    appts, err = api_get("/api/appointments", token)
    if err:
        st.error(err)
    else:
        upcoming  = [a for a in appts if a["status"] == "upcoming"]
        completed = [a for a in appts if a["status"] == "completed"]
        no_shows  = [a for a in appts if a["status"] == "no-show"]

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Upcoming",  len(upcoming))
        c2.metric("Completed", len(completed))
        c3.metric("No-shows",  len(no_shows))
        c4.metric("Total",     len(appts))

        if upcoming:
            st.subheader("Upcoming Appointments")
            for a in upcoming[:3]:
                risk_html = risk_badge(a.get("noshow_risk"), a.get("risk_level"))
                with st.container(border=True):
                    col1, col2 = st.columns([3,1])
                    col1.write(f"**{a.get('doctor_name')}** — {a.get('department_name')}\n\n📅 {a['appointment_date']} @ {a['appointment_time']}")
                    col2.markdown(f"**Risk:** {risk_html}", unsafe_allow_html=True)
                    if a.get("noshow_risk", 0) >= 0.7:
                        st.warning("⚠️ High no-show risk. Please attend or cancel in advance.")


# ══════════════════════════════════════════════════════
# PATIENT — Book Appointment
# ══════════════════════════════════════════════════════
elif role == "patient" and page == "Book Appointment":
    st.title("Book an Appointment")

    # Step 1: Select doctor
    docs, err = api_get("/api/doctors")
    if err:
        st.error(err)
        st.stop()

    depts, _ = api_get("/api/departments")
    dept_names = ["All Departments"] + [d["name"] for d in (depts or [])]
    dept_sel = st.selectbox("Filter by Department", dept_names)

    filtered_docs = docs if dept_sel == "All Departments" else [d for d in docs if d.get("department_name") == dept_sel]
    doc_options = {f"{d['name']} — {d['specialization']} ({d['department_name']})": d["id"] for d in filtered_docs}

    if not doc_options:
        st.info("No doctors found.")
        st.stop()

    selected_label = st.selectbox("Select Doctor", list(doc_options.keys()))
    selected_doc_id = doc_options[selected_label]

    # Step 2: Available slots
    slots, serr = api_get(f"/api/doctors/{selected_doc_id}/slots")
    if serr or not slots:
        st.warning("No available slots for this doctor.")
        st.stop()

    slot_options = {f"{s['slot_date']}  {s['slot_time']}": s for s in slots[:30]}
    slot_label = st.selectbox("Select Slot", list(slot_options.keys()))
    chosen_slot = slot_options[slot_label]
    reason = st.text_area("Reason for Visit (optional)", height=80)

    if st.button("Book Appointment", type="primary"):
        body = {
            "doctor_id": selected_doc_id,
            "slot_id": chosen_slot["id"],
            "appointment_date": chosen_slot["slot_date"],
            "appointment_time": chosen_slot["slot_time"],
            "reason": reason or None,
        }
        result, err = api_post("/api/appointments", body, token)
        if err:
            st.error(err)
        else:
            st.success("✅ Appointment booked successfully!")
            risk = result.get("noshow_risk")
            level = result.get("risk_level")
            if risk is not None:
                pct = round(risk * 100)
                st.metric("No-show Risk", f"{pct}%", help="ML-predicted risk score")
                if level == "high":
                    st.warning("⚠️ High no-show risk detected. A reminder will be sent 24h before your appointment.")
            st.info("📬 SMS and email reminders have been scheduled.")


# ══════════════════════════════════════════════════════
# PATIENT — My Appointments
# ══════════════════════════════════════════════════════
elif role == "patient" and page == "My Appointments":
    st.title("My Appointments")

    tab_labels = ["All", "Upcoming", "Completed", "Cancelled", "No-show"]
    tab_map = {"All": None, "Upcoming": "upcoming", "Completed": "completed", "Cancelled": "cancelled", "No-show": "no-show"}
    tabs = st.tabs(tab_labels)

    appts, err = api_get("/api/appointments", token)
    if err:
        st.error(err)
    else:
        for tab, label in zip(tabs, tab_labels):
            with tab:
                filtered = appts if tab_map[label] is None else [a for a in appts if a["status"] == tab_map[label]]
                if not filtered:
                    st.info("No appointments.")
                for a in filtered:
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3,2,1])
                        col1.write(f"**{a.get('doctor_name')}**\n\n{a.get('department_name')}")
                        col2.write(f"📅 {a['appointment_date']} @ {a['appointment_time']}\n\n{a.get('reason','') or ''}")
                        risk_html = risk_badge(a.get("noshow_risk"), a.get("risk_level"))
                        col3.markdown(f"{status_color(a['status'])}<br>{risk_html}", unsafe_allow_html=True)

                        if a["status"] == "upcoming":
                            if st.button("Cancel", key=f"pat_cancel_{a['id']}_{label}"):
                                _, e = api_patch(f"/api/appointments/{a['id']}", {"status":"cancelled"}, token)
                                if e: st.error(e)
                                else: st.rerun()


# ══════════════════════════════════════════════════════
# AI ASSISTANT — All roles
# ══════════════════════════════════════════════════════
elif page == "AI Assistant":
    st.title("🤖 AI Health Assistant (Gemini)")
    st.caption("Powered by Google Gemini AI — For appointment management guidance only. Not medical advice.")

    if not GEMINI_API_KEY:
        st.error("Gemini API key not configured. Add `GEMINI_API_KEY` to your environment or Streamlit secrets.")
        st.code("""
# In .streamlit/secrets.toml:
GEMINI_API_KEY = "your-key-here"
BACKEND_URL = "http://localhost:4000"

# Or set as environment variable:
# export GEMINI_API_KEY=your-key-here
        """, language="toml")
        st.stop()

    system_prompt = {
        "admin":   "You are a helpful clinic management assistant. Help with appointment scheduling, no-show reduction strategies, clinic operations, and patient management. Never give medical advice.",
        "doctor":  "You are a scheduling and patient management assistant for a doctor. Help with appointment planning, understanding no-show patterns, and patient communication. Never give medical diagnoses.",
        "patient": "You are a friendly healthcare appointment assistant. Help patients understand their appointment details, explain no-show risk scores in simple terms, and answer questions about booking. Never give medical advice.",
    }.get(role, "You are a healthcare assistant.")

    # Conversation history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display conversation
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Context injection
    context = ""
    if role == "admin":
        stats, _ = api_get("/api/appointments/stats", token)
        if stats:
            context = f"\n\nCurrent clinic stats: total={stats['total']}, upcoming={stats['upcoming']}, no-shows={stats['noShows']} ({stats['noShowRate']}% rate), high-risk={stats['highRisk']}."
    elif role in ("patient", "doctor"):
        appts, _ = api_get("/api/appointments", token)
        if appts:
            n_upcoming = sum(1 for a in appts if a["status"] == "upcoming")
            context = f"\n\nUser has {n_upcoming} upcoming appointment(s) out of {len(appts)} total."

    # Chat input
    if prompt := st.chat_input("Ask anything about your appointments..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Gemini is thinking..."):
                full_prompt = f"{context}\n\nUser question: {prompt}" if context else prompt
                response = gemini_generate(full_prompt, system=system_prompt)
                st.write(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})

    if st.session_state.chat_history:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
