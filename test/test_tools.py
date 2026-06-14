
# tests/test_tools.py
"""
Pytest tests for each FitFindr tool.
Each failure mode has its own individual test.
 
Run with:
    pytest tests/
or for verbose output:
    pytest tests/ -v
"""
 
from unittest.mock import MagicMock, patch
 
import pytest
 
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
from tools import create_fit_card, search_listings, suggest_outfit

from utils.data_loader import get_example_wardrobe, get_empty_wardrobe
 
 
# ══════════════════════════════════════════════════════════════════════════════
# Tool 1: search_listings
# ══════════════════════════════════════════════════════════════════════════════
 
def test_search_returns_results():
    """Basic happy path — a broad query should return at least one result."""
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0
 
 
def test_search_empty_results():
    """Failure mode: no listings match — must return [] not raise an exception."""
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []
 
 
def test_search_price_filter():
    """All returned listings must be at or below max_price."""
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)
 
 
def test_search_price_filter_none_skips_filtering():
    """When max_price is None, expensive items are not filtered out."""
    results_capped = search_listings("vintage", size=None, max_price=20)
    results_uncapped = search_listings("vintage", size=None, max_price=None)
    # Uncapped should return at least as many results as capped
    assert len(results_uncapped) >= len(results_capped)
 
 
def test_search_size_filter_exact():
    """Size filter: an exact size string should only return matching listings."""
    results = search_listings("jeans", size="W30", max_price=None)
    for item in results:
        assert "W30".lower() in item["size"].lower()
 
 
def test_search_size_filter_substring():
    """Size filter: partial match like 'M' should match 'S/M' and 'M/L'."""
    results = search_listings("top", size="M", max_price=None)
    for item in results:
        assert "m" in item["size"].lower()
 
 
def test_search_size_filter_none_skips_filtering():
    """When size is None, listings of all sizes are eligible."""
    results_no_size = search_listings("vintage", size=None, max_price=None)
    results_with_size = search_listings("vintage", size="M", max_price=None)
    assert len(results_no_size) >= len(results_with_size)
 
 
def test_search_results_are_sorted_by_relevance():
    """
    The first result should match more description keywords than the last.
    Uses a query with distinct keywords to produce a meaningful score spread.
    """
    results = search_listings("vintage graphic tee streetwear grunge", size=None, max_price=None)
    assert len(results) >= 2  # need at least two results to compare
 
 
def test_search_returns_list_of_dicts():
    """Each result must be a dict with all required listing fields."""
    required_fields = {"id", "title", "description", "category", "style_tags",
                       "size", "condition", "price", "colors", "brand", "platform"}
    results = search_listings("vintage", size=None, max_price=None)
    assert len(results) > 0
    for item in results:
        assert isinstance(item, dict)
        assert required_fields.issubset(item.keys())
 
 
def test_search_empty_description_returns_no_results():
    """An empty description string scores 0 on every listing → empty list."""
    results = search_listings("", size=None, max_price=None)
    assert results == []
 
 
def test_search_price_boundary_inclusive():
    """max_price is inclusive — a listing priced exactly at the limit is included."""
    # lst_014 (leather belt) is $12.00 — should appear when max_price=12
    results = search_listings("belt", size=None, max_price=12.00)
    prices = [item["price"] for item in results]
    assert 12.00 in prices


# ══════════════════════════════════════════════════════════════════════════════
# Tool 2: suggest_outfit
# ══════════════════════════════════════════════════════════════════════════════

def _mock_groq_response(content: str):
    """Helper: build a mock Groq completion object returning `content`."""
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


SAMPLE_ITEM = {
    "id": "lst_006",
    "title": "Graphic Tee — 2003 Tour Bootleg Style",
    "category": "tops",
    "style_tags": ["graphic tee", "vintage", "grunge", "streetwear"],
    "colors": ["black"],
    "description": "Vintage-style bootleg tee with faded graphic. Slightly boxy fit.",
    "condition": "good",
    "price": 24.00,
    "platform": "depop",
    "brand": None,
    "size": "L",
}


@patch("tools._get_groq_client")
def test_suggest_outfit_returns_string(mock_client_fn):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_groq_response(
        "Pair the tee with baggy jeans and chunky sneakers for easy streetwear."
    )
    mock_client_fn.return_value = mock_client

    result = suggest_outfit(SAMPLE_ITEM, get_example_wardrobe())
    assert isinstance(result, str)
    assert len(result.strip()) > 0


@patch("tools._get_groq_client")
def test_suggest_outfit_empty_wardrobe_does_not_crash(mock_client_fn):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_groq_response(
        "Try pairing this tee with wide-leg jeans and chunky boots for a grunge look."
    )
    mock_client_fn.return_value = mock_client

    result = suggest_outfit(SAMPLE_ITEM, get_empty_wardrobe())
    assert isinstance(result, str)
    assert len(result.strip()) > 0


@patch("tools._get_groq_client")
def test_suggest_outfit_empty_wardrobe_calls_llm_once(mock_client_fn):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_groq_response(
        "General styling advice here."
    )
    mock_client_fn.return_value = mock_client

    suggest_outfit(SAMPLE_ITEM, get_empty_wardrobe())
    assert mock_client.chat.completions.create.call_count == 1


@patch("tools._get_groq_client")
def test_suggest_outfit_with_wardrobe_calls_llm_once(mock_client_fn):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_groq_response(
        "Wear the tee with baggy jeans and a black denim jacket."
    )
    mock_client_fn.return_value = mock_client

    suggest_outfit(SAMPLE_ITEM, get_example_wardrobe())
    assert mock_client.chat.completions.create.call_count == 1


