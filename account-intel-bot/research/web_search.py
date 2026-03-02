import asyncio
import logging
from tavily import AsyncTavilyClient

from config import TAVILY_API_KEY

logger = logging.getLogger(__name__)

client = AsyncTavilyClient(api_key=TAVILY_API_KEY)


async def search(query: str, max_results: int = 5) -> list[dict]:
    """Execute a single Tavily search and return structured results."""
    try:
        response = await client.search(
            query=query,
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
        )
        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "score": r.get("score", 0),
            })
        return results
    except Exception as e:
        logger.error(f"Tavily search failed for query '{query}': {e}")
        return []


async def search_company(company_name: str) -> dict[str, list[dict]]:
    """Run 8-10 parallel searches covering different research angles for a company.

    Returns a dict keyed by search category with lists of result dicts.
    """
    queries = {
        "overview": f"{company_name} company overview financials revenue employees headquarters",
        "risk_stack": f"{company_name} fraud detection risk management technology vendor platform",
        "earnings": f"{company_name} earnings call fraud risk compliance 2025 2026",
        "regulatory": f"{company_name} regulatory action fine consent order OCC FDIC FinCEN",
        "jobs": f"{company_name} job posting fraud risk engineer AML compliance analyst",
        "digital": f"{company_name} digital transformation payments fintech innovation 2025 2026",
        "executive": f"{company_name} chief risk officer CISO head of fraud executive hire departure",
        "competitors": f"{company_name} Actimize Feedzai Featurespace NICE risk vendor",
        "incidents": f"{company_name} fraud incident data breach security cyber attack",
        "annual_report": f"{company_name} annual report risk management strategy technology investment",
    }

    tasks = {
        category: search(query)
        for category, query in queries.items()
    }

    results = {}
    gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)
    for category, result in zip(tasks.keys(), gathered):
        if isinstance(result, Exception):
            logger.error(f"Search category '{category}' failed: {result}")
            results[category] = []
        else:
            results[category] = result

    return results


def format_search_results(results: dict[str, list[dict]]) -> str:
    """Format all search results into a single string for inclusion in Claude prompts."""
    sections = []
    for category, items in results.items():
        if not items:
            continue
        section_lines = [f"=== {category.upper().replace('_', ' ')} ==="]
        for item in items:
            section_lines.append(f"\nTitle: {item['title']}")
            section_lines.append(f"URL: {item['url']}")
            section_lines.append(f"Content: {item['content']}")
            section_lines.append(f"Relevance Score: {item['score']}")
        sections.append("\n".join(section_lines))
    return "\n\n".join(sections)
