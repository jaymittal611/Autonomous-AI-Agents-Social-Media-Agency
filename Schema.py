from pydantic import BaseModel, Field
from typing import List


class StrategyPlan(BaseModel):
    target_audience: str = Field(
        description="Target audience demographics and psychographics, including age, interests, and behaviors")
    key_themes: list[str] = Field(
        description="Core campaign content themes based on business objectives and audience interests")
    channel_mix: list[str] = Field(
        description="Selected channels: Static_Image, Short_Video, Blog_Post")
    target_kpis: list[str] = Field(
        description="KPIs such as Engagement_rate, impressions, views, likes, comments, shares, saves, clicks")

class PostDraft(BaseModel):
    channel_id: str = Field(description="Target channel ID (Static_Image, Short_Video, Blog_Post)")
    content: str = Field(description=" Tagline(Meangingful & engaging), text, hooks, and hashtags")
    creative_brief: str = Field(description="Visual brief describing placeholder assets or media")
    scheduled_hour: int = Field(description="Scheduled publishing hour in 24h format (e.g. 13 or 19)")

class CampaignDrafts(BaseModel):
    posts: List[PostDraft]

class ComplianceReview(BaseModel):
    approved: bool = Field(description="True if the post meets brand niche, objective, brand guidelines and is engaging, False otherwise") 
    feedback: str = Field(description="Constructive critique if rejected, or approval notes")

class CommentReply(BaseModel): 
    comment_id: int = Field(description="ID of the comment being answered")
    reply_text: str = Field(description="Helpful, brand-centered reply to the user")

class CommunityAction(BaseModel):
    replies: List[CommentReply]

class WeeklyAnalysisReport(BaseModel):
    kpi_summary: str = Field(description="Summary of aggregate Engagement_rateimpressions, views, likes, comments, shares, saves and clicks")
    top_performing_post_id: int = Field(description="ID of the best post")
    top_performing_reason: str = Field(description="Valid Hypothesis on why this post outperformed")
    bottom_performing_post_id: int = Field(description="ID of the lowest performing post")
    bottom_performing_reason: str = Field(description="Valid Hypothesis on why this post underperformed")
    discovered_patterns: List[str] = Field(description="Observed correlations (length, questions, timing, hashtags)")
    actionable_recommendations: List[str] = Field(description="Specific, concrete changes for next week's campaign")