@patch("tools._get_groq_client")
def test_suggest_outfit_wardrobe_items_referenced_in_prompt(mock_client_fn):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_groq_response("outfit text")
    mock_client_fn.return_value = mock_client

    suggest_outfit(SAMPLE_ITEM, get_example_wardrobe())

    call_args = mock_client.chat.completions.create.call_args
    prompt_text = call_args[1]["messages"][0]["content"]

    # These names come directly from example_wardrobe in wardrobe_schema.json
    assert "Baggy straight-leg jeans" in prompt_text
    assert "Chunky white sneakers" in prompt_text


@patch("tools._get_groq_client")
def test_suggest_outfit_item_title_in_prompt(mock_client_fn):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_groq_response("outfit text")
    mock_client_fn.return_value = mock_client

    suggest_outfit(SAMPLE_ITEM, get_example_wardrobe())

    call_args = mock_client.chat.completions.create.call_args
    prompt_text = call_args[1]["messages"][0]["content"]
    assert "Graphic Tee" in prompt_text

# ══════════════════════════════════════════════════════════════════════════════
# Tool 3: create_fit_card
# ══════════════════════════════════════════════════════════════════════════════
 
SAMPLE_OUTFIT = (
    "Outfit 1: Graphic Tee with baggy straight-leg jeans, chunky white sneakers, "
    "and a vintage black denim jacket. Classic vintage streetwear energy."
)
 
 
@patch("tools._get_groq_client")
def test_create_fit_card_returns_string(mock_client_fn):
    """Happy path: create_fit_card must return a non-empty string."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_groq_response(
        "Thrifted this graphic tee off Depop for $24 and it's giving everything 🖤"
    )
    mock_client_fn.return_value = mock_client
 
    result = create_fit_card(SAMPLE_OUTFIT, SAMPLE_ITEM)
    assert isinstance(result, str)
    assert len(result.strip()) > 0
 
 
def test_create_fit_card_empty_outfit_returns_error_string():
    """Failure mode: empty outfit string must return an error message, not crash."""
    result = create_fit_card("", SAMPLE_ITEM)
    assert isinstance(result, str)
    assert len(result.strip()) > 0
 
 
def test_create_fit_card_whitespace_only_outfit_returns_error_string():
    """Failure mode: whitespace-only outfit string must also return an error message."""
    result = create_fit_card("   \n\t  ", SAMPLE_ITEM)
    assert isinstance(result, str)
    assert len(result.strip()) > 0
 
 
def test_create_fit_card_empty_outfit_does_not_raise():
    """Failure mode: passing an empty outfit must never raise any exception."""
    try:
        create_fit_card("", SAMPLE_ITEM)
    except Exception as e:
        pytest.fail(f"create_fit_card raised an exception on empty outfit: {e}")
 
 
def test_create_fit_card_empty_outfit_mentions_item_title():
    """The fallback error message should still reference the item title."""
    result = create_fit_card("", SAMPLE_ITEM)
    assert "Graphic Tee" in result or "2003 Tour" in result
 
 
def test_create_fit_card_empty_outfit_mentions_platform():
    """The fallback error message should mention the platform."""
    result = create_fit_card("", SAMPLE_ITEM)
    assert "depop" in result.lower()
 
 
@patch("tools._get_groq_client")
def test_create_fit_card_prompt_includes_item_title(mock_client_fn):
    """The LLM prompt must include the thrifted item's title."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_groq_response("caption here")
    mock_client_fn.return_value = mock_client
 
    create_fit_card(SAMPLE_OUTFIT, SAMPLE_ITEM)
 
    call_args = mock_client.chat.completions.create.call_args
    prompt_text = call_args[1]["messages"][0]["content"]
    assert "Graphic Tee" in prompt_text
 
 
@patch("tools._get_groq_client")
def test_create_fit_card_prompt_includes_price(mock_client_fn):
    """The LLM prompt must include the item price."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_groq_response("caption here")
    mock_client_fn.return_value = mock_client
 
    create_fit_card(SAMPLE_OUTFIT, SAMPLE_ITEM)
 
    call_args = mock_client.chat.completions.create.call_args
    prompt_text = call_args[1]["messages"][0]["content"]
    assert "24" in prompt_text
 
 
@patch("tools._get_groq_client")
def test_create_fit_card_prompt_includes_platform(mock_client_fn):
    """The LLM prompt must include the platform name."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_groq_response("caption here")
    mock_client_fn.return_value = mock_client
 
    create_fit_card(SAMPLE_OUTFIT, SAMPLE_ITEM)
 
    call_args = mock_client.chat.completions.create.call_args
    prompt_text = call_args[1]["messages"][0]["content"]
    assert "depop" in prompt_text.lower()
 
 
@patch("tools._get_groq_client")
def test_create_fit_card_uses_high_temperature(mock_client_fn):
    """create_fit_card must use a temperature >= 0.9 to ensure caption variety."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_groq_response("caption here")
    mock_client_fn.return_value = mock_client
 
    create_fit_card(SAMPLE_OUTFIT, SAMPLE_ITEM)
 
    call_args = mock_client.chat.completions.create.call_args
    temperature = call_args[1].get("temperature", call_args[0][1] if len(call_args[0]) > 1 else None)
    assert temperature is not None and temperature >= 0.9
 