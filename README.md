# FitFindr — README.md
---

## Tool Inventory

### Tool 1: search_listings

**What it does:**
Searches the mock secondhand listings dataset for items that match the user's description, preferred size, and maximum budget. It returns the most relevant listings sorted by how well they match the search criteria.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Keywords describing the item the user wants to find (e.g., "vintage graphic tee" or "90s track jacket").
- `size` (str): The user's preferred size. If provided, the search filters listings by size, otherwise it is None. 
- `max_price` (float): The maximum amount the user is willing to spend. Only listings at or below this price are returned. In case the max_price is None, there is no maximum value.

**What it returns:**
A list of listing dictionaries sorted by relevance. Each listing contains:
- `id` (str)
- `title` (str)
- `description` (str)
- `category` (str)
- `style_tags` (list[str])
- `size` (str)
- `condition` (str)
- `price` (float)
- `colors` (list[str])
- `brand` (str or None)
- `platform` (str)

The planning loop selects the first item in the returned list as the `selected_item`.

Example return value:

```python
[{'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}]
```


**What happens if it fails or returns nothing:**
If no listings match the search criteria, the tool returns an empty list. The agent responds with a helpful message such as: *"No matching listings found. Try using a broader description, removing the size filter, or increasing your budget."* The workflow stops at this point and does not call `suggest_outfit()` or `create_fit_card()`.

---

### Tool 2: suggest_outfit

**What it does:**
Generates one or more outfit recommendations using the selected thrifted item and the user's existing wardrobe. This tool uses the Groq LLM to identify wardrobe pieces that complement the new item and suggest complete looks that match the item's style, colors, and overall aesthetic.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The selected listing returned by `search_listings()`. Contains information such as title, description, category, style tags, colors, price, and platform.
- `wardrobe` (dict): A wardrobe dictionary containing an `items` list of wardrobe pieces. Each item includes fields such as name, category, colors, style tags, and optional notes.

**What it returns:**
A string representing a complete outfit recommendation built around the selected thrifted item. The outfit includes specific pieces from the user's wardrobe (when available) organized by clothing category. The outfit suggestion is stored in session state as `outfit_suggestion` and passed directly to `create_fit_card()`.

Example return value:

```text
Pair the Graphic Tee — 2003 Tour Bootleg Style with Baggy Straight-Leg Jeans and Chunky White Sneakers for a relaxed vintage streetwear look. Layer the outfit with the Vintage Black Denim Jacket to add structure and complete the overall style.
```

**What happens if it fails or returns nothing:**
If the wardrobe is empty or there is no matching wardrobe piece for a particular category, the Groq LLM generates general styling advice instead of specific outfit combinations. For example, it may recommend types of pants, shoes, jackets, or accessories that pair well with the thrifted item. The agent continues the workflow and still calls `create_fit_card()`. 

---

### Tool 3: create_fit_card

**What it does:**
Generates a short, shareable outfit caption based on the thrifted item and the outfit recommendation. This tool uses the Groq LLM to create a caption that sounds like a natural social media post rather than a product description. The caption highlights the overall style, aesthetic, and vibe of the outfit while naturally incorporating details about the thrifted item.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (...): The outfit string returned by `suggest_outfit()`, containing clothing pieces (e.g., top, bottom, shoes, layer).
- `new_item` (dict): The selected thrifted item returned by `search_listings()`, including information such as title, price, platform, colors, and style tags.

**What it returns:**
A string containing a short social-media-style caption that references the thrifted item and outfit.
Example return value:

```text
Thrifted this Graphic Tee — 2003 Tour Bootleg Style off Depop for $24 and paired it with baggy denim, chunky sneakers, and a vintage black denim jacket. Easy vintage streetwear energy for everyday wear 🖤
```

The returned caption is stored in session state as `fit_card` and displayed to the user as part of the final response.

**What happens if it fails or returns nothing:**
If the outfit data is missing or incomplete, `create_fit_card()` generates a simplified caption using only the thrifted item information. For example:

```text
Found this Graphic Tee — 2003 Tour Bootleg Style on Depop for $24. A great vintage-inspired piece that can be styled in many different ways.
```

---

## Planning Loop

### Overview

The agent uses a planning loop and a session state dictionary to determine which tool should be called at each stage of the workflow. The session state stores all important information, including the original user query, parsed search parameters, search results, the selected item, the outfit suggestion, the fit card, and any error messages. Before calling a tool, the agent checks whether the required information already exists in the session and whether the previous step completed successfully.

### Step 1: Parse the User Query

The workflow begins by parsing the user's query to extract a description, optional size, and optional maximum price. These values are stored in `session["parsed"]`.

### Step 2: Search for Matching Listings

The agent then calls `search_listings(description, size, max_price)` to find matching items in the listings dataset. After the search completes, the agent checks whether any results were returned. If the results list is empty, the agent stores a helpful error message in `session["error"]` and immediately returns the session to the user. The workflow stops at this point because there is no valid item available for styling. The agent does not call `suggest_outfit()` or `create_fit_card()` with empty input.

