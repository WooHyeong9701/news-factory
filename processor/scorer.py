from datetime import datetime

class IssueScorer:
    def __init__(self, w_density=1.0, w_velocity=2.0, w_social=0.5):
        self.w_density = w_density     # D
        self.w_velocity = w_velocity   # V
        self.w_social = w_social       # S

    def calculate_score(self, stats: dict) -> float:
        """
        Score = (w1 * Density) + (w2 * Velocity) + (w3 * SocialResponse)
        """
        density = stats.get('article_count', 0)
        
        # Calculate Velocity (articles per hour)
        first_seen_str = stats.get('first_seen')
        if first_seen_str:
            first_seen = datetime.strptime(first_seen_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            hours_elapsed = (now - first_seen).total_seconds() / 3600
            velocity = density / (hours_elapsed + 0.5) # Avoid division by zero
        else:
            velocity = 0
            
        social_response = (stats.get('total_comments') or 0) + (stats.get('total_reactions') or 0)
        
        # Normalized Social (e.g., scale it down slightly)
        social_score = social_response / 10.0
        
        total_score = (self.w_density * density) + \
                      (self.w_velocity * velocity) + \
                      (self.w_social * social_score)
        
        return round(total_score, 2)

    def select_top_issues(self, db, threshold=15.0):
        """
        Fetch active issues, score them, and return prioritized list.
        """
        active_issues = db.get_active_issues(hours=24)
        scored_issues = []
        
        for issue in active_issues:
            stats = db.get_issue_stats(issue['id'])
            score = self.calculate_score(stats)
            
            if score >= threshold:
                issue['score'] = score
                issue['stats'] = stats
                scored_issues.append(issue)
        
        # Sort by score descending
        scored_issues.sort(key=lambda x: x['score'], reverse=True)
        return scored_issues
