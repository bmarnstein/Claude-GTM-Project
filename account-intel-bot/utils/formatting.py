import re


def extract_top_pain_point(pain_points_text: str) -> str:
    """Extract the name of the highest-confidence pain point from the hypotheses text.

    Looks for the first hypothesis (which should be highest confidence) and
    maps it to one of the 8 core pain point categories for the Notion select field.
    """
    PAIN_POINT_CATEGORIES = [
        "Legacy Vendor Lock-in",
        "Fragmented Stack",
        "Slow Model Iteration",
        "High False Positives",
        "Rising Fraud Losses",
        "Regulatory Pressure",
        "Digital Transformation Gaps",
        "TCO",
    ]

    text_lower = pain_points_text.lower()
    for category in PAIN_POINT_CATEGORIES:
        if category.lower() in text_lower:
            return category

    return ""


def extract_domain_from_brief(brief_text: str) -> str:
    """Try to extract a company domain from the account brief text.

    Looks for URLs in the brief and extracts the domain.
    """
    urls = re.findall(r'https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', brief_text)
    if urls:
        # Filter out common non-company domains
        skip_domains = {
            "reuters.com", "bloomberg.com", "wsj.com", "nytimes.com",
            "sec.gov", "federalreserve.gov", "occ.gov", "fdic.gov",
            "linkedin.com", "glassdoor.com", "indeed.com",
            "google.com", "twitter.com", "facebook.com",
        }
        for domain in urls:
            if domain not in skip_domains:
                return domain

    return ""


def clean_outreach_for_dm(outreach_text: str) -> str:
    """Strip markdown formatting from outreach text for clean copy-paste in DMs.

    Removes bold markers, emoji, and header markers.
    """
    text = outreach_text
    # Remove markdown bold
    text = text.replace("**", "")
    # Remove heading markers
    text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)
    # Remove emoji at start of lines
    text = re.sub(r'^[📧💬👤✉️🎯📋🔥📄]\s*', '', text, flags=re.MULTILINE)
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def get_slack_thread_permalink(channel: str, ts: str, workspace_domain: str = "") -> str:
    """Construct a Slack thread permalink.

    If workspace_domain is not provided, returns a generic deep link.
    """
    # Convert ts to Slack's format (remove the dot)
    ts_formatted = ts.replace(".", "")
    if workspace_domain:
        return f"https://{workspace_domain}.slack.com/archives/{channel}/p{ts_formatted}"
    return f"https://slack.com/archives/{channel}/p{ts_formatted}"