### Step 3: Select the Best Listing

If matching listings are found, the agent selects the highest-ranked result and stores it as `session["selected_item"]`. This selected item becomes the input for the next tool.

### Step 4: Generate an Outfit Suggestion

The agent then calls `suggest_outfit(selected_item, wardrobe)` using either the example wardrobe or the empty wardrobe chosen by the user. If the wardrobe contains items, the tool creates an outfit using specific wardrobe pieces. If the wardrobe is empty, the tool generates a generalized outfit recommendation using common staple pieces instead of failing. The resulting outfit string is stored as `session["outfit_suggestion"]`.

### Step 5: Create a Fit Card

Once an outfit suggestion exists, the agent calls `create_fit_card(outfit_suggestion, selected_item)`. This tool uses both the selected thrifted item and the outfit recommendation to generate a short, shareable caption that captures the overall style and vibe of the outfit. The caption is stored as `session["fit_card"]`.

### Step 6: Return the Final Response

The planning loop is complete when all required pieces of information have been successfully generated: a selected item, an outfit suggestion, and a fit card. At that point, the agent returns the completed session and displays the listing, outfit recommendation, and fit card to the user. This approach ensures that each tool only runs when the information it needs is available and prevents later tools from receiving incomplete or invalid input.


---

## State Management

The agent uses a session state dictionary to store and manage information throughout a user interaction. The session acts as a central source of truth that keeps track of all inputs, tool outputs, and any error messages generated during the workflow. This allows information produced by one tool to be reused by later tools without requiring the user to provide the same information again.

### User Query and Parsed Parameters

When the interaction begins, the original user query is stored in the session. The agent then parses the query and extracts the description, optional size, and optional maximum price. These values are stored in `session["parsed"]` and are used as inputs for `search_listings()`.

### Search Results and Selected Item

After `search_listings()` runs, all matching listings are stored in `session["search_results"]`. The agent selects the highest-ranked listing from these results and stores it as `session["selected_item"]`. This selected item becomes the input for the next tool and eliminates the need to search again.

### Outfit Suggestion

The selected item and the user's wardrobe are passed into `suggest_outfit()`. The returned outfit recommendation is stored in `session["outfit_suggestion"]`. This outfit string contains the clothing pieces that make up the recommended look and serves as the input for the fit card generation step.

### Fit Card

The outfit suggestion and selected thrifted item are passed into `create_fit_card()`. The generated caption is stored in `session["fit_card"]`. This is the final piece of information produced by the workflow and is displayed to the user along with the selected listing and outfit recommendation.

### Error Tracking

If any step cannot continue, the agent stores a helpful message in `session["error"]`. For example, if `search_listings()` returns no results, the error message is saved and returned to the user. This prevents later tools from receiving incomplete or invalid input and ensures the workflow remains organized and easy to manage.

### Data Flow Between Tools

The information flows through the session in the following order:

```text
User Query
    ↓
session["parsed"]
    ↓
search_listings()
    ↓
session["search_results"]
    ↓
session["selected_item"]
    ↓
suggest_outfit()
    ↓
session["outfit_suggestion"]
    ↓
create_fit_card()
    ↓
session["fit_card"]
```

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Return a helpful message such as *"No matching listings found. Try using a broader description, removing the size filter, or increasing your budget."* The workflow stops at this point and does not call `suggest_outfit()` or `create_fit_card()`. |
| suggest_outfit | Wardrobe is empty | Generate a general outfit recommendation using common staple pieces instead of specific wardrobe items. For example, recommend jeans, sneakers, or a denim jacket that would pair well with the selected thrifted item. The workflow continues normally and passes the outfit recommendation to `create_fit_card()`. |
| create_fit_card | Outfit input is missing or incomplete | Generate a simplified caption using only the thrifted item information. For example: *"Found this Graphic Tee — 2003 Tour Bootleg Style on Depop for $24. A great vintage-inspired piece that can be styled in many different ways."* If a caption still cannot be generated, return a helpful error message explaining that there was not enough outfit information available to create a fit card. |


Each tool in FitFindr includes its own error handling to ensure the agent remains useful even when a tool cannot produce its normal output. Rather than crashing or passing invalid data to the next step, each tool returns a meaningful response that allows the workflow to either stop safely or continue with a fallback strategy.

### Tool 1: `search_listings`

The primary failure mode for `search_listings()` occurs when no listings match the user's search criteria. In this case, the function returns an empty list instead of raising an exception.

**Example test:**

```python
search_listings("designer ballgown", size="XXS", max_price=5)
```

**Result:**

```python
[]
```

**Agent response:**

When no results are found, the agent stores an error message in `session["error"]` and stops the workflow immediately. A helpful message is returned to the user:

> "No matching listings found. Try using a broader description, removing the size filter, or increasing your budget."

The agent does **not** call `suggest_outfit()` or `create_fit_card()` because there is no valid item available for styling.

