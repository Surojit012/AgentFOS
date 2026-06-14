"""
Intelligence Summarizer — generates AI narrative summaries for portfolio allocations.

Calls Claude Sonnet via Straico API (https://api.straico.com/v1/prompt/completion).
Falls back to a generic summary string if API key is missing or call fails.
"""

import json
import httpx
from pathlib import Path
from typing import Any, Dict

from config import settings


# Load prompt template at module level
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "summarize.txt"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")

# Straico API configuration
STRAICO_API_URL = "https://api.straico.com/v1/prompt/completion"
STRAICO_MODEL = "anthropic/claude-3.5-sonnet"

# Mock fallback summary — used when Straico API is unavailable
_MOCK_SUMMARY = (
    "This portfolio targets risk-adjusted RWA yields above US Treasury benchmarks, "
    "diversified across tokenized treasuries, private credit, and trade finance protocols. "
    "Key risk factors to monitor include TVL fluctuations, issuer concentration changes, "
    "and evolving audit coverage across the allocated protocols."
)


async def summarize_allocation(
    allocation_data: Dict[str, Any],
    treasury_rate: float,
) -> str:
    """
    Generate a 2-3 sentence AI narrative summary for a portfolio allocation.

    Uses Claude Sonnet via Straico API. Falls back to a generic summary
    if API key is missing or the call fails.

    Args:
        allocation_data: Full AllocationResponse dict
        treasury_rate: Current 10Y Treasury rate

    Returns: str — 2-3 sentence narrative summary
    """
    # Check for API key first
    if not settings.STRAICO_API_KEY:
        return _MOCK_SUMMARY

    try:
        # Build prompt from template
        portfolio_json = json.dumps(allocation_data, indent=2, default=str)
        prompt = _PROMPT_TEMPLATE.format(
            portfolio_json=portfolio_json,
            treasury_rate=treasury_rate,
        )

        # Call Straico API
        headers = {
            "Authorization": f"Bearer {settings.STRAICO_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "models": ["anthropic/claude-sonnet-4.5"],
            "message": prompt,
            "temperature": 0.3,
            "max_tokens": 200,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                STRAICO_API_URL,
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        # Extract completion text from Straico response
        # Structure is data.completions['anthropic/claude-sonnet-4.5'].completion.choices[0].message.content
        completions = data.get("data", {}).get("completions", {})
        model_data = completions.get("anthropic/claude-sonnet-4.5", {})
        completion = model_data.get("completion", {})
        choices = completion.get("choices", [])
        
        if choices and len(choices) > 0:
            content = choices[0].get("message", {}).get("content", "")
            if content:
                return content.strip()

        return _MOCK_SUMMARY
    except Exception as e:
        # Silent fallback — demo must never crash
        return _MOCK_SUMMARY
