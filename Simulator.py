import sqlite3
import random
from mock_db import get_connection

class EngagementSimulator:
    """
    PLANTED RULES (Ground Truth):
    1. Question Rule: Posts ending in '?' receive 2.0x comments.
    2. Static_Image Length Penalty: Posts on 'Static_Image' with > 50 words suffer a 50% impression cut.
    3. Peak Time Window: Posts scheduled at peak hours (12-14 or 18-20) gain 1.4x impressions.
    4. Hashtag Penalty: Posts with 0 hashtags or > 5 hashtags suffer a 25% reach reduction.
    """

    def simulate_post(self, post_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        post = cursor.fetchone()
        if not post:
            conn.close()
            return

        channel_id = post["channel_id"]
        content = post["content"].strip()
        hour = post["scheduled_hour"] or 12

        words = content.split()
        word_count = len(words)
        hashtag_count = sum(1 for w in words if w.startswith("#"))
        has_question = content.endswith("?")

        # 1. Base impressions by channel
        base_reach = {
            "Static_Image": 1200,
            "Short_Video": 1800,
            "Blog_Post": 800
        }.get(channel_id, 1000)

        # 2. Timing Multiplier
        time_mult = 1.4 if (12 <= hour <= 14 or 18 <= hour <= 20) else 0.8

        # 3. Channel Word Count Penalty
        length_mult = 0.5 if (channel_id == "Static_Image" and word_count > 50) else 1.0

        # 4. Hashtag Multiplier
        hashtag_mult = 0.75 if (hashtag_count == 0 or hashtag_count > 5) else 1.2

        # Final Impressions (with slight +/- 5% noise)
        noise = random.uniform(0.95, 1.05)
        impressions = int(base_reach * time_mult * length_mult * hashtag_mult * noise)

        # Likes (~4% of impressions)
        likes = int(impressions * 0.04 * random.uniform(0.9, 1.1))

        # Comments (base 1.5% of impressions, boosted 3x if ends in a question)
        comment_mult = 3.0 if has_question else 1.0
        comments_count = int(impressions * 0.015 * comment_mult * random.uniform(0.9, 1.1))

        # Shares (~1% of impressions)
        shares = int(impressions * 0.01 * random.uniform(0.8, 1.2))

        engagement_rate = (
            (likes + comments_count + shares) / impressions * 100
            if impressions
            else 0
        )

        # Save Metrics
        cursor.execute("""
            INSERT OR REPLACE INTO post_metrics (
                post_id, impressions, likes, comments_count, shares, engagement_rate
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (post_id, impressions, likes, comments_count, shares, engagement_rate))

        # Generate Mock Audience Comments for the Community Agent
        self._generate_comments(cursor, post_id, has_question, channel_id)

        conn.commit()
        conn.close()
        print(f"[Simulator] Post #{post_id} simulated: {impressions} views, {likes} likes, {comments_count} comments.")

    def _generate_comments(self, cursor, post_id: int, has_question: bool, channel_id: str):
        sample_comments = [
            ("Alex_Student", "How much does it cost? Is there a student discount?", "neutral"),
            ("CoffeeLover99", "Does it use regular ground coffee or pods?", "neutral"),
            ("BudgetGuru", "Looks clean! Perfect for a dorm room.", "positive")
        ]
        if has_question:
            sample_comments.append(("DailyGrind", "Definitely option A! Much more reliable.", "positive"))

        for author, text, sentiment in sample_comments[:random.randint(2, 4)]:
            cursor.execute("""
                INSERT INTO comments (post_id, author, text, sentiment)
                VALUES (?, ?, ?, ?)
            """, (post_id, author, text, sentiment))

if __name__ == "__main__":
    from mock_db import init_db
    init_db()
    
    # Test simulation run
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO posts (channel_id, content, creative_brief, scheduled_hour, status)
        VALUES ('Static_Image', 'Need espresso on a student budget? Which roast do you prefer?', 'Photo of coffee cup on a study desk', 13, 'published')
    """)
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()

    sim = EngagementSimulator()
    sim.simulate_post(post_id)