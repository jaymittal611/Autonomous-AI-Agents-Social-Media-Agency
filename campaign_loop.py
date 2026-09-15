import ollama

from mock_db import init_db, get_connection
from Simulator import EngagementSimulator
from Orchestrator import run_orchestrator
from agents import community_agent, analytics_agent, content_and_creative_agent, strategy_agent
from Schema import StrategyPlan

def run_simulation_and_community(post_ids: list):
    sim = EngagementSimulator()
    print("\n--- Publishing Posts & Simulating Audience ---")
    for pid in post_ids:
        sim.simulate_post(pid)

    # Community Management
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, post_id, author, text, sentiment 
        FROM comments 
        WHERE post_id IN ({})
    """.format(','.join('?' * len(post_ids))), post_ids)
    
    comments = [dict(row) for row in cursor.fetchall()]
    if comments:
        print(f"\n[Community Agent] Responding to {len(comments)} incoming audience comments...")
        actions = community_agent(comments)
        for rep in actions.replies:
            cursor.execute("UPDATE comments SET agent_reply = ? WHERE id = ?", (rep.reply_text, rep.comment_id))
        conn.commit()
    conn.close()
    print(f"[Community Agent] Completed responses for posts: {post_ids}")

def collect_metrics(post_ids: list) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.channel_id, p.content, p.scheduled_hour,
               m.impressions, m.likes, m.comments_count, m.shares
        FROM posts p
        JOIN post_metrics m ON p.id = m.post_id
        WHERE p.id IN ({})
    """.format(','.join('?' * len(post_ids))), post_ids)
    
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return data

def execute_closed_loop():
    init_db()
    brief = (input("Enter a sample human brief for the campaign orchestration: "))
    

    # 1. Week 1 Execution
    print("\n==================== [WEEK 1: INITIAL RUN] ====================")
    week1_post_ids = run_orchestrator(brief)
    run_simulation_and_community(week1_post_ids)

    # 2. Week 1 Analytics
    week1_metrics = collect_metrics(week1_post_ids)
    print("\n[Analytics Agent] Analyzing Week 1 Data...")
    report = analytics_agent(week1_metrics)

    print("\n" + "=" * 50)
    print("📊 WEEK 1 ANALYTICS REPORT")
    print("=" * 50)
    print(f"Top Post: #{report.top_performing_post_id} | Reason: {report.top_performing_reason}")
    print(f"Bottom Post: #{report.bottom_performing_post_id} | Reason: {report.bottom_performing_reason}")
    print("\nDiscovered Patterns:")
    for pat in report.discovered_patterns:
        print(f"  • {pat}")
    print("\nActionable Recommendations:")
    for rec in report.actionable_recommendations:
        print(f"  ➜ {rec}")

    # 3. Week 2 Closed-Loop Adaptation
    print("\n==================== [WEEK 2: ADAPTATION RUN] ====================")
    print("Feeding Analytics recommendations back into Strategy & Content generation...")

    adapted_brief = (
        f"{brief}\n\nSTRICT OPTIMIZATIONS FROM LAST WEEK'S PERFORMANCE DATA:\n"
        + "\n".join(report.actionable_recommendations)
    )

    strategy_week2 = strategy_agent(adapted_brief)
    week2_drafts = content_and_creative_agent(adapted_brief, strategy_week2)

    conn = get_connection()
    cursor = conn.cursor()
    week2_post_ids = []
    for post in week2_drafts.posts:
        cursor.execute("""
            INSERT INTO posts (channel_id, content, creative_brief, scheduled_hour, status)
            VALUES (?, ?, ?, ?, 'published')
        """, (post.channel_id, post.content, post.creative_brief, post.scheduled_hour))
        week2_post_ids.append(cursor.lastrowid)
    conn.commit()
    conn.close()

    run_simulation_and_community(week2_post_ids)
    week2_metrics = collect_metrics(week2_post_ids)

    # 4. Before / After Comparison
    w1_impressions = sum(m["impressions"] for m in week1_metrics)
    w2_impressions = sum(m["impressions"] for m in week2_metrics)
    w1_comments = sum(m["comments_count"] for m in week1_metrics)
    w2_comments = sum(m["comments_count"] for m in week2_metrics)

    print("\n" + "=" * 50)
    print("📈 CLOSED-LOOP PERFORMANCE DELTA (WEEK 1 vs WEEK 2)")
    print("=" * 50)
    print(f"Total Impressions: Week 1 = {w1_impressions:,}  -->  Week 2 = {w2_impressions:,} ({(w2_impressions - w1_impressions)/w1_impressions:+.1%})")
    print(f"Total Comments:    Week 1 = {w1_comments:,}  -->  Week 2 = {w2_comments:,} ({(w2_comments - w1_comments)/w1_comments:+.1%})")
    while True:
        cont = str(input("\nDo you want to run Campaign cycle or Business Related Queries or Exit? : ").strip().lower())
        if cont == "Campaign Cycle":
            execute_closed_loop()
            break
        elif cont == "Business Related Queries":
            response= ollama.chat(messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": input("Enter your business related query: ")}], model="llama3.1:8b", base_url="http://localhost:11434")
            return print(f"Response: {response['message']['content']}")
        elif cont == "Exit":
            print("[Exit] Closed-loop simulation completed.")
            break
        else:
            print("Invalid input. Please enter 'Campaign Cycle', 'Business Related Queries', or 'Exit'.")

if __name__ == "__main__":
    execute_closed_loop()