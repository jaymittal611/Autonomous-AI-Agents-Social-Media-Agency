import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from Simulator import EngagementSimulator
from mock_db import init_db, DB_FILE
from Schema import StrategyPlan, CampaignDrafts, PostDraft
from agents import (
    strategy_agent,
    content_and_creative_agent,
    compliance_agent,
    community_agent,
    analytics_agent
)
from agent_tracer import tracer

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Social Media Agency | Multi-Agent System",
    page_icon="🤖",
    layout="wide"
)

# Initialize database and platform simulator
init_db()
simulator = EngagementSimulator()

def query_dataframe(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Helper to fetch data from SQLite into Pandas."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

# --- Session State Management ---
if "stage" not in st.session_state:
    st.session_state.stage = "input"  # input -> review -> published -> week2
if "strategy" not in st.session_state:
    st.session_state.strategy = None
if "draft_posts" not in st.session_state:
    st.session_state.draft_posts = []
if "compliance_logs" not in st.session_state:
    st.session_state.compliance_logs = []
if "week1_ids" not in st.session_state:
    st.session_state.week1_ids = []
if "week2_ids" not in st.session_state:
    st.session_state.week2_ids = []
if "analysis" not in st.session_state:
    st.session_state.analysis = None

# --- UI Header ---
st.title("🤖 Autonomous AI Social Media Agency")
st.caption("Locally deployed multi-agent marketing collective running on Ollama")
st.markdown("---")

# --- SIDEBAR: Campaign Controls ---
with st.sidebar:
    st.header("📋 Human Campaign Brief")
    default_brief = (
        "We are launching a budget espresso machine for college students. "
        "Run an awareness campaign across our channels targeting price-sensitive 18-25 year olds. "
        "Tone: Playful, relatable, do not over-promise."
    )
    user_brief = st.text_area("Client Brief", value=default_brief, height=140)

    if st.button("🚀 Run Campaign Planning", type="primary", use_container_width=True):
        with st.spinner("Agents coordinating: Strategy ➔ Content & Creative ➔ Compliance Loop..."):
            # 1. Strategy Agent
            strategy = strategy_agent(user_brief)
            st.session_state.strategy = strategy

            # 2. Content & Creative Loop with Compliance Agent
            approved_posts = []
            logs = []
            channels = getattr(strategy, "channel_mix", ["Static_image", "Short_video", "Blog_post"])

            for ch in channels:
                feedback = ""
                active_draft = None
                for cycle in range(1, 4):
                    draft_pkg = content_and_creative_agent(user_brief, strategy, feedback)
                    cand = next((p for p in draft_pkg.posts if p.channel_id == ch), draft_pkg.posts[0])
                    cand.channel_id = ch
                    active_draft = cand

                    review = compliance_agent(active_draft.content, ch)
                    is_ok = getattr(review, "approved", False) or getattr(review, "passed", False)
                    fb_text = getattr(review, "feedback", "") or getattr(review, "critique", "")
                    
                    logs.append(f"[{ch}] Cycle {cycle}: {'✅ Approved' if is_ok else '❌ Rejected'} - {fb_text}")

                    if is_ok:
                        break
                    feedback += f"Cycle {cycle} rejection: {fb_text}\n"

                approved_posts.append(active_draft)

            st.session_state.draft_posts = approved_posts
            st.session_state.compliance_logs = logs
            st.session_state.stage = "review"
            st.rerun()

    if st.button("🔄 Reset Platform Database", use_container_width=True):
        st.session_state.clear()
        tracer.clear()
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM comments")
        c.execute("DELETE FROM post_metrics")
        c.execute("DELETE FROM posts")
        conn.commit()
        conn.close()
        st.rerun()

# --- MAIN WORKFLOW DISPLAY ---
tab_workflow, tab_telemetry, tab_trace = st.tabs([
    "🎯 Campaign Lifecycle", 
    "📈 Platform Telemetry", 
    "📡 Inter-Agent Conversation Trace"
])

# =====================================================================
# TAB 1: CAMPAIGN LIFECYCLE & HUMAN GATE
# =====================================================================
with tab_workflow:
    if st.session_state.stage == "input":
        st.info("Enter or refine the human client brief in the sidebar and click **'Run Campaign Planning'** to trigger the agency.")

    # 1. REVIEW & APPROVAL STAGE
    if st.session_state.stage == "review":
        st.subheader("1. Strategic Architecture & Compliance Loop")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f"**Target Audience:** {getattr(st.session_state.strategy, 'target_audience', 'N/A')}")
            st.markdown(f"**Themes / Pillars:** {', '.join(getattr(st.session_state.strategy, 'key_themes', []))}")
            st.markdown(f"**Selected Channels:** {', '.join(getattr(st.session_state.strategy, 'channel_mix', []))}")
        with c2:
            st.markdown("**Compliance Loop Audit Trail:**")
            for l in st.session_state.compliance_logs:
                st.code(l, language="markdown")

        st.subheader("2. Human-in-the-Loop Review Gate")
        st.write("Review content drafts generated by the Content & Creative Agent before scheduling:")
        
        post_cols = st.columns(len(st.session_state.draft_posts))
        for idx, post in enumerate(st.session_state.draft_posts):
            with post_cols[idx]:
                st.info(f"**Channel:** `{post.channel_id}` (Slot: {post.scheduled_hour}:00)")
                st.caption(f"Creative Brief: {post.creative_brief}")
                st.text_area(f"Copy #{idx+1}", value=post.content, height=180, disabled=True)

        b1, b2, _ = st.columns([1.2, 1, 3])
        with b1:
            if st.button("✅ Authorize & Publish Campaign", type="primary"):
                with st.spinner("Publishing Campaign & responding to audience comments..."):
                    conn = sqlite3.connect(DB_FILE)
                    cur = conn.cursor()
                    w1_ids = []
                    for p in st.session_state.draft_posts:
                        cur.execute("""
                            INSERT INTO posts (channel_id, campaign_week, content, creative_brief, scheduled_hour, status)
                            VALUES (?, 1, ?, ?, ?, 'published')
                        """, (p.channel_id, p.content, p.creative_brief, p.scheduled_hour))
                        w1_ids.append(cur.lastrowid)
                    conn.commit()
                    conn.close()
                    st.session_state.week1_ids = w1_ids

                    # Run Simulator Physics
                    for pid in w1_ids:
                        simulator.simulate_post(pid)

                    # Community Manager Auto-Replies
                    comm_df = query_dataframe(f"SELECT id, post_id, author, text FROM comments WHERE post_id IN ({','.join('?'*len(w1_ids))})", tuple(w1_ids))
                    if not comm_df.empty:
                        action = community_agent(comm_df.to_dict(orient="records"))
                        conn = sqlite3.connect(DB_FILE)
                        cur = conn.cursor()
                        for rep in getattr(action, "replies", []):
                            cur.execute("UPDATE comments SET agent_reply = ? WHERE id = ?", (rep.reply_text, rep.comment_id))
                        conn.commit()
                        conn.close()

                    # Analytics Agent Review
                    perf_df = query_dataframe(f"""
                        SELECT p.id, p.channel_id, p.content, p.scheduled_hour,
                               m.impressions, m.likes, m.comments_count, m.shares, m.engagement_rate
                        FROM posts p
                        JOIN post_metrics m ON p.id = m.post_id
                        WHERE p.id IN ({','.join('?'*len(w1_ids))})
                    """, tuple(w1_ids))
                    
                    st.session_state.analysis = analytics_agent(perf_df.to_dict(orient="records"))
                    st.session_state.stage = "published"
                    st.rerun()

        with b2:
            if st.button("❌ Reject Drafts"):
                st.session_state.stage = "input"
                st.rerun()

    # 2. CLOSED-LOOP WEEK 2 ITERATION
    if st.session_state.stage in ["published", "week2"]:
        st.subheader("3. Feedback Optimization Cycle (Week 2)")
        
        # Display recommendations extracted by Analytics Agent
        recs = getattr(st.session_state.analysis, "actionable_recommendations", [])
        if recs:
            st.markdown("**Directives Extracted from Analytics Agent:**")
            for r in recs:
                st.markdown(f"👉 **{r}**")

        if st.session_state.stage == "published":
            if st.button("📈 Run Week 2 Optimization Loop", type="primary"):
                with st.spinner("Passing directives to Strategy Agent & generating optimized Week 2 content..."):
                    week2_brief = (
                        f"{user_brief}\n\n"
                        f"DATA-BACKED STRATEGY DIRECTIVES FROM PREVIOUS PERFORMANCE CYCLE:\n" +
                        "\n".join([f"- {r}" for r in recs])
                    )

                    strat_v2 = strategy_agent(week2_brief)
                    w2_drafts = content_and_creative_agent(week2_brief, strat_v2)

                    conn = sqlite3.connect(DB_FILE)
                    cur = conn.cursor()
                    w2_ids = []
                    for p in w2_drafts.posts:
                        cur.execute("""
                            INSERT INTO posts (channel_id, campaign_week, content, creative_brief, scheduled_hour, status)
                            VALUES (?, 2, ?, ?, ?, 'published')
                        """, (p.channel_id, p.content, p.creative_brief, p.scheduled_hour))
                        w2_ids.append(cur.lastrowid)
                    conn.commit()
                    conn.close()

                    for pid in w2_ids:
                        simulator.simulate_post(pid)

                    st.session_state.week2_ids = w2_ids
                    st.session_state.stage = "week2"
                    st.rerun()

        if st.session_state.stage == "week2":
            st.success("Week 2 closed-loop adaptation executed successfully! Inspect 'Platform Telemetry' tab for delta measurements.")

