import logging
from research.web_search import search_company, format_search_results

logger = logging.getLogger(__name__)


async def gather_research(company_name: str) -> tuple[dict[str, list[dict]], str]:
    """Orchestrate all research for a company.

    Returns:
        raw_results: Dict of search category -> list of result dicts
        formatted_results: Single formatted string for Claude prompts
    """
    logger.info(f"Starting research aggregation for: {company_name}")

    raw_results = await search_company(company_name)

    # Count total results across all categories
    total = sum(len(v) for v in raw_results.values())
    categories_with_results = sum(1 for v in raw_results.values() if v)
    logger.info(
        f"Research complete: {total} results across "
        f"{categories_with_results}/{len(raw_results)} categories"
    )

    formatted_results = format_search_results(raw_results)

    return raw_results, formatted_results
