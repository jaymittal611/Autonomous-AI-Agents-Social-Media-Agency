from agents import strategy_agent, content_and_creative_agent, compliance_agent, community_agent, analytics_agent
from Schema import StrategyPlan, PostDraft, CampaignDrafts, ComplianceReview, CommunityAction, WeeklyAnalysisReport
from typing import Optional
from mock_db import init_db, get_connection

def run_orchestrator(brief: str) -> None:
    print("=" * 60)
    print("CAMPAIGN ORCHESTRATION STARTED")
    print(f"Human Brief: {brief}")
    print("=" * 60)

    print("\n[Orchestrator] Invoking Strategy Agent...")
    strategy = strategy_agent(brief)
    print(f"Strategy Approved:\n- Target: {strategy.target_audience}\n- Channels: {strategy.channel_mix}\n- KPIs: {strategy.target_kpis}")

# 2. Content & Creative Loop with Compliance Agent
    max_revisions = 3
    final_approved_posts = []
    
    for channel in strategy.channel_mix:
        print(f"\n[Orchestrator] Drafting content for channel: {channel}...")
        feedback_history = ""
        post_approved = False
        current_post: Optional[PostDraft] = None

        for attempt in range(1, max_revisions+1 ):
            drafts = content_and_creative_agent(brief, strategy, feedback_history)
            candidate_posts = [p for p in drafts.posts if p.channel_id == channel]
            
            if not candidate_posts:
                candidate_posts = [drafts.posts[0]]
                candidate_posts[0].channel_id = channel
            
            current_post = candidate_posts[0]
            print(f"  > Attempt {attempt}: Compliance reviewing post draft...")
            
            review = compliance_agent(current_post.content, channel)
            if review.approved:
                print(f"  [✓] Compliance Approved: {review.feedback}")
                post_approved = True
                break
            else:
                print(f"  [✗] Compliance Rejected: {review.feedback}")
                feedback_history += f"Attempt {attempt} rejected: {review.feedback}\n"
                


        if not post_approved:
            print(f"[!] Warning: Compliance review hit retry limit on {channel}. Proceeding with latest revision.")
            Complete_rejection= input("Do you want to re-enter your brief or exit?")
            if Complete_rejection.lower() in {"exit", "quit"}:
                print("[Abort] Campaign rejected by operator. Exiting.")
                exit()
            else:
                run_orchestrator(input("Please re-enter your brief: "))  # Recursive call to re-run the orchestrator with feedback
        
        final_approved_posts.append(current_post)

    # 3. Human-in-the-Loop Approval Gate
    print("\n" + "=" * 60)
    print("📋 PROPOSED CAMPAIGN PLAN FOR REVIEW")
    print("=" * 60)
    for idx, post in enumerate(final_approved_posts, 1):
        print(f"\nPost #{idx} [{post.channel_id.upper()}] (Scheduled: {post.scheduled_hour}:00)")
        print(f"Creative Brief: {post.creative_brief}")
        print(f"Content:\n{post.content}")
        print("-" * 40)

    user_decision = input("\n[Human Gate] Do you approve this campaign? (y/n): ").strip().lower()
    if user_decision != "y":
        Complete_rejection= input("Do you want to re-enter your brief or exit?")
        if Complete_rejection.lower() in {"exit", "quit"}:
            print("[Abort] Campaign rejected by operator. Exiting.")
            exit()
        else:
            run_orchestrator(input("Please re-enter your brief: "))  # Recursive call to re-run the orchestrator with feedback
        
    
    # 4. Save to Mock Platform Database (Publishing Queue)
    conn = get_connection()
    cursor = conn.cursor()
    saved_ids = []
    for post in final_approved_posts:
        cursor.execute("""
            INSERT INTO posts (channel_id, content, creative_brief, scheduled_hour, status)
            VALUES (?, ?, ?, ?, 'approved')
        """, (post.channel_id, post.content, post.creative_brief, post.scheduled_hour))
        saved_ids.append(cursor.lastrowid)
    conn.commit()
    conn.close()

    print(f"\n Campaign approved! {len(saved_ids)} posts saved to database with IDs: {saved_ids}")
    return saved_ids

if __name__ == "__main__":
    init_db()
    sample_brief = (input("Enter a sample human brief for the campaign orchestration: ")
    )
    run_orchestrator(sample_brief)

if __name__ == "__main__":
    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            break

        if user_input:
            run_orchestrator(user_input)