# =====================================================================
# TAB 2: PLATFORM TELEMETRY & MEASURED DELTA
# =====================================================================
with tab_telemetry:
    if not st.session_state.week1_ids:
        st.info("No posts published yet. Launch and authorize a campaign to view metrics.")
    else:
        st.subheader("Week 1 Performance Metrics")
        w1_perf = query_dataframe(f"""
            SELECT p.id, p.channel_id, p.scheduled_hour,
                   m.impressions, m.likes, m.comments_count, m.shares, m.engagement_rate
            FROM posts p
            JOIN post_metrics m ON p.id = m.post_id
            WHERE p.id IN ({','.join('?'*len(st.session_state.week1_ids))})
        """, tuple(st.session_state.week1_ids))

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Impressions", f"{w1_perf['impressions'].sum():,}")
        m2.metric("Total Likes", f"{w1_perf['likes'].sum():,}")
        m3.metric("Total Comments", f"{w1_perf['comments_count'].sum():,}")
        m4.metric("Avg Engagement Rate", f"{w1_perf['engagement_rate'].mean():.2f}%")

        st.dataframe(w1_perf, use_container_width=True)

        # Community Inbound Thread
        with st.expander("💬 Audience Comments & Community Agent Replies"):
            comments_data = query_dataframe(
                f"SELECT post_id, author, sentiment, text, agent_reply FROM comments WHERE post_id IN ({','.join('?'*len(st.session_state.week1_ids))})", 
                tuple(st.session_state.week1_ids)
            )
            for _, r in comments_data.iterrows():
                st.markdown(f"**@{r['author']}** on Post #{r['post_id']} ({r['sentiment']}): _{r['text']}_")
                st.markdown(f"↳ **Agent Reply:** `{r['agent_reply']}`")
                st.markdown("---")

        # Week 1 vs. Week 2 Delta Comparison
        if st.session_state.week2_ids:
            st.markdown("---")
            st.subheader("📈 Closed-Loop Performance Delta (Week 1 vs. Week 2)")

            w1_data = query_dataframe(f"SELECT impressions, comments_count, likes FROM post_metrics WHERE post_id IN ({','.join('?'*len(st.session_state.week1_ids))})", tuple(st.session_state.week1_ids))
            w2_data = query_dataframe(f"SELECT impressions, comments_count, likes FROM post_metrics WHERE post_id IN ({','.join('?'*len(st.session_state.week2_ids))})", tuple(st.session_state.week2_ids))

            w1_imp, w2_imp = w1_data["impressions"].sum(), w2_data["impressions"].sum()
            w1_com, w2_com = w1_data["comments_count"].sum(), w2_data["comments_count"].sum()
            w1_lik, w2_lik = w1_data["likes"].sum(), w2_data["likes"].sum()

            c1, c2, c3 = st.columns(3)
            imp_delta = ((w2_imp - w1_imp) / max(w1_imp, 1)) * 100
            com_delta = ((w2_com - w1_com) / max(w1_com, 1)) * 100
            lik_delta = ((w2_lik - w1_lik) / max(w1_lik, 1)) * 100

            c1.metric("Total Impressions", f"{w2_imp:,}", f"{imp_delta:+.2f}%")
            c2.metric("Total Comments", f"{w2_com:,}", f"{com_delta:+.2f}%")
            c3.metric("Total Likes", f"{w2_lik:,}", f"{lik_delta:+.2f}%")

            chart_df = pd.DataFrame({
                "Metric": ["Impressions", "Comments", "Likes"] * 2,
                "Count": [w1_imp, w1_com, w1_lik, w2_imp, w2_com, w2_lik],
                "Week": ["Week 1 (Baseline)"] * 3 + ["Week 2 (Optimized)"] * 3
            })
            fig = px.bar(
                chart_df, 
                x="Metric", 
                y="Count", 
                color="Week", 
                barmode="group", 
                title="Performance Uplift from Analytics Recommendations"
            )
            st.plotly_chart(fig, use_container_width=True)

