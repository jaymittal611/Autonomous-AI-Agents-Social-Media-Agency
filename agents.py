from Schema import (
    StrategyPlan, 
    PostDraft, 
    CampaignDrafts, 
    ComplianceReview, 
    CommunityAction, 
    WeeklyAnalysisReport
)
from Local_llm import OllamaStructured
from agent_tracer import tracer

ollama = OllamaStructured()

def strategy_agent(user_input: str) -> StrategyPlan:
    # 1. Log incoming orchestrator dispatch
    tracer.log_message(
        sender="Orchestrator",
        receiver="Strategy Agent",
        action="DISPATCH_BRIEF",
        content=f"Decompose this client brief into practical strategy components: '{user_input}'"
    )

    system_prompt = """
You are an expert social-media strategist with 10+ years of experience. Break a campaign brief into practical strategy components.
Allowed channels:
- Static_image
- Short_video
- Blog_post""" 
    user_prompt = f"Develop an actionable strategy for this brief:\n{user_input}"

    plan = ollama.ask(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_model=StrategyPlan,
    )

    # 2. Log strategy handoff to content team
    tracer.log_message(
        sender="Strategy Agent",
        receiver="Content & Creative Agent",
        action="STRATEGY_HANDOFF",
        content=(
            f"Strategy finalized.\n"
            f"- Audience: {plan.target_audience}\n"
            f"- Channels: {', '.join(plan.channel_mix)}\n"
            f"- Themes: {', '.join(plan.key_themes)}"
        ),
        metadata={"channel_mix": plan.channel_mix}
    )

    return plan


def content_and_creative_agent(brief: str, strategy: StrategyPlan, feedback_context: str = "") -> CampaignDrafts:
    """Content & Creative Agent: Produces, copy, hooks, hashtags, schedules, and visual briefs."""
    system_prompt = (
        "You are an expert Social Media Copywriter and Creative Director. "
        "Write 3 platform-tailored posts covering the chosen channels: "
        "'Static_image' (concise, snappy hooks, questions, <50 words), "
        "'Short_video' (Strict_word_limit=80-100, brandfocused, engaging, 2-3 hashtags), and "
        "'Blog_post' (value-driven, Strict_word_limit=150-180, professional tone). "
        "Include a creative brief describing visual assets for each type of post."
    )
    user_prompt = (
        f"Campaign Brief: {brief}\n"
        f"Audience: {strategy.target_audience}\n"
        f"Themes: {', '.join(strategy.key_themes)}\n"
        f"Target Channels: {', '.join(strategy.channel_mix)}\n"
    )
    if feedback_context:
        user_prompt += f"\nImportant Compliance Feedback from previous rejection:\n{feedback_context}"

    drafts = ollama.ask(system_prompt, user_prompt, CampaignDrafts)

    tracer.log_message(
        sender="Content & Creative Agent",
        receiver="Compliance Agent",
        action="SUBMIT_DRAFTS_FOR_AUDIT",
        content=f"Generated {len(drafts.posts)} draft post(s) for channels: {', '.join(p.channel_id for p in drafts.posts)}."
    )

    return drafts


def compliance_agent(post_content: str, channel: str) -> ComplianceReview:
    """Brand & Compliance Agent: Enforces tone, length, and claims with rejection capability."""
    tracer.log_message(
        sender="Content & Creative Agent",
        receiver="Compliance Agent",
        action="AUDIT_POST_REQUEST",
        content=f"Requesting compliance audit for channel [{channel}]:\n\"{post_content}\""
    )

    system_prompt = (
        "You are a Brand & Compliance Officer. Review social posts. "
        "Content_Word_limits: 'Short_Image' < 50 words, 80 <'Static_Video' < 100 words, 150 <'Blog_Post' < 180 words. "
        "Reject any post that makes wild unsubstantiated promises (e.g., 'guaranteed', '100% life-changing'), "
        "exceeds the word limit for its channel, or uses offensive language. Approve solid, truthful copy."
    )
    user_prompt = f"Channel: {channel}\nPost Content:\n\"{post_content}\""
    
    review = ollama.ask(system_prompt, user_prompt, ComplianceReview)

    # Determine approval status based on boolean attribute
    is_approved = getattr(review, "approved", False) or getattr(review, "passed", False)
    status_label = "APPROVED" if is_approved else "REJECTED"
    feedback_text = getattr(review, "feedback", "") or getattr(review, "critique", "")

    tracer.log_message(
        sender="Compliance Agent",
        receiver="Content & Creative Agent" if not is_approved else "Orchestrator",
        action=f"COMPLIANCE_{status_label}",
        content=f"Channel [{channel}] status: {status_label}. Feedback: {feedback_text}"
    )

    return review


def community_agent(comments_data: list) -> CommunityAction:
    """Community Manager Agent: Reads mock audience comments and crafts on-brand replies."""
    tracer.log_message(
        sender="Mock Social Platform",
        receiver="Community Agent",
        action="INBOUND_COMMENTS_ALERT",
        content=f"Received {len(comments_data)} audience comments to review and address."
    )

    system_prompt = (
        "You are a helpful, witty Community Manager. Respond politely to customer questions, "
        "reassure skeptics about price/quality, and address questions directly."
    )
    user_prompt = f"Review these incoming comments and draft replies:\n{comments_data}"
    
    action = ollama.ask(system_prompt, user_prompt, CommunityAction)

    replies_count = len(getattr(action, "replies", []))
    tracer.log_message(
        sender="Community Agent",
        receiver="Mock Social Platform",
        action="PUBLISH_REPLIES",
        content=f"Drafted and submitted {replies_count} responses to audience comments."
    )

    return action


