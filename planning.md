# FitFindr — planning.md
---

## Tools

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

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**

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

**How does information from one tool get passed to the next?**
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

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

```text
User Input
    |
    v
Planning Loop
    |
    v
Session State
(query, parsed search info, search results, selected item, wardrobe, outfit suggestion, fit card, error)
    |
    v
Parse query into description, size, and max_price
    |
    v
search_listings(description, size, max_price)
    |
    |-- No results found
    |       |
    |       v
    |   Store error message in session
    |       |
    |       v
    |   Return helpful message to user and stop
    |
    |-- Results found
            |
            v
        Store search results in session
            |
            v
        Select top listing as session["selected_item"]
            |
            v
        Check wardrobe
            |
            |-- Wardrobe is empty
            |       |
            |       v
            |   suggest_outfit(selected_item, empty_wardrobe)
            |       |
            |       v
            |   Generate general outfit recommendation
            |
            |-- Wardrobe has missing or incomplete items
            |       |
            |       v
            |   Ignore incomplete wardrobe items
            |       |
            |       v
            |   Use valid wardrobe pieces when possible
            |       |
            |       v
            |   If not enough valid pieces exist, generate general styling advice
            |
            |-- Wardrobe has valid items
                    |
                    v
                suggest_outfit(selected_item, wardrobe)
                    |
                    v
                Generate outfit using specific wardrobe pieces
                    |
                    v
        Store outfit as session["outfit_suggestion"]
            |
            v
        create_fit_card(outfit_suggestion, selected_item)
            |
            |-- Outfit is missing or incomplete
            |       |
            |       v
            |   Generate simplified caption or message
            |
            |-- Outfit is complete
                    |
                    v
                Generate shareable fit card
                    |
                    v
        Store caption as session["fit_card"]
            |
            v
Final Response to User
(top listing + outfit suggestion + fit card)

```

---

## AI Tool Plan

I plan to use Claude to help with implementation, but I will give it specific parts of my planning document instead of asking it to write the whole project at once. I will use Claude mainly to generate first drafts of individual functions and the planning loop, then I will review and test the code myself before using it.

**Milestone 3 — Individual tool implementations:**

For `search_listings()`, I will give Claude the Tool 1 section of `planning.md`, the listings data structure, and the information about `load_listings()` from `utils/data_loader.py`. I expect Claude to produce a Python function that loads the listings, filters by description, size, and maximum price, sorts results by relevance, and returns an empty list if nothing matches. I will verify it by testing one query that returns results, one query with a price limit, and one query that should return no results.

For `suggest_outfit()`, I will give Claude the Tool 2 section of `planning.md`, the wardrobe schema, and the example return value format. I expect Claude to produce a function that takes a selected item and wardrobe dictionary, then returns an outfit dictionary with fields like `top`, `bottom`, `shoes`, and `layer`. I will verify it using both `get_example_wardrobe()` and `get_empty_wardrobe()` to make sure it handles normal and empty wardrobe cases.

For `create_fit_card()`, I will give Claude the Tool 3 section of `planning.md` and example fit card captions. I expect Claude to produce a function that takes the outfit dictionary and selected item, then returns a short social-media-style caption. I will verify that the caption includes the thrifted item, price, platform, and outfit vibe, and that it still returns a simplified caption if the outfit is incomplete.

**Milestone 4 — Planning loop and state management:**

For the planning loop, I will give Claude the Planning Loop section, State Management section, Error Handling section, and Architecture diagram from `planning.md`. I expect Claude to produce the `run_agent()` function in `agent.py` that stores information in a session dictionary and calls the tools in the correct order.

I will verify the planning loop by running a complete query such as `"vintage graphic tee under $30"` and checking that the session stores `selected_item`, `outfit_suggestion`, and `fit_card`. I will also test the no-results path with a query like `"designer ballgown size XXS under $5"` to confirm that the agent stops after `search_listings()` and does not call the later tools.

---

## A Complete Interaction (Step by Step)

Before implementing the agent, I explored the provided datasets and helper functions. I also reviewed the wardrobe schema and understand the difference between the two helper functions:

- `get_example_wardrobe()` returns a sample wardrobe containing 10 clothing items and is useful for testing successful outfit recommendations.
- `get_empty_wardrobe()` returns an empty wardrobe and is useful for testing how the agent behaves when a user has not yet entered any wardrobe information.

---

### Example User Query

> "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

---

### Step 1: Search for Matching Listings

The agent first analyzes the user's request and extracts the key search criteria:

- Item type: **vintage graphic tee**
- Budget: **under $30**
- Style context: **baggy jeans and chunky sneakers**
- Size: **not specified**

The agent then calls the search tool:

```python
search_listings(
    description="vintage graphic tee",
    size=None,
    max_price=30.0
)
```

The tool searches the listings database and returns all matching thrift listings ranked by relevance.

#### Example Return Value

```python
[
    {
        "id": "123",
        "title": "Graphic Tee — 2003 Tour Bootleg Style",
        "price": 24.0,
        "platform": "Depop",
        "condition": "Good"
    },
    ...
]
```

---

### Step 2: Select the Best Listing and Generate an Outfit

The agent examines the search results and selects the highest-ranked listing.

```python
selected_item = {
    "id": "123",
    "title": "Graphic Tee — 2003 Tour Bootleg Style",
    "price": 24.0,
    "platform": "Depop",
    "condition": "Good"
}
```

The selected listing is stored in session state so it can be reused by later tools.

Next, the agent generates an outfit recommendation by combining the new thrifted item with the user's wardrobe.

For testing, the agent uses:

```python
wardrobe = get_example_wardrobe()
```

and calls:

```python
suggest_outfit()
```

The outfit tool analyzes the style of the thrifted item and identifies complementary pieces from the wardrobe.

#### Example Return Value

```text
Pair the Graphic Tee — 2003 Tour Bootleg Style with Baggy Straight-Leg Jeans and Chunky White Sneakers for a relaxed vintage streetwear look. Layer the outfit with the Vintage Black Denim Jacket to add structure and complete the overall style.
```

---

### Step 3: Create a Shareable Fit Card

After generating the outfit, the agent creates a social-media-style fit summary.

It calls:

```python
create_fit_card()
```

#### Example Return Value

```text
"Thrifted this vintage graphic tee off Depop for $24 and styled it with baggy denim, chunky sneakers, and a black denim jacket for an effortless vintage streetwear vibe."
```

The fit card is saved and returned to the user along with the listing and outfit recommendation.

---

## Final Output to User

### Top Listing Found

**Graphic Tee — 2003 Tour Bootleg Style**

- Price: $24
- Platform: Depop
- Condition: Good

### Outfit Suggestion

Pair the graphic tee with:

- Baggy straight-leg jeans
- Chunky white sneakers
- Vintage black denim jacket

This creates an easy vintage streetwear look that matches the user's existing style preferences.

### Fit Card

> "Thrifted this vintage graphic tee off Depop for $24 and styled it with baggy denim, chunky sneakers, and a black denim jacket for an effortless vintage streetwear vibe."

---

## Error Path

### Tool 1: `search_listings`

The primary failure mode for `search_listings()` occurs when no listings match the user's description, size, and price requirements. When this happens, the tool returns an empty result and the agent immediately stops the workflow. Instead of continuing with invalid input, the agent displays a helpful message such as: *"No matching listings found. Try using a broader description, removing the size filter, or increasing your budget."* Because no item was found, the agent does not call `suggest_outfit()` or `create_fit_card()`.

### Tool 2: `suggest_outfit`

The primary failure mode for `suggest_outfit()` occurs when the user's wardrobe is empty, the selected item is missing, or the tool cannot generate a strong outfit recommendation. Rather than failing completely, the tool creates a general styling recommendation using common staple pieces such as jeans, sneakers, jackets, or accessories that would pair well with the selected item. This ensures that the user still receives useful styling advice, and the workflow continues normally to `create_fit_card()`.

### Tool 3: `create_fit_card`

The primary failure mode for `create_fit_card()` occurs when the outfit recommendation is missing or incomplete. In this situation, the tool generates a simplified caption using only the thrifted item information, such as the item name, platform, and price. If there is still not enough information to create a meaningful caption, the tool returns a clear error message explaining that additional outfit information is required to generate a fit card.