# =====================================================================
# TAB 3: AGENT CONVERSATION & NEGOTIATION TRACE
# =====================================================================
with tab_trace:
    st.subheader("Inter-Agent Decision Transcript")
    st.caption("Structured record of inter-agent messages, compliance reviews, and analytical directives.")

    traces = tracer.get_traces()
    if not traces:
        st.info("No traces logged yet. Start a campaign run to inspect inter-agent messages.")
    else:
        # Download buttons for evaluation submission
        d1, d2, _ = st.columns([1, 1, 3])
        with d1:
            try:
                with open("agent_trace.json", "r", encoding="utf-8") as f:
                    st.download_button("📥 Download JSON Trace", f.read(), file_name="agent_trace.json", mime="application/json")
            except FileNotFoundError:
                pass
        with d2:
            try:
                with open("agent_trace.md", "r", encoding="utf-8") as f:
                    st.download_button("📥 Download Markdown Trace", f.read(), file_name="agent_trace.md", mime="text/markdown")
            except FileNotFoundError:
                pass

        st.markdown("---")

        AVATARS = {
            "Orchestrator": "👔",
            "Strategy Agent": "🎯",
            "Content & Creative Agent": "✍️",
            "Compliance Agent": "🛡️",
            "Community Agent": "💬",
            "Analytics Agent": "📊",
            "Mock Social Platform": "🌐"
        }

        for t in traces:
            icon = AVATARS.get(t["sender"], "🤖")
            with st.chat_message(name=t["sender"], avatar=icon):
                st.markdown(f"**{t['sender']}** ➔ **{t['receiver']}** &nbsp;&nbsp; `<{t['action']}>` &nbsp;&nbsp; *{t['timestamp']}*")
                st.markdown(t["content"])