---

### Tool 2: `suggest_outfit`

The primary failure mode for `suggest_outfit()` occurs when the user has an empty wardrobe or there are not enough wardrobe items available to create a complete outfit.

**Example test:**

```python
from utils.data_loader import get_empty_wardrobe

suggest_outfit(selected_item, get_empty_wardrobe())
```

**Input wardrobe:**

```python
{
    "items": []
}
```

**Agent response:**

Instead of failing, the tool generates general styling advice using common wardrobe staples such as jeans, sneakers, jackets, or accessories that would pair well with the thrifted item. This ensures that new users without a saved wardrobe can still receive useful recommendations.

The workflow continues normally and passes the generated styling advice to `create_fit_card()`.

**Example output:**

```text
For a laid-back vibe, pair this graphic tee with a pair of high-waisted, straight-leg jeans and some sleek black sneakers. The slightly boxy fit of the tee will be balanced by the fitted silhouette of the jeans, creating a cool, effortless look. Add a trendy denim jacket or a faux leather jacket to elevate the outfit and give it a bit of an edge. This is a great way to dress down the tee while still looking put-together.

Alternatively, style the graphic tee with a flowy, neutral-colored skirt, like a beige or gray midi skirt, and a pair of combat boots for a grunge-inspired look. The flowy skirt will add a feminine touch to the overall outfit, while the combat boots will keep it grounded and edgy. A chunky belt or a floppy hat can add a fun, eclectic touch to the look, tying in with the vintage vibe of the tee.
```

---

### Tool 3: `create_fit_card`

The primary failure mode for `create_fit_card()` occurs when the outfit recommendation is missing or incomplete.

**Example test:**

```python
create_fit_card("", selected_item)
```

**Agent response:**

Rather than raising an error, the tool generates a simplified caption using only the thrifted item information, such as the item title, platform, and price.

**Example output:**

```text
Found this Graphic Tee — 2003 Tour Bootleg Style on Depop for $24. A great vintage-inspired piece that can be styled in many different ways.
```

If there is still not enough information to generate a caption, the tool returns a clear error message explaining that additional outfit information is required.

---

### Summary

These error-handling strategies ensure that FitFindr remains reliable and user-friendly. If no listings are found, the workflow stops with a helpful suggestion. If the wardrobe is empty, the agent falls back to general styling advice. If outfit information is incomplete, the agent generates a simplified fit card instead of failing. This prevents crashes, avoids passing invalid data between tools, and ensures that users always receive a meaningful response.

---

## Spec Reflection

### One way the spec helped me during implementation:

The spec provided a clear structure for the entire agent workflow before any code was written. Defining each tool's inputs, outputs, and failure modes in advance made it much easier to implement the functions because I always knew what information each tool needed and what it should return. The Planning Loop and State Management sections were especially helpful because they served as a blueprint for implementing `run_agent()` and ensured that information flowed correctly between tools.

### One way my implementation diverged from the spec, and why:

One difference between my initial design and the final implementation was the output format of `suggest_outfit()`. During planning, I originally considered returning a structured outfit dictionary containing fields such as `top`, `bottom`, `shoes`, and `layer`. However, after reviewing the starter code and function signature, I implemented the tool to return a descriptive string instead. This better matched the provided interface, simplified the interaction with `create_fit_card()`, and aligned with the expected return type in the starter repository.

---

## AI Usage

### Instance 1

- **What I gave the AI:**  
  I provided the Tool 1 (`search_listings`) specification from `planning.md`, including the tool description, input parameters, expected return value, and failure mode. I also shared information about the listings dataset structure and the `load_listings()` helper function from `utils/data_loader.py`.

- **What it produced:**  
  The AI generated an implementation of `search_listings()` that loaded the listings dataset, filtered results by size and maximum price, scored listings using keyword overlap with the user's description, and returned the matching listings sorted by relevance.

- **What I changed or overrode:**  
  I reviewed and modified the scoring logic to better prioritize relevant listings and ensured that the function returned an empty list when no matches were found. I also verified that the size filtering was case-insensitive and matched partial sizes such as `"M"` matching `"S/M"`.

---

### Instance 2

- **What I gave the AI:**  
  I provided the Planning Loop, State Management, Error Handling, and Architecture sections from `planning.md`, including the agent diagram showing how information should flow between `search_listings()`, `suggest_outfit()`, `create_fit_card()`, and the session state dictionary.

- **What it produced:**  
  The AI generated a first version of the `run_agent()` planning loop that parsed the user query, called the tools in sequence, and stored results in the session dictionary.

- **What I changed or overrode:**  
  I updated the query parsing logic to correctly extract the description, size, and maximum price from user input using regular expressions. I also added the early-return error path so that if `search_listings()` returned no results, the agent stopped the workflow and did not call `suggest_outfit()` or `create_fit_card()`. Finally, I verified that state was passed correctly through `session["selected_item"]`, `session["outfit_suggestion"]`, and `session["fit_card"]`.
