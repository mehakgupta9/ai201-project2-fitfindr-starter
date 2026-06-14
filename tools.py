"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # Replace this with your implementation

    listings = load_listings()

    matches = []

    query_terms = description.lower().split()

    for listing in listings:

        if max_price is not None and listing["price"] > max_price:
            continue

        if size is not None:
            if size.lower() not in listing["size"].lower():
                continue

        relevance = 0

        for term in query_terms:

            relevance += sum(
                term in tag.lower()
                for tag in listing["style_tags"]
            )

            fields = [
                listing["title"],
                listing["description"],
                listing["category"],
            ]

            relevance += sum(
                term in field.lower()
                for field in fields
            )

        if relevance:
            matches.append((relevance, listing))

    matches.sort(reverse=True, key=lambda result: result[0])

    return [listing for _, listing in matches]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation
    client = _get_groq_client()
 
    item_summary = (
        f"Title: {new_item.get('title', 'Unknown item')}\n"
        f"Category: {new_item.get('category', 'unknown')}\n"
        f"Colors: {', '.join(new_item.get('colors', []))}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', []))}\n"
        f"Description: {new_item.get('description', '')}\n"
        f"Condition: {new_item.get('condition', 'unknown')}\n"
        f"Price: ${new_item.get('price', 0):.2f} on {new_item.get('platform', 'unknown platform')}"
    )
 
    wardrobe_items = wardrobe.get("items", [])
 
    # Step 1 & 2: Empty wardrobe → general styling advice
    if not wardrobe_items:
        prompt = (
            "You are a thrift fashion stylist. A user is considering buying this secondhand item:\n\n"
            f"{item_summary}\n\n"
            "They haven't shared their existing wardrobe yet. Give them 1–2 specific outfit ideas "
            "using common wardrobe staples (describe the types of pieces, colors, and silhouettes "
            "that would work well). Keep it casual, specific, and style-savvy — like advice from "
            "a friend who really knows fashion. 3–5 sentences max per outfit idea."
        )
    else:
        # Step 3: Format wardrobe and ask for specific outfit combinations
        wardrobe_lines = []
        for item in wardrobe_items:
            line = (
                f"- {item.get('name', 'item')} "
                f"[{item.get('category', '')}] "
                f"| colors: {', '.join(item.get('colors', []))} "
                f"| tags: {', '.join(item.get('style_tags', []))}"
            )
            if item.get("notes"):
                line += f" | note: {item['notes']}"
            wardrobe_lines.append(line)
 
        wardrobe_text = "\n".join(wardrobe_lines)
 
        prompt = (
            "You are a thrift fashion stylist. A user is considering buying this secondhand item:\n\n"
            f"{item_summary}\n\n"
            "Here is their existing wardrobe:\n"
            f"{wardrobe_text}\n\n"
            "Suggest 1–2 complete outfits using the thrifted item alongside specific pieces "
            "from their wardrobe. Name the exact pieces you're pulling from their wardrobe. "
            "Explain why the combination works in terms of style, color, and silhouette. "
            "Keep it conversational and specific — like advice from a stylish friend. "
            "3–5 sentences per outfit idea."
        )
 
    # Step 4: Call the LLM and return the response
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
    )
 
    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation
    if not outfit or not outfit.strip():
        title = new_item.get("title", "this item")
        platform = new_item.get("platform", "a thrift platform")
        price = new_item.get("price")
        price_str = f"${price:.2f}" if price is not None else "an unknown price"
        return (
            f"Found {title} on {platform} for {price_str}. "
            "A great vintage-inspired piece that can be styled in many different ways. "
            "(Note: full outfit details were unavailable to generate a complete fit card.)"
        )
 
    client = _get_groq_client()
 
    title = new_item.get("title", "a thrifted piece")
    platform = new_item.get("platform", "a thrift platform")
    price = new_item.get("price")
    price_str = f"${price:.2f}" if price is not None else "unknown price"
    colors = ", ".join(new_item.get("colors", []))
    style_tags = ", ".join(new_item.get("style_tags", []))
 
    # Step 2: Build the prompt
    prompt = (
        "You are writing Instagram/TikTok OOTD captions for thrift finds. "
        "Write a 2–4 sentence caption that:\n"
        "- Sounds like a real person posting their outfit, not a product description\n"
        "- Mentions the item name, price, and platform naturally (each exactly once)\n"
        "- Captures the specific vibe of the outfit\n"
        "- Ends with a relevant emoji or two\n\n"
        f"Thrifted item: {title}\n"
        f"Price: {price_str}\n"
        f"Platform: {platform}\n"
        f"Colors: {colors}\n"
        f"Style: {style_tags}\n\n"
        f"Outfit breakdown:\n{outfit}\n\n"
        "Write only the caption — no preamble, no quotation marks around it."
    )
 
    # Step 3: Call the LLM with higher temperature for variety
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,   # Higher temp so repeated calls vary noticeably
        max_tokens=200,
    )
 
    return response.choices[0].message.content.strip()