def analytics_agent(campaign_metrics: list) -> WeeklyAnalysisReport:
    """Analytics Agent: Inspects post performance data to find signals and actionable changes."""
    tracer.log_message(
        sender="Mock Social Platform",
        receiver="Analytics Agent",
        action="PERFORMANCE_DATA_FEED",
        content=f"Transmitting telemetry data for {len(campaign_metrics)} campaign posts."
    )

    system_prompt = (
        "You are a Chief Data & Analytics Officer. Analyze post performance metrics. "
        "Find empirical patterns across post length, question endings, scheduling times, and hashtags. "
        "Do NOT give vague advice. Provide exact, prescriptive adjustments for next week."
    )
    user_prompt = (
        f"Analyze these campaign results from the mock platform and produce your weekly review:\n"
        f"{campaign_metrics}"
    )
    
    report = ollama.ask(system_prompt, user_prompt, WeeklyAnalysisReport)

    recommendations = getattr(report, "actionable_recommendations", []) or getattr(report, "concrete_strategy_directives", [])
    tracer.log_message(
        sender="Analytics Agent",
        receiver="Strategy Agent",
        action="ANALYTICS_RECOMMENDATIONS_DISPATCH",
        content=(
            f"Performance report generated.\n"
            f"Key recommendations: {'; '.join(recommendations)}"
        )
    )

    return report
# from Schema import StrategyPlan, PostDraft, CampaignDrafts, ComplianceReview, CommunityAction, WeeklyAnalysisReport
# from Local_llm import  OllamaStructured

# ollama = OllamaStructured()
# def strategy_agent(user_input: str) -> StrategyPlan:
#     system_prompt = """
# You are an expert social-media strategist with 10+ years of experience. Break a campaign brief into practical strategy components.
# Allowed channels:
# - Static_image
# - Short_video
# - Blog_post""" 
#     user_prompt = f"Develop an actionable strategy for this brief:\n{user_input}"

#     return ollama.ask(
#         system_prompt=system_prompt,
#         user_prompt=user_prompt,
#         output_model=StrategyPlan,
#     )

# def content_and_creative_agent(brief: str, strategy: StrategyPlan, feedback_context: str = "") -> CampaignDrafts:
#     """Content & Creative Agent: Produces, copy, hooks, hashtags, schedules, and visual briefs."""
#     system_prompt = (
#         "You are an expert Social Media Copywriter and Creative Director. "
#         "Write 3 platform-tailored posts covering the chosen channels: "
#         "'Static_image' (concise, snappy hooks, questions, <50 words), "
#         "'Short_video' (Strict_word_limit=80-100, brandfocused, engaging, 2-3 hashtags), and "
#         "'Blog_post' (value-driven, Strict_word_limit=150-180, professional tone). "
#         "Include a creative brief describing visual assets for each type of post."
#     )
#     user_prompt = (
#         f"Campaign Brief: {brief}\n"
#         f"Audience: {strategy.target_audience}\n"
#         f"Themes: {', '.join(strategy.key_themes)}\n"
#         f"Target Channels: {', '.join(strategy.channel_mix)}\n"
#     )
#     if feedback_context:
#         user_prompt += f"\nImportant Compliance Feedback from previous rejection:\n{feedback_context}"

#     return ollama.ask(system_prompt, user_prompt, CampaignDrafts)

# def compliance_agent(post_content: str, channel: str) -> ComplianceReview:
#     """Brand & Compliance Agent: Enforces tone, length, and claims with rejection capability."""
#     system_prompt = (
#         "You are a Brand & Compliance Officer. Review social posts. "
#         "Content_Word_limits: 'Short_Image' < 50 words, 80 <'Static_Video' < 100 words, 150 <'Blog_Post' < 180 words. "
#         "Reject any post that makes wild unsubstantiated promises (e.g., 'guaranteed', '100% life-changing'), "
#         "exceeds the word limit for its channel, or uses offensive language. Approve solid, truthful copy."
#     )
#     user_prompt = f"Channel: {channel}\nPost Content:\n\"{post_content}\""
#     return ollama.ask(system_prompt, user_prompt, ComplianceReview)

# def community_agent(comments_data: list) -> CommunityAction:
#     """Community Manager Agent: Reads mock audience comments and crafts on-brand replies."""
#     system_prompt = (
#         "You are a helpful, witty Community Manager. Respond politely to customer questions, "
#         "reassure skeptics about price/quality, and address questions directly."
#     )
#     user_prompt = f"Review these incoming comments and draft replies:\n{comments_data}"
#     return ollama.ask(system_prompt, user_prompt, CommunityAction)

# def analytics_agent(campaign_metrics: list) -> WeeklyAnalysisReport:
#     """Analytics Agent: Inspects post performance data to find signals and actionable changes."""
#     system_prompt = (
#         "You are a Chief Data & Analytics Officer. Analyze post performance metrics. "
#         "Find empirical patterns across post length, question endings, scheduling times, and hashtags. "
#         "Do NOT give vague advice. Provide exact, prescriptive adjustments for next week."
#     )
#     user_prompt = (
#         f"Analyze these campaign results from the mock platform and produce your weekly review:\n"
#         f"{campaign_metrics}"
#     )
#     return ollama.ask(system_prompt, user_prompt, WeeklyAnalysisReport)