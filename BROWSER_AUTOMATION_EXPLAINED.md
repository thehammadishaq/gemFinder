# Browser Automation via Gemini - Complete Explanation

## 📋 Project Overview

**gemFinder** is a FastAPI-based application that scrapes company profile data from Google's Gemini AI interface using browser automation. The system uses Playwright to interact with Gemini's web UI, extract JSON responses, and store them in MongoDB.

---

## 🏗️ Architecture Flow

```
API Request → Controller → Service → Playwright Browser → Gemini UI → Response Extraction → JSON Parsing → Database
```

### Component Breakdown:

1. **API Route** (`routes/gemini_routes.py`)
   - Receives HTTP requests (POST/GET)
   - Validates input (ticker symbol)
   - Calls controller

2. **Controller** (`controllers/gemini_controller.py`)
   - Thin wrapper around service
   - Handles errors and returns formatted responses

3. **Service** (`services/gemini_scraper_service.py`)
   - **Core browser automation logic**
   - Uses Playwright to control browser
   - Extracts data from Gemini UI

---

## 🔍 Browser Automation Deep Dive

### **Entry Point: `fetch_company_profile_from_gemini(ticker: str)`**

This is the main async function that orchestrates the entire browser automation process.

#### **Step 1: Browser Launch (Lines 882-888)**
```python
async with async_playwright() as p:
    browser = await p.chromium.launch_persistent_context(
        user_data_dir=SESSION_PATH,  # Persists login session
        headless=HEADLESS,            # Can run with/without GUI
        args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
    )
```

**Key Features:**
- **Persistent Context**: Uses `x_browser_session_gemini_company/` directory to save browser session
  - **Why?** So you don't have to log in every time - session persists between runs
- **Headless Mode**: Can run without visible browser (controlled by `GEMINI_HEADLESS` env var)
- **Anti-Detection**: `--disable-blink-features=AutomationControlled` helps avoid bot detection

#### **Step 2: Navigate to Gemini (Lines 889-893)**
```python
page = await browser.new_page()
await page.goto("https://gemini.google.com/app", timeout=60000)
await async_human_wait(2.0, 3.5)  # Human-like delay
```

**Human-like Behavior:**
- Random delays between actions (`async_human_wait`)
- Simulates real user interaction patterns

#### **Step 3: Check Login Status (Lines 895-898)**
```python
if "accounts.google.com" in (page.url or "").lower():
    print(f"⚠️ Please log in manually; session will persist.")
    await async_human_wait(10.0, 10.0)  # Wait for manual login
```

**Note:** First run requires manual login. After that, session persists.

#### **Step 4: Construct Query (Lines 900-952)**
Creates a comprehensive JSON-structured prompt asking Gemini for company profile data with specific structure:
- **What**: Sector, Industry, Description, Products
- **When**: Founded, IPO, Milestones
- **Where**: Headquarters, Locations
- **How**: Business Model, Revenue Streams
- **Who**: CEO, Leadership, Founders

#### **Step 5: Find Input Box (Lines 954-978)**
Uses multiple selector strategies to find the message input:
```python
selectors = [
    "textarea[aria-label*='Message' i]",
    "textarea[aria-label*='Ask Gemini' i]",
    "textarea",
    "div[contenteditable='true']",
    # ... more fallbacks
]
```

**Why multiple selectors?** Gemini UI can change, so this provides resilience.

#### **Step 6: Human-like Typing (Lines 980-1008)**
```python
await human_click(page, input_box)  # Realistic mouse movement
await human_type(input_box, query)  # Character-by-character typing
await page.keyboard.press("Enter")
```

**Human Simulation Functions:**

1. **`human_click(page, el)`** (Lines 81-98):
   - Uses Bézier curve interpolation for mouse movement
   - Random start position, smooth curved path to target
   - Simulates real mouse click with down/up events

2. **`human_type(el, text)`** (Lines 50-56):
   - Types character-by-character with random delays (20-80ms)
   - Occasionally pauses (5% chance) to simulate thinking
   - Avoids instant paste detection

3. **`human_move_mouse(mouse, start, end, steps=30)`** (Lines 64-78):
   - Bézier curve interpolation for smooth, curved mouse paths
   - Adds random jitter to make movement look natural
   - Not a straight line (humans don't move in straight lines)

#### **Step 7: Wait for Response (Lines 1010-1011)**
```python
await async_human_wait(5.0, 8.0)  # Wait for Gemini to start generating
```

#### **Step 8: Extract Response (Lines 1013-1037)**

**Three-tier extraction strategy** (tries each method in order):

##### **Method 1: Direct DOM Extraction** (`get_json_directly_from_dom`)
- **Lines 354-477**
- Targets specific Gemini response selectors:
  ```python
  json_selectors = [
      "model-response message-content.model-response-text .markdown p",
      "model-response message-content.model-response-text p",
      # ... more selectors
  ]
  ```
- **How it works:**
  1. Waits for response elements to appear
  2. Extracts text from latest response element
  3. Validates it's JSON (starts with `{`, has expected keys)
  4. **Stability check**: Waits for text to stabilize (not changing) before returning
  5. Returns raw JSON string

##### **Method 2: Copy Button Method** (`get_response_via_copy_button`)
- **Lines 480-630**
- **How it works:**
  1. Finds the "Copy" button in the response
  2. Clicks it to copy response to clipboard
  3. Reads from clipboard using:
     - Browser's `navigator.clipboard.readText()` API (preferred)
     - Falls back to `pyperclip` library if browser API fails
  4. Validates clipboard content (not prompt, has minimum length)
  5. Returns clipboard text

##### **Method 3: DOM Scraping Fallback** (`scrape_gemini_response`)
- **Lines 633-716**
- **Most robust but slowest method**
- **How it works:**
  1. Uses **60+ CSS selectors** to find response text (Lines 206-268)
  2. Collects text from all matching elements
  3. **Deep shadow DOM traversal** (Lines 314-341):
     - Recursively traverses shadow roots
     - Extracts text from hidden/nested elements
  4. **Text cleaning pipeline:**
     - `strong_clean()`: Removes HTML, scripts, boilerplate (Lines 125-148)
     - `dedupe_sentences()`: Removes duplicate sentences (Lines 165-202)
     - Filters out JavaScript garbage (Lines 112-122)
  5. **Stability check**: Waits until text doesn't change for `STABILIZE_SECONDS` (7 seconds)
  6. **Selector memory**: Saves working selectors to `working_selectors_company.json` for faster future runs

#### **Step 9: JSON Parsing (Lines 1055-1196)**

**Multi-stage parsing strategy:**

1. **Direct JSON parse** (Lines 1076-1090):
   - Try parsing cleaned response directly
   - Handles nested JSON (if response is `{"Response": "{...}"}`)

2. **Escaped JSON handling** (Lines 1092-1099):
   - Handles cases where JSON is wrapped in quotes: `"{\"key\": \"value\"}"`
   - Unescapes and parses

3. **Extract from text** (`extract_and_parse_json`, Lines 719-832):
   - Finds JSON in code blocks: ` ```json {...} ``` `
   - Finds JSON between braces (handles nested braces correctly)
   - Handles multiple JSON candidates, picks the best one

4. **Validation** (Lines 1108-1138):
   - Checks for expected keys: `['What', 'When', 'Where', 'How', 'Who']`
   - Requires at least 3 of 5 sections
   - If incomplete, tries to find complete JSON by matching braces

#### **Step 10: Return Result**
Returns parsed JSON dictionary or `None` if failed.

---

## 🎯 Key Design Patterns

### **1. Human-like Behavior**
- **Random delays**: `rand(0.3, 1.2)` seconds between actions
- **Curved mouse movement**: Bézier interpolation, not straight lines
- **Character-by-character typing**: Not instant paste
- **Micro-pauses**: Occasional pauses during typing

### **2. Resilience & Fallbacks**
- **Multiple extraction methods**: If one fails, try next
- **60+ CSS selectors**: If UI changes, other selectors may still work
- **Selector memory**: Saves working selectors for faster future runs
- **Multiple JSON parsing strategies**: Handles various response formats

### **3. Anti-Detection**
- **Persistent session**: Avoids repeated logins (looks more human)
- **Human-like timing**: Random delays, not fixed intervals
- **Natural mouse movement**: Curved paths, not robotic straight lines
- **Browser flags**: `--disable-blink-features=AutomationControlled`

### **4. Text Cleaning Pipeline**
```
Raw HTML → Remove Scripts/Styles → Remove HTML Tags → 
Filter JS Garbage → Deduplicate Sentences → Extract JSON
```

### **5. Stability Checks**
- Waits for response text to stabilize (not changing)
- Multiple stability checks before returning
- Prevents returning partial/incomplete responses

---

## 🔧 Configuration

### **Environment Variables:**
- `GEMINI_HEADLESS`: Set to `"false"` to see browser (default: `"true"`)
- `DISPLAY`: If not set, forces headless mode (for servers without X server)

### **File Paths:**
- **Session**: `backend/x_browser_session_gemini_company/` (persists login)
- **Selector Memory**: `backend/working_selectors_company.json` (saves working selectors)

### **Constants:**
- `STABILIZE_SECONDS = 7`: How long to wait for text to stabilize
- `MIN_ACCEPT_CHARS = 300`: Minimum response length to accept
- `MOUSE_STEP_MS = 6`: Mouse movement step delay

---

## 🚀 Usage Flow Example

1. **API Request:**
   ```bash
   POST /api/v1/gemini/fetch-profile
   {"ticker": "AAPL", "save_to_db": true}
   ```

2. **Controller** (`gemini_controller.py`):
   ```python
   profile_data = await fetch_company_profile_from_gemini("AAPL")
   ```

3. **Service** (`gemini_scraper_service.py`):
   - Launches browser (or reuses session)
   - Navigates to Gemini
   - Types query with human-like behavior
   - Waits for response
   - Extracts JSON using 3 methods
   - Parses and validates JSON
   - Returns dictionary

4. **Response:**
   ```json
   {
     "What": {"Sector": "...", "Industry": "..."},
     "When": {"FoundedYear": "...", ...},
     "Where": {"Headquarters": "...", ...},
     "How": {"BusinessModel": "...", ...},
     "Who": {"CEO": "...", ...}
   }
   ```

---

## 🐛 Windows Compatibility

Special handling for Windows (Lines 15-17, 835-871):
- Uses `WindowsProactorEventLoopPolicy` for Playwright compatibility
- Can run in separate thread with new event loop if needed
- Handles Windows-specific async issues

---

## 📊 Performance Characteristics

- **First run**: ~60-120 seconds (includes login if needed)
- **Subsequent runs**: ~30-60 seconds (session persists)
- **Headless mode**: Slightly faster (no rendering)
- **Extraction method speed**: Direct DOM > Copy Button > DOM Scraping

---

## 🔐 Security & Privacy

- **Session persistence**: Login credentials stored in browser session directory
- **No API keys**: Uses UI scraping, not official API
- **Rate limiting**: None built-in (relies on Gemini's own rate limits)
- **Headless mode**: Recommended for production servers

---

## 🎓 Key Takeaways

1. **This is UI scraping, not API access** - Uses Playwright to interact with Gemini's web interface
2. **Human-like behavior is crucial** - Random delays, curved mouse movement, character typing
3. **Multiple fallback strategies** - Three extraction methods, 60+ selectors, multiple JSON parsers
4. **Session persistence** - Saves login so you don't have to authenticate every time
5. **Robust text extraction** - Handles shadow DOM, nested elements, dynamic content
6. **Stability checks** - Waits for complete responses, not partial ones

---

## 🔄 Similar Pattern for Fundamentals

The same architecture is used for fundamentals scraping:
- `services/gemini_fundamentals_scraper_service.py` (similar structure)
- `controllers/fundamentals_controller.py`
- Uses separate session: `x_browser_session_gemini_fundamentals/`

