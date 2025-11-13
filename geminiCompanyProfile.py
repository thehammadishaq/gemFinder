# -*- coding: utf-8 -*-
"""
Gemini UI Scraper for Company Profile Data

- Uses Gemini AI to fetch comprehensive company profile information
- Extracts: What, When, Where, How, Who sections
- Human-like browser automation with Playwright
- Structured data extraction from Gemini responses
"""

from playwright.sync_api import sync_playwright
import time, random, os, sys, json, re
from typing import Dict, Optional

# ---------- CONFIG ----------
session_path = "x_browser_session_gemini_company"
headless = False
CHROME_PATH = None
OUTPUT_FILE = "gemini_company_profile_{TICKER}.json"
MOUSE_STEP_MS = 6
SELECTOR_MEMORY_FILE = "working_selectors_company.json"
STABILIZE_SECONDS = 7
MIN_ACCEPT_CHARS = 300
# ----------------------------


# ---------- Human-like behavior ----------
def rand(a, b): return random.uniform(a, b)
def human_wait(a=0.3, b=1.2): time.sleep(rand(a, b))

def human_type(el, text):
    """Type text character-by-character with random micro-delays."""
    for ch in text:
        el.type(ch, delay=int(rand(20, 80)))
        if random.random() < 0.05:
            time.sleep(rand(0.1, 0.4))

def bezier_interp(p0, p1, p2, p3, t):
    x = ((1 - t)**3)*p0[0] + 3*((1 - t)**2)*t*p1[0] + 3*(1 - t)*(t**2)*p2[0] + (t**3)*p3[0]
    y = ((1 - t)**3)*p0[1] + 3*((1 - t)**2)*t*p1[1] + 3*(1 - t)*(t**2)*p2[1] + (t**3)*p3[1]
    return x, y

def human_move_mouse(mouse, start, end, steps=30):
    """Smooth curved mouse movement using Bézier interpolation."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    p0, p1, p2, p3 = start, (
        start[0] + dx * rand(0.2, 0.4) + rand(-50, 50),
        start[1] + dy * rand(0.2, 0.4) + rand(-50, 50)
    ), (
        start[0] + dx * rand(0.6, 0.8) + rand(-50, 50),
        start[1] + dy * rand(0.6, 0.8) + rand(-50, 50)
    ), end
    for i in range(steps):
        t = i / float(steps - 1)
        x, y = bezier_interp(p0, p1, p2, p3, t)
        mouse.move(x + rand(-1.2, 1.2), y + rand(-1.2, 1.2))
        time.sleep(MOUSE_STEP_MS / 1000.0)

def human_click(page, el):
    """Perform a realistic mouse click on an element."""
    try: el.scroll_into_view_if_needed(timeout=4000)
    except: pass
    box = el.bounding_box()
    if not box: return
    start = (rand(100, 400), rand(100, 400))
    target = (box["x"] + rand(5, box["width"] - 5),
              box["y"] + rand(5, box["height"] - 5))
    human_move_mouse(page.mouse, start, target, steps=random.randint(25, 45))
    human_wait(0.05, 0.3)
    page.mouse.down()
    human_wait(0.02, 0.08)
    page.mouse.up()
# ------------------------------------------


# ---------- Cleaner ----------
BANNED_PATTERNS = [
    r"^\s*\(function", r"use strict", r"const\s", r"let\s", r"var\s", r"class\s",
    r"throw\s+Error", r"theme-host", r"google-sans", r"old-google-sans",
    r"Sign in", r"Saving your chats", r"Sources\s", r"Gemini can make mistakes",
    r"Once you'?re signed in", r"iframe\s+src=", r"gbar_",
    r"window\.", r"document\.", r"try\s*\{", r"catch\s*\(", r"\.prototype\.",
    r"export\s+default", r"import\s+"
]
BANNED_REGEX = re.compile("|".join(BANNED_PATTERNS), re.IGNORECASE)

def looks_like_js_garbage(s: str) -> bool:
    if not s or len(s) < 40:
        return True
    punct = sum(s.count(ch) for ch in "{}();[]=<>")
    if punct > max(12, len(s) // 30):
        return True
    if BANNED_REGEX.search(s):
        return True
    if "theme" in s and "google" in s and "sans" in s:
        return True
    return False

def strong_clean(text: str) -> str:
    """Remove HTML, scripts, boilerplate, and duplicates."""
    if not text:
        return ""
    text = re.sub(r"(?is)<script.*?>.*?</script>", "", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", "", text)
    text = re.sub(r"(?is)<.*?>", "", text)
    text = re.sub(r"(?is)Sign in.*?(?:\n|$)", " ", text)
    text = re.sub(r"(?is)Sources:?.*", " ", text)
    text = re.sub(r"(?is)Gemini can make mistakes.*", " ", text)
    text = re.sub(r"(?is)Once you'?re signed in.*", " ", text)
    text = re.sub(r"(?is)\(function.*?use strict.*?\)", " ", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    seen, out = set(), []
    for l in lines:
        if looks_like_js_garbage(l):
            continue
        if l in seen:
            continue
        seen.add(l)
        out.append(l)
    text = " ".join(out)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text
# ---------- Sentence-level de-duplication ----------
SENT_SEP_REGEX = re.compile(
    r'(?<=[.?!])\s+(?=[A-Z0-9"(\[])|(?<=\n)\s+'
)

def _normalize_sentence(s: str) -> str:
    s2 = s.strip()
    s2 = re.sub(r"\s+", " ", s2)
    # Remove various quote types and punctuation
    s2 = s2.strip('"""\'`•–- ').lower()
    s2 = s2.replace(",", "")
    return s2

def dedupe_sentences(text: str) -> str:
    """Remove duplicate or near-duplicate sentences."""
    if not text:
        return text
    splits = SENT_SEP_REGEX.split(text)
    tmp = []
    for chunk in splits:
        if not chunk:
            continue
        sub = re.split(r'(?:(?<=\:)|(?<=\)))(?=\s+)|(?<=\n)|(?<=—)\s+', chunk)
        for s in sub:
            if s and s.strip():
                tmp.append(s.strip())
    seen = set()
    out = []
    for s in tmp:
        sub_sents = re.split(r'(?<=;)\s+|(?<=—)\s+|(?<=–)\s+', s)
        if len(sub_sents) > 1:
            for ss in sub_sents:
                _norm = _normalize_sentence(ss)
                if not _norm or len(_norm) < 5:
                    continue
                if _norm in seen:
                    continue
                seen.add(_norm)
                out.append(ss.strip())
        else:
            _norm = _normalize_sentence(s)
            if not _norm or len(_norm) < 5:
                continue
            if _norm in seen:
                continue
            seen.add(_norm)
            out.append(s.strip())
    cleaned = " ".join(out)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned
# ----------------------------------------------------


# ---------- Selector Set ----------
BASE_SELECTORS = list(dict.fromkeys([
    # Direct Gemini JSON response selectors (highest priority)
    "model-response message-content.model-response-text .markdown p",
    "model-response message-content.model-response-text p",
    "model-response message-content p",
    "message-content.model-response-text .markdown p",
    "message-content.model-response-text p",
    "response-container message-content p",
    # Gemini response container selectors
    "model-response",
    "response-container",
    "message-content.model-response-text",
    # Legacy selectors
    "div[data-message-author='ai']",
    "[data-message-author='ai']",
    "div[aria-live='polite']",
    "div[aria-live='assertive']",
    "[role='feed'] [role='article']",
    "article[aria-live]",
    "article[role='article']",
    "div[role='article']",
    "div[role='region'][aria-live]",
    "section[role='region'][aria-live]",
    "section[aria-live]",
    "div[role='main'] div[aria-live]",
    "main [aria-live]",
    "cib-response",
    "cib-serp",
    "chat-message[role='response']",
    "chat-message[data-author='ai']",
    "chat-turn",
    "chat-ui",
    "chat-line",
    "md-content",
    "md-output",
    "md-block",
    "div[class*='markdown' i]",
    "section[class*='markdown' i]",
    "span[class*='markdown' i]",
    "div[class*='prose' i]",
    "div[class*='content' i]",
    "div[class*='response' i]",
    "section[class*='response' i]",
    "div[class*='output' i]",
    "div[class*='assistant' i]",
    "div[class*='answer' i]",
    "div[class*='message' i]",
    "div[class*='msg' i]",
    "div[class*='ai' i]",
    "[aria-label*='response' i]",
    "[aria-label*='assistant' i]",
    "[aria-label*='answer' i]",
    "[aria-label*='message' i]",
    "article",
    "section",
    "div[dir='auto']",
    "div[role='region']",
    "div[role='main']",
    "main",
    "p",
    "pre",
    "code"
]))
# ----------------------------------------------------


# ---------- Core Scraper ----------
def collect_text_candidates(page, selectors):
    texts = []
    for sel in selectors:
        try:
            els = page.query_selector_all(sel)
            if not els:
                continue
            for el in els:
                try:
                    if not el or not el.is_visible():
                        continue
                    
                    # Skip input fields, textareas, and contenteditable elements (these contain the prompt, not response)
                    tag_name = (el.evaluate("el => el.tagName") or "").upper()
                    is_contenteditable = el.evaluate("el => el.contentEditable === 'true'") or False
                    is_input = tag_name in ("INPUT", "TEXTAREA")
                    role = (el.get_attribute("role") or "").lower()
                    
                    # Skip input elements and contenteditable that might be input fields
                    if is_input or (is_contenteditable and role in ("textbox", "combobox")):
                        continue
                    if role in ("navigation", "banner", "complementary", "contentinfo"):
                        continue
                    
                    t = el.inner_text().strip()
                    if not t or len(t) < 40 or looks_like_js_garbage(t):
                        continue
                    
                    # Skip if text looks like a prompt (contains prompt keywords)
                    prompt_indicators = [
                        "Provide a complete and comprehensive",
                        "Return ONLY valid JSON",
                        "Return ONLY the JSON object"
                    ]
                    if any(indicator in t for indicator in prompt_indicators) and len(t) < 500:
                        continue
                    
                    texts.append(t)
                except:
                    continue
        except:
            continue
    return texts


def deep_shadow_text(page) -> str:
    try:
        return page.evaluate("""() => {
            function visible(e){
                const st = (el)=>getComputedStyle(el);
                if(!e || !(e instanceof Element)) return false;
                const s = st(e);
                if (s && (s.visibility === 'hidden' || s.display === 'none' || parseFloat(s.opacity||'1') < 0.05)) return false;
                const r = e.getBoundingClientRect();
                if ((r.width===0 && r.height===0) || (r.bottom < 0) || (r.right < 0)) return false;
                return true;
            }
            function deepText(e){
                if(!e) return '';
                let t='';
                if(e.shadowRoot) t+=deepText(e.shadowRoot);
                for(const n of e.childNodes){
                    if(n.nodeType===Node.TEXT_NODE) t+=n.textContent;
                    else if(n.nodeType===Node.ELEMENT_NODE){
                        if(visible(n)) t+=deepText(n);
                    }
                }
                return t;
            }
            return deepText(document.body);
        }""")
    except:
        return ""


def stabilize_text(current: str, last: str, stable_since: float):
    """Return updated stability state for response text."""
    now = time.time()
    if current != last:
        return current, now, False
    if now - stable_since >= STABILIZE_SECONDS:
        return last, stable_since, True
    return last, stable_since, False


def get_json_directly_from_dom(page, user_prompt: str, timeout_ms=60000) -> Optional[str]:
    """Extract JSON directly from DOM using specific selectors - fastest method."""
    print("📋 Attempting to extract JSON directly from DOM...")
    
    start = time.time()
    user_prompt_clean = user_prompt.strip()
    
    # Direct JSON selectors (highest priority)
    json_selectors = [
        "model-response message-content.model-response-text .markdown p",
        "model-response message-content.model-response-text p",
        "model-response message-content p",
        "message-content.model-response-text .markdown p",
        "message-content.model-response-text p",
        "response-container message-content p",
    ]
    
    print("⏳ Waiting for Gemini JSON response to appear...")
    
    # Wait a bit before starting to check (give Gemini time to start generating)
    time.sleep(3.0)
    
    while (time.time() - start) * 1000 < timeout_ms:
        try:
            # Try each selector in priority order
            for selector in json_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        # Get the last/most recent element (latest response)
                        latest_element = elements[-1]
                        if latest_element and latest_element.is_visible():
                            json_text = latest_element.inner_text().strip()
                            
                            # Verify it's not the prompt
                            if user_prompt_clean in json_text or json_text == user_prompt_clean:
                                continue
                            
                            # Check if it looks like JSON
                            if json_text.startswith('{') and len(json_text) > MIN_ACCEPT_CHARS:
                                # Wait longer to ensure response is complete (Gemini might still be generating)
                                time.sleep(5.0)
                                
                                # Re-check multiple times to ensure it's stable and complete
                                stable_count = 0
                                last_json_text = json_text
                                for _ in range(3):
                                    time.sleep(2.0)
                                    elements = page.query_selector_all(selector)
                                    if elements:
                                        latest_element = elements[-1]
                                        current_json_text = latest_element.inner_text().strip()
                                        
                                        # Check if response is still growing
                                        if current_json_text == last_json_text:
                                            stable_count += 1
                                        else:
                                            stable_count = 0
                                            last_json_text = current_json_text
                                        
                                        # If stable for 2 checks, response is likely complete
                                        if stable_count >= 2:
                                            json_text = current_json_text
                                            break
                                        json_text = current_json_text
                                
                                # Final verification - check if it has expected structure
                                if json_text.startswith('{') and user_prompt_clean not in json_text and len(json_text) > MIN_ACCEPT_CHARS:
                                    # Quick check: try to parse and verify it has expected keys
                                    try:
                                        test_parse = json.loads(json_text)
                                        if isinstance(test_parse, dict):
                                            expected_keys = ['What', 'When', 'Where', 'How', 'Who']
                                            # If it has at least 3 expected keys, it's likely complete
                                            if sum(1 for key in expected_keys if key in test_parse) >= 3:
                                                print("✅ Successfully extracted complete JSON directly from DOM!")
                                                return json_text
                                            # If response is very long, it might be complete even without all keys
                                            elif len(json_text) > 2000:
                                                print("✅ Successfully extracted JSON directly from DOM!")
                                                return json_text
                                    except:
                                        pass
                                    
                                    # If parsing fails but text looks good, return it anyway
                                    if len(json_text) > 500:
                                        print("✅ Successfully extracted JSON directly from DOM!")
                                        return json_text
                except:
                    continue
            
            # Also try response container selectors - get complete message-content
            response_elements = page.query_selector_all("model-response, response-container")
            if response_elements:
                latest_response = response_elements[-1]
                # Try to get complete message-content text (not just p tag)
                try:
                    message_content = latest_response.query_selector("message-content.model-response-text")
                    if message_content and message_content.is_visible():
                        json_text = message_content.inner_text().strip()
                        if json_text.startswith('{') and user_prompt_clean not in json_text and len(json_text) > MIN_ACCEPT_CHARS:
                            # Wait and check for stability
                            time.sleep(5.0)
                            stable_count = 0
                            last_json_text = json_text
                            for _ in range(3):
                                time.sleep(2.0)
                                current_json_text = message_content.inner_text().strip()
                                if current_json_text == last_json_text:
                                    stable_count += 1
                                else:
                                    stable_count = 0
                                    last_json_text = current_json_text
                                if stable_count >= 2:
                                    json_text = current_json_text
                                    break
                                json_text = current_json_text
                            
                            # Verify it has expected structure
                            if json_text.startswith('{') and len(json_text) > MIN_ACCEPT_CHARS:
                                try:
                                    test_parse = json.loads(json_text)
                                    if isinstance(test_parse, dict):
                                        expected_keys = ['What', 'When', 'Where', 'How', 'Who']
                                        if sum(1 for key in expected_keys if key in test_parse) >= 3 or len(json_text) > 2000:
                                            print("✅ Successfully extracted complete JSON directly from DOM!")
                                            return json_text
                                except:
                                    if len(json_text) > 500:
                                        print("✅ Successfully extracted JSON directly from DOM!")
                                        return json_text
                except:
                    pass
                
                # Fallback: Try to find JSON within it using selectors
                for selector in json_selectors:
                    try:
                        json_element = latest_response.query_selector(selector)
                        if json_element and json_element.is_visible():
                            json_text = json_element.inner_text().strip()
                            if json_text.startswith('{') and user_prompt_clean not in json_text and len(json_text) > MIN_ACCEPT_CHARS:
                                time.sleep(5.0)  # Wait longer for stability
                                json_text = json_element.inner_text().strip()
                                if json_text.startswith('{') and len(json_text) > MIN_ACCEPT_CHARS:
                                    print("✅ Successfully extracted JSON directly from DOM!")
                                    return json_text
                    except:
                        continue
        except:
            pass
        
        time.sleep(1.0)
    
    print("⚠️ Direct JSON extraction failed. Trying copy button method...")
    return None


def get_response_via_copy_button(page, user_prompt: str, timeout_ms=120000) -> Optional[str]:
    """Get Gemini response by clicking copy button and reading from clipboard. Ensures only response is copied, not user prompt."""
    print("📋 Attempting to get response via copy button...")
    
    start = time.time()
    user_prompt_clean = user_prompt.strip()
    
    # Wait for response to appear
    print("⏳ Waiting for Gemini response to appear...")
    
    # Wait a bit before starting to check (give Gemini time to start generating)
    time.sleep(3.0)
    
    latest_response_element = None
    
    while (time.time() - start) * 1000 < timeout_ms:
        try:
            # Step 1: Find latest Gemini response element using multiple selectors
            # Try different selectors based on Gemini UI structure
            response_elements = None
            
            # Method 1: Try model-response tag (Angular component)
            response_elements = page.query_selector_all("model-response")
            
            # Method 2: If not found, try response-container
            if not response_elements or len(response_elements) == 0:
                response_elements = page.query_selector_all("response-container")
            
            # Method 3: If still not found, try message-content with model-response-text class
            if not response_elements or len(response_elements) == 0:
                response_elements = page.query_selector_all("message-content.model-response-text")
            
            # Method 4: Fallback to old selector
            if not response_elements or len(response_elements) == 0:
                response_elements = page.query_selector_all(
                    "div[data-message-author-role='model'], div[data-message-author-role='assistant']"
                )
            
            if response_elements and len(response_elements) > 0:
                latest_response_element = response_elements[-1]  # Most recent response
                
                # Step 2: Verify it's not the prompt
                response_text_dom = latest_response_element.inner_text().strip()
                
                # Check if response text matches prompt (reject if it does)
                if user_prompt_clean in response_text_dom or response_text_dom == user_prompt_clean:
                    # This is likely the prompt, not response - wait more
                    time.sleep(1.0)
                    continue
                
                # Check if response is long enough and different from prompt
                if len(response_text_dom) > MIN_ACCEPT_CHARS and response_text_dom != user_prompt_clean:
                    # Response detected, check if it's stable (complete)
                    # Wait a bit to ensure response is complete
                    time.sleep(2.0)
                    
                    # Re-check to ensure response is still there and stable
                    # Use same selector methods as before
                    response_elements = page.query_selector_all("model-response")
                    if not response_elements or len(response_elements) == 0:
                        response_elements = page.query_selector_all("response-container")
                    if not response_elements or len(response_elements) == 0:
                        response_elements = page.query_selector_all("message-content.model-response-text")
                    if not response_elements or len(response_elements) == 0:
                        response_elements = page.query_selector_all(
                            "div[data-message-author-role='model'], div[data-message-author-role='assistant']"
                        )
                    if response_elements:
                        latest_response_element = response_elements[-1]
                        response_text_dom = latest_response_element.inner_text().strip()
                        
                        # Final verification: ensure it's not prompt
                        if user_prompt_clean not in response_text_dom and len(response_text_dom) > MIN_ACCEPT_CHARS:
                            break  # Response is ready
        except Exception as e:
            pass
        
        time.sleep(1.0)
    
    if not latest_response_element:
        print("⚠️ Gemini response element not found. Falling back to DOM scraping...")
        return None
    
    try:
        # Step 3: Find copy button ONLY in this response element
        # Try multiple selectors based on Gemini UI structure
        copy_button = None
        
        # Method 1: Look for copy button using direct selectors from HTML
        # Copy button is in copy-button component with data-test-id="copy-button"
        copy_button = latest_response_element.query_selector("copy-button button[data-test-id='copy-button']")
        if not copy_button:
            copy_button = latest_response_element.query_selector("copy-button button[aria-label='Copy']")
        if not copy_button:
            copy_button = latest_response_element.query_selector("copy-button button")
        
        # Method 2: Look for copy button in response-container or message-actions
        if not copy_button:
            response_container = latest_response_element.query_selector("response-container")
            if response_container:
                # Try finding copy button in response container footer/actions
                copy_button = response_container.query_selector("copy-button button[data-test-id='copy-button']")
                if not copy_button:
                    copy_button = response_container.query_selector("message-actions copy-button button[data-test-id='copy-button']")
                    if not copy_button:
                        copy_button = response_container.query_selector("button[aria-label*='Copy' i]")
        
        # Method 3: Direct search in response element
        if not copy_button:
            copy_button = latest_response_element.query_selector("button[aria-label*='Copy' i]")
            # Make sure it's not the user query copy button
            if copy_button:
                # Check if button is in user-query (reject if so)
                # Use evaluate to check parent elements
                is_in_user_query = copy_button.evaluate("""
                    (button) => {
                        let parent = button.parentElement;
                        while (parent) {
                            if (parent.tagName && parent.tagName.toLowerCase() === 'user-query') {
                                return true;
                            }
                            parent = parent.parentElement;
                        }
                        return false;
                    }
                """)
                if is_in_user_query:
                    copy_button = None  # This is user query copy button, not response
        
        # Method 3: Try alternative selectors
        if not copy_button:
            for selector in [
                "button[title*='Copy' i]",
                "button[data-testid*='copy' i]",
                "button[fonticon='content_copy']",
                "[role='button'][aria-label*='Copy' i]",
            ]:
                copy_button = latest_response_element.query_selector(selector)
                if copy_button:
                    # Verify it's not in user-query
                    is_in_user_query = copy_button.evaluate("""
                        (button) => {
                            let parent = button.parentElement;
                            while (parent) {
                                if (parent.tagName && parent.tagName.toLowerCase() === 'user-query') {
                                    return true;
                                }
                                parent = parent.parentElement;
                            }
                            return false;
                        }
                    """)
                    if not is_in_user_query:
                        break
                    else:
                        copy_button = None
        
        if not copy_button:
            print("⚠️ Copy button not found in response element. Falling back to DOM scraping...")
            return None
        
        # Step 4: Click copy button
        print("🖱️ Clicking copy button...")
        copy_button.scroll_into_view_if_needed()
        human_wait(0.3, 0.6)
        copy_button.click(timeout=5000)
        human_wait(0.5, 1.0)  # Wait for clipboard to update
        
        # Step 5: Read clipboard
        print("📋 Reading from clipboard...")
        clipboard_text = None
        
        try:
            # Method 1: Using Playwright's clipboard API
            clipboard_text = page.evaluate("""async () => {
                try {
                    const text = await navigator.clipboard.readText();
                    return text;
                } catch (err) {
                    return null;
                }
            }""")
        except Exception as e:
            print(f"⚠️ Clipboard API error: {e}. Trying alternative method...")
        
        # Method 2: Try pyperclip if available
        if not clipboard_text:
            try:
                import pyperclip
                clipboard_text = pyperclip.paste()
            except (ImportError, Exception):
                pass
        
        if not clipboard_text:
            print("⚠️ Failed to read clipboard. Falling back to DOM scraping...")
            return None
        
        clipboard_text = clipboard_text.strip()
        
        # Step 6: Validate clipboard ≠ prompt
        if user_prompt_clean in clipboard_text or clipboard_text == user_prompt_clean:
            print("⚠️ Clipboard contains user prompt, not response. Falling back to DOM scraping...")
            return None
        
        # Additional validation: check if clipboard has expected content (JSON structure)
        if len(clipboard_text) < MIN_ACCEPT_CHARS:
            print("⚠️ Clipboard content too short. Falling back to DOM scraping...")
            return None
        
        # Check if clipboard has prompt keywords (reject if found)
        prompt_keywords = [
            "Provide a complete and comprehensive company profile",
            "Return ONLY valid JSON",
            "Return ONLY the JSON object"
        ]
        if any(keyword in clipboard_text for keyword in prompt_keywords) and len(clipboard_text) < 500:
            print("⚠️ Clipboard appears to contain prompt text. Falling back to DOM scraping...")
            return None
        
        print("✅ Successfully copied response from clipboard!")
        return clipboard_text
        
    except Exception as e:
        print(f"⚠️ Error with copy button: {e}. Falling back to DOM scraping...")
        return None


def scrape_gemini_response(page, timeout_ms=120000) -> str:
    """Scrape Gemini's response text from the UI, waiting until it stabilizes. (Fallback method)"""
    start = time.time()
    last_clean = ""
    stable_since = time.time()

    # Load saved working selectors if available
    saved = []
    if os.path.exists(SELECTOR_MEMORY_FILE):
        try:
            with open(SELECTOR_MEMORY_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
        except:
            saved = []

    # Combine saved selectors with base list
    selectors_to_try = list(dict.fromkeys(saved + BASE_SELECTORS))
    successful = set()

    print("⏳ Waiting for Gemini AI response...")
    while (time.time() - start) * 1000 < timeout_ms:
        # 1. Gather candidates via selectors
        chunks = collect_text_candidates(page, selectors_to_try)

        # 2. Deep shadow DOM traversal
        shadow = deep_shadow_text(page)
        if shadow and len(shadow) > MIN_ACCEPT_CHARS and not looks_like_js_garbage(shadow):
            chunks.append(shadow)

        # 3. Clean, merge, and dedupe
        combined_raw = " ".join(dict.fromkeys(chunks))
        clean = strong_clean(combined_raw)
        clean = dedupe_sentences(clean)

        # 4. Track successful selectors
        if chunks:
            for sel in selectors_to_try:
                try:
                    els = page.query_selector_all(sel)
                    for el in els:
                        if not el or not el.is_visible():
                            continue
                        t = el.inner_text().strip()
                        if t and len(t) >= MIN_ACCEPT_CHARS and not looks_like_js_garbage(t):
                            successful.add(sel)
                            break
                except:
                    continue

        # 5. Stabilization logic
        if len(clean) >= MIN_ACCEPT_CHARS:
            last_clean, stable_since, ok = stabilize_text(clean, last_clean, stable_since)
            if ok:
                print("✅ Gemini output stabilized.")
                if successful:
                    try:
                        with open(SELECTOR_MEMORY_FILE, "w", encoding="utf-8") as f:
                            json.dump(sorted(list(successful)), f, indent=2, ensure_ascii=False)
                        print(f"💾 Saved {len(successful)} working selectors.")
                    except:
                        pass

                # Clean the output
                final_text = clean.strip()
                final_text = re.sub(r"(?i)opens in a new window", "", final_text)
                final_text = re.sub(r"(?i)about gemini.*$", "", final_text)
                final_text = final_text.strip()
                
                # Validate: Ensure we're not returning just the prompt
                prompt_indicators = [
                    "Provide a complete and comprehensive company profile",
                    "Return ONLY valid JSON",
                    "Return ONLY the JSON object"
                ]
                # If text is too short and contains prompt keywords, it's likely just the prompt
                if any(indicator in final_text for indicator in prompt_indicators) and len(final_text) < 500:
                    print("⚠️ Detected prompt text in response. Waiting longer for actual response...")
                    time.sleep(3.0)
                    continue  # Continue waiting for actual response

                return final_text

        time.sleep(1.0)

    print("⚠️ No complete Gemini response detected (timeout). Returning best-effort text.")
    # Filter prompt from last_clean if present
    if last_clean:
        prompt_indicators = [
            "Provide a complete and comprehensive company profile",
            "Return ONLY valid JSON",
            "Return ONLY the JSON object"
        ]
        if any(indicator in last_clean for indicator in prompt_indicators) and len(last_clean) < 500:
            print("⚠️ Warning: Response appears to be prompt text, not actual response.")
    return last_clean


# ---------- JSON Parser ----------
def extract_and_parse_json(response_text: str) -> Optional[Dict]:
    """Extract JSON from response text and parse it."""
    if not response_text:
        return None
    
    response_stripped = response_text.strip()
    
    # Method 0: Handle escaped JSON strings (e.g., "{ \"What\": ... }")
    # Check if response is an escaped JSON string
    if response_stripped.startswith('"') and '{' in response_stripped:
        try:
            # Try to find if it's an escaped JSON string
            # Pattern: "{ \"key\": ... }" or " { \"key\": ... } "
            # First, try to parse as JSON string (unescape it)
            parsed_string = json.loads(response_stripped)
            if isinstance(parsed_string, str):
                # Now parse the unescaped string as JSON
                parsed = json.loads(parsed_string)
                if isinstance(parsed, dict) and any(key in parsed for key in ['What', 'When', 'Where', 'How', 'Who']):
                    return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Method 0.5: Try parsing the entire response as direct JSON object
    if response_stripped.startswith('{'):
        try:
            parsed = json.loads(response_stripped)
            if isinstance(parsed, dict) and any(key in parsed for key in ['What', 'When', 'Where', 'How', 'Who']):
                return parsed
        except json.JSONDecodeError:
            pass
    
    # Method 1: Look for JSON wrapped in markdown code blocks
    code_block_patterns = [
        r'```json\s*(\{.*?\})\s*```',  # ```json { ... } ```
        r'```\s*(\{.*?\})\s*```',      # ``` { ... } ```
    ]
    
    for pattern in code_block_patterns:
        match = re.search(pattern, response_text, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, dict) and any(key in parsed for key in ['What', 'When', 'Where', 'How', 'Who']):
                    return parsed
            except json.JSONDecodeError:
                continue
    
    # Method 2: Find JSON using balanced braces (most reliable for nested JSON)
    # But first check if the entire response might be an escaped JSON string
    if '"' in response_stripped and response_stripped.count('"') >= 2:
        # Check if it looks like an escaped JSON string: "{ \"key\": ... }"
        # Find the first " and last " to extract the string
        first_quote = response_stripped.find('"')
        last_quote = response_stripped.rfind('"')
        if first_quote != -1 and last_quote != -1 and last_quote > first_quote:
            potential_escaped = response_stripped[first_quote:last_quote + 1]
            try:
                unescaped = json.loads(potential_escaped)
                if isinstance(unescaped, str) and unescaped.strip().startswith('{'):
                    parsed = json.loads(unescaped)
                    if isinstance(parsed, dict) and any(key in parsed for key in ['What', 'When', 'Where', 'How', 'Who']):
                        return parsed
            except (json.JSONDecodeError, TypeError):
                pass
    
    brace_count = 0
    start_idx = -1
    candidates = []
    
    for i, char in enumerate(response_text):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                json_str = response_text[start_idx:i + 1]
                candidates.append((start_idx, i + 1, json_str))
                start_idx = -1
    
    # Try all candidates, prefer the one with expected structure
    for start, end, json_str in candidates:
        try:
            # First try direct parsing
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                # Check if it has expected structure
                if any(key in parsed for key in ['What', 'When', 'Where', 'How', 'Who']):
                    return parsed
        except json.JSONDecodeError:
            # If direct parsing fails, check if it's an escaped JSON string
            try:
                if json_str.startswith('"') and json_str.endswith('"'):
                    unescaped = json.loads(json_str)
                    if isinstance(unescaped, str):
                        parsed = json.loads(unescaped)
                        if isinstance(parsed, dict) and any(key in parsed for key in ['What', 'When', 'Where', 'How', 'Who']):
                            return parsed
            except (json.JSONDecodeError, TypeError):
                continue
    
    # Method 3: Fallback - try first { to last } if balanced method didn't work
    json_start = response_text.find('{')
    json_end = response_text.rfind('}')
    
    if json_start != -1 and json_end != -1 and json_end > json_start:
        json_str = response_text[json_start:json_end + 1]
        try:
            # Try direct parsing first
            parsed = json.loads(json_str)
            if isinstance(parsed, dict) and any(key in parsed for key in ['What', 'When', 'Where', 'How', 'Who']):
                return parsed
        except json.JSONDecodeError:
            # If direct parsing fails, check if we need to look for escaped JSON before this
            # Check if there's a quote before the first {
            if json_start > 0:
                before_brace = response_text[:json_start].strip()
                if before_brace.endswith('"'):
                    # Might be an escaped JSON string, try to find the opening quote
                    quote_start = response_text.rfind('"', 0, json_start)
                    if quote_start != -1:
                        potential_escaped = response_text[quote_start:json_end + 2]  # Include closing quote if exists
                        try:
                            unescaped = json.loads(potential_escaped)
                            if isinstance(unescaped, str) and unescaped.strip().startswith('{'):
                                parsed = json.loads(unescaped)
                                if isinstance(parsed, dict) and any(key in parsed for key in ['What', 'When', 'Where', 'How', 'Who']):
                                    return parsed
                        except (json.JSONDecodeError, TypeError, IndexError):
                            pass
    
    return None


# ---------- Company Profile Parser ----------
def extract_section_content(text: str, section_keywords: list, max_lines: int = 20) -> str:
    """Extract content for a section based on keywords."""
    lines = text.split('\n')
    section_content = []
    in_section = False
    lines_collected = 0
    
    for i, line in enumerate(lines):
        line_upper = line.upper().strip()
        
        # Check if this line starts a section
        if any(keyword in line_upper for keyword in section_keywords):
            in_section = True
            lines_collected = 0
            # Skip the header line itself
            continue
        
        # If in section, collect content
        if in_section:
            # Stop if we hit another major section
            if line_upper.startswith(('WHAT', 'WHEN', 'WHERE', 'HOW', 'WHO', '##', '**')):
                break
            if line.strip():
                section_content.append(line.strip())
                lines_collected += 1
                if lines_collected >= max_lines:
                    break
    
    return '\n'.join(section_content).strip()


def extract_sources(response_text: str) -> Dict:
    """Extract sources and links from Gemini response."""
    sources = {
        "URLs": [],
        "Source Mentions": [],
        "References": [],
        "Domains": []
    }
    
    if not response_text:
        return sources
    
    # Extract URLs (http/https and www.)
    url_pattern = r'https?://[^\s\)\]<>"]+|www\.[^\s\)\]<>"]+'
    urls = re.findall(url_pattern, response_text)
    if urls:
        # Clean and deduplicate URLs
        cleaned_urls = []
        for url in urls:
            url = url.strip('.,;:!?)')
            # Add http:// if missing for www. URLs
            if url.startswith('www.'):
                url = 'https://' + url
            if url not in cleaned_urls and len(url) > 10:
                cleaned_urls.append(url)
        sources["URLs"] = cleaned_urls
    
    # Extract source section (Sources:, References:, etc.) - more comprehensive
    source_section_patterns = [
        r"(?i)(?:sources?|references?|links?|citations?)[:\-]?\s*\n(.+?)(?:\n\n|\n[A-Z]|\Z)",
        r"(?i)(?:source|reference|link)[:\-]?\s*([^\n]+)",
    ]
    for pattern in source_section_patterns:
        matches = re.finditer(pattern, response_text, re.DOTALL | re.MULTILINE)
        for match in matches:
            source_text = match.group(1).strip()
            # Split by newlines, bullets, or numbered lists
            source_items = re.split(r'\n|•|\*|-\s+|^\d+[\.\)]\s+', source_text, flags=re.MULTILINE)
            for item in source_items:
                item = item.strip()
                # Remove common prefixes
                item = re.sub(r'^(source|reference|link)[:\-]?\s*', '', item, flags=re.I)
                if item and len(item) > 5:
                    if item not in sources["Source Mentions"]:
                        sources["Source Mentions"].append(item)
    
    # Extract domain names mentioned (excluding common ones)
    domain_pattern = r'\b(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})\b'
    domains = re.findall(domain_pattern, response_text)
    if domains:
        unique_domains = list(dict.fromkeys(domains))
        # Filter out common non-source domains
        filtered_domains = [d for d in unique_domains if d.lower() not in [
            'google.com', 'gemini.google.com', 'gmail.com', 'youtube.com',
            'wikipedia.org', 'wikimedia.org'
        ]]
        if filtered_domains:
            sources["Domains"] = filtered_domains
    
    # Extract citations (e.g., [1], (Source: ...), etc.)
    citation_patterns = [
        r'\[(\d+)\][:\-]?\s*([^\n]+)',
        r'\(Source[:\-]?\s*([^\)]+)\)',
        r'\([^\)]*source[:\-]?\s*([^\)]+)\)',
        r'\[Source[:\-]?\s*([^\]]+)\]',
    ]
    for pattern in citation_patterns:
        matches = re.finditer(pattern, response_text, re.IGNORECASE)
        for match in matches:
            citation = match.group(-1).strip()  # Get last group
            if citation and len(citation) > 5:
                if citation not in sources["References"]:
                    sources["References"].append(citation)
    
    # Clean up empty lists
    sources = {k: v for k, v in sources.items() if v}
    
    return sources


def parse_company_profile(response_text: str, ticker: str) -> Dict:
    """Parse Gemini response to extract structured company profile data."""
    profile = {
        "What": {},
        "When": {},
        "Where": {},
        "How": {},
        "Who": {},
        "Sources": {},
        "Raw Response": response_text
    }
    
    if not response_text or len(response_text.strip()) < 50:
        return profile
    
    text = response_text
    
    # Method 1: Try to extract by section headers (markdown style)
    what_content = extract_section_content(text, ["WHAT", "## WHAT", "**WHAT", "*WHAT"])
    when_content = extract_section_content(text, ["WHEN", "## WHEN", "**WHEN", "*WHEN"])
    where_content = extract_section_content(text, ["WHERE", "## WHERE", "**WHERE", "*WHERE"])
    how_content = extract_section_content(text, ["HOW", "## HOW", "**HOW", "*HOW"])
    who_content = extract_section_content(text, ["WHO", "## WHO", "**WHO", "*WHO"])
    
    if what_content:
        profile["What"]["Description"] = what_content
    if when_content:
        profile["When"]["Description"] = when_content
    if where_content:
        profile["Where"]["Description"] = where_content
    if how_content:
        profile["How"]["Description"] = how_content
    if who_content:
        profile["Who"]["Description"] = who_content
    
    # Method 2: Extract specific fields with flexible patterns
    
    # WHAT: Sector, Industry
    sector_match = re.search(r"(?i)(?:sector|industry)[:\-]\s*([^\n\.]+)", text)
    if sector_match:
        profile["What"]["Sector"] = sector_match.group(1).strip()
    
    industry_match = re.search(r"(?i)industry[:\-]\s*([^\n\.]+)", text)
    if industry_match and not profile["What"].get("Sector"):
        profile["What"]["Industry"] = industry_match.group(1).strip()
    
    # WHEN: Founded, IPO
    founded_match = re.search(r"(?i)(?:founded|established|incorporated|founded in|established in)[:\-]?\s*(\d{4})", text)
    if founded_match:
        profile["When"]["Founded Year"] = founded_match.group(1)
    
    ipo_match = re.search(r"(?i)(?:ipo|initial public offering|went public)[:\-]?\s*([^\n\.]+)", text)
    if ipo_match:
        ipo_text = ipo_match.group(1).strip()
        # Try to extract date
        date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}|\w+\s+\d{4})", ipo_text)
        if date_match:
            profile["When"]["IPO Date"] = date_match.group(1)
        else:
            profile["When"]["IPO Date"] = ipo_text
    
    # WHERE: Location
    location_patterns = [
        r"(?i)(?:headquarters|hq|headquartered|located|based)[:\-]?\s*(?:in|at)?\s*([^\n\.]+)",
        r"(?i)(?:address)[:\-]?\s*([^\n\.]+)",
    ]
    for pattern in location_patterns:
        match = re.search(pattern, text)
        if match:
            location = match.group(1).strip()
            # Clean up common prefixes
            location = re.sub(r"^(in|at|is|are)\s+", "", location, flags=re.I)
            if len(location) > 5:  # Valid location
                profile["Where"]["Location"] = location
                break
    
    # HOW: Business Model, Products
    business_model_match = re.search(r"(?i)(?:business model|revenue model|how it works)[:\-]?\s*([^\n\.]+)", text)
    if business_model_match:
        profile["How"]["Business Model"] = business_model_match.group(1).strip()
    
    products_match = re.search(r"(?i)(?:products?|services?|key offerings?)[:\-]?\s*([^\n\.]+)", text)
    if products_match:
        profile["How"]["Products/Services"] = products_match.group(1).strip()
    
    # WHO: CEO, Leadership
    ceo_patterns = [
        r"(?i)(?:ceo|chief executive officer)[:\-]?\s*(?:is|named)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        r"(?i)(?:ceo)[:\-]?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)",
    ]
    for pattern in ceo_patterns:
        match = re.search(pattern, text)
        if match:
            profile["Who"]["CEO"] = match.group(1).strip()
            break
    
    founder_match = re.search(r"(?i)(?:founded by|founder|founders?)[:\-]?\s*([^\n\.]+)", text)
    if founder_match:
        profile["Who"]["Founder"] = founder_match.group(1).strip()
    
    # Method 3: If sections are still empty, try to extract from full text
    if not any(profile["What"].values()):
        # Try to find any mention of sector/industry
        sector_industry = re.search(r"(?i)(?:sector|industry).{0,100}", text)
        if sector_industry:
            profile["What"]["Extracted Info"] = sector_industry.group(0).strip()
        else:
            # Store first few sentences as description
            sentences = re.split(r'[.!?]+', text)
            if sentences:
                profile["What"]["Description"] = '. '.join(sentences[:3]).strip() + '.'
    
    if not any(profile["When"].values()):
        # Try to find any date/year
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        if year_match:
            profile["When"]["Mentioned Year"] = year_match.group(0)
    
    if not any(profile["Where"].values()):
        # Try to find location keywords
        location_keywords = ["city", "state", "country", "headquarters", "based"]
        for keyword in location_keywords:
            match = re.search(rf"(?i){keyword}[:\-]?\s*([^\n\.]+)", text)
            if match:
                profile["Where"]["Location"] = match.group(1).strip()
                break
    
    if not any(profile["How"].values()):
        # Extract business description
        business_desc = re.search(r"(?i)(?:business|company|operates?|provides?)[:\-]?\s*([^\n\.]{20,200})", text)
        if business_desc:
            profile["How"]["Description"] = business_desc.group(1).strip()
    
    if not any(profile["Who"].values()):
        # Try to find any person name
        person_name = re.search(r"(?i)(?:ceo|founder|executive|leader)[:\-]?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)", text)
        if person_name:
            profile["Who"]["Leadership"] = person_name.group(1).strip()
    
    # Extract sources and links
    sources_data = extract_sources(response_text)
    profile["Sources"] = sources_data
    
    return profile


# ---------- Browser Worker ----------
def fetch_company_profile(ticker: str) -> Optional[str]:
    """Launch Gemini browser, send company profile query, collect response. Returns raw response text."""
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=session_path,
            headless=headless,
            executable_path=CHROME_PATH if CHROME_PATH else None,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        page = ctx.new_page()
        page.set_viewport_size({"width": 1366, "height": 768})
        print(f"🌐 Opening Gemini...")
        page.goto("https://gemini.google.com/app", timeout=60000)
        human_wait(2.0, 3.5)

        # Manual login if session not active
        if "accounts.google.com" in (page.url or "").lower():
            print(f"⚠️ Please log in manually; session will persist.")
            page.pause()

        # Single Comprehensive Company Profile Query - Request JSON format
        query = f"""Provide a complete and comprehensive company profile for stock ticker {ticker} in JSON format. 

Return ONLY valid JSON with the following structure (no markdown, no code blocks, just pure JSON):

{{
  "What": {{
    "Sector": "sector name",
    "Industry": "industry name",
    "Niche": "niche or business focus",
    "Description": "detailed description of what the company does",
    "Products": "main products, services, or offerings",
    "MarketPosition": "business category and market position"
  }},
  "When": {{
    "FoundedYear": "founded year",
    "FoundedDetails": "founding details",
    "IPODate": "IPO date if publicly traded",
    "KeyMilestones": "key milestones and growth timeline",
    "Acquisitions": "major acquisitions or expansions",
    "RecentEvents": "recent significant events"
  }},
  "Where": {{
    "Headquarters": "full headquarters address",
    "City": "city",
    "State": "state/province",
    "Country": "country",
    "OperationalFootprint": "where they operate",
    "OfficeLocations": "key office locations or facilities",
    "GeographicPresence": "geographic presence"
  }},
  "How": {{
    "BusinessModel": "business model and how the company operates",
    "RevenueStreams": "revenue streams and monetization strategy",
    "Products": "key products or services offered",
    "Monetization": "how the company makes money",
    "CompetitiveAdvantages": "competitive advantages or unique selling points",
    "MarketStrategy": "market strategy"
  }},
  "Who": {{
    "CEO": "current CEO name and title",
    "LeadershipTeam": "key leadership team members",
    "Founders": "founder(s) name(s) and background",
    "InstitutionalOwnership": "institutional ownership percentage if available",
    "MajorShareholders": "major shareholders or stakeholders",
    "BoardOfDirectors": "board of directors if available"
  }},
  "Sources": {{
    "URLs": ["list of URLs"],
    "References": ["list of references, articles, websites"]
  }}
}}

Provide factual, detailed, and comprehensive information about {ticker}. Return ONLY the JSON object, nothing else."""

        print(f"💬 Sending company profile query for {ticker}...")
        input_box = None

        # Try multiple known Gemini selectors for the input field
        for s in [
            "textarea[aria-label*='Message' i]",
            "textarea[aria-label*='Ask Gemini' i]",
            "textarea",
            "div[contenteditable='true']",
            "div[role='textbox']",
            "div[aria-label*='Message' i]",
            "div[aria-label*='Ask Gemini' i]",
            "input[aria-label*='Ask Gemini' i]",
        ]:
            try:
                el = page.query_selector(s)
                if el and el.is_visible():
                    input_box = el
                    break
            except:
                continue

        if not input_box:
            print(f"❌ Input box not found.")
            ctx.close()
            return None

        # Focus and send prompt - Use JavaScript to set value directly to avoid Enter key issues
        human_click(page, input_box)
        human_wait(0.3, 0.8)
        
        # Clear existing content
        try:
            input_box.fill("")
        except:
            pass
        
        # Set the entire prompt at once to avoid Enter key presses during typing
        # This prevents newlines from triggering Enter key which submits the form prematurely
        try:
            # Method 1: Try fill() first - works for textarea and input elements
            # fill() sets the entire value at once without typing, so no Enter key issues
            input_box.fill(query)
        except:
            # Method 2: For contenteditable divs, use JavaScript
            try:
                # Use evaluate with element handle
                input_box.evaluate("""
                    (element, text) => {
                        element.focus();
                        // Clear existing content
                        element.innerHTML = '';
                        element.textContent = text;
                        // Trigger input event so Gemini knows the text changed
                        const inputEvent = new Event('input', { bubbles: true });
                        element.dispatchEvent(inputEvent);
                        // Also trigger change event
                        const changeEvent = new Event('change', { bubbles: true });
                        element.dispatchEvent(changeEvent);
                    }
                """, query)
            except:
                # Method 3: Last resort - replace newlines with spaces to avoid Enter key
                query_single_line = query.replace('\n', ' ')
                human_type(input_box, query_single_line)
        
        human_wait(0.5, 1.0)
        
        # Now press Enter only once to submit
        page.keyboard.press("Enter")
        
        # Wait a bit for response to start appearing
        print("⏳ Waiting for Gemini to start generating response...")
        human_wait(5.0, 8.0)  # Wait longer for response to start

        # Method 1: Try direct DOM extraction (fastest - extracts JSON directly from DOM)
        response_text = get_json_directly_from_dom(page, query)
        
        # Method 2: Fallback to copy button method
        if not response_text:
            response_text = get_response_via_copy_button(page, query)
        
        # Method 3: Fallback to DOM scraping if both methods failed
        if not response_text:
            print("📋 Falling back to DOM scraping method...")
            response_text = scrape_gemini_response(page)
            
            # Filter out the prompt text if it appears in the response
            # Remove the prompt query from response if it was captured
            if query and query in response_text:
                # Remove the prompt from response
                response_text = response_text.replace(query, "").strip()
            
            # Also check for partial prompt matches
            prompt_keywords = [
                "Provide a complete and comprehensive company profile",
                "Return ONLY valid JSON",
                "Return ONLY the JSON object"
            ]
            for keyword in prompt_keywords:
                if keyword in response_text and len(response_text) < 500:
                    # If response is too short and contains prompt keywords, it's likely just the prompt
                    print("⚠️ Warning: Response may contain prompt text. Waiting longer...")
                    human_wait(3.0, 5.0)
                    response_text = scrape_gemini_response(page)
                    # Filter again
                    if query and query in response_text:
                        response_text = response_text.replace(query, "").strip()
                    break
        
        # Print response preview
        if response_text:
            print(f"📋 Response preview: {response_text[:200]}...")
            print(f"   Response length: {len(response_text)} chars")
        else:
            print("❌ Failed to get response from Gemini")
            print("⏳ Waiting a bit more in case response is still generating...")
            human_wait(5.0, 8.0)
            # Try one more time with DOM scraping
            response_text = scrape_gemini_response(page, timeout_ms=30000)
            if not response_text:
                print("❌ Still no response after extended wait. Closing browser.")
                ctx.close()
                return None
        
        ctx.close()
        print(f"✅ Company profile extracted for {ticker}")
        return response_text


# ---------- Main ----------
def main():
    """Main entry point for Gemini company profile scraper."""
    ticker = input("Enter Stock Ticker (e.g., TSLA, NVDA, AAPL, IBM): ").upper().strip()
    
    if not ticker:
        print("❌ Please enter a valid ticker symbol.")
        return

    # Ensure session folder exists
    os.makedirs(session_path, exist_ok=True)

    print(f"\n🚀 Fetching company profile for {ticker} via Gemini AI...\n")
    
    response_text = fetch_company_profile(ticker)
    
    if response_text:
        output_file = OUTPUT_FILE.replace("{TICKER}", ticker)
        
        # Clean and parse the response - remove wrapper fields, extract clean JSON
        parsed_json = None
        cleaned_response = response_text.strip()
        
        # Step 0: Remove prompt text if it appears in the response
        prompt_keywords = [
            "Provide a complete and comprehensive company profile",
            "Return ONLY valid JSON",
            "Return ONLY the JSON object",
            "with the following structure",
            "no markdown, no code blocks"
        ]
        for keyword in prompt_keywords:
            if keyword in cleaned_response:
                # Find the position after the prompt text
                keyword_pos = cleaned_response.find(keyword)
                # Look for JSON start after the prompt
                json_start = cleaned_response.find('{', keyword_pos)
                if json_start != -1:
                    cleaned_response = cleaned_response[json_start:]
                    break
                # If no JSON found, try to remove the prompt line
                lines = cleaned_response.split('\n')
                cleaned_response = '\n'.join([line for line in lines if keyword not in line])
        
        # Method 1: Try direct JSON parsing (if response is already a JSON object)
        try:
            parsed_json = json.loads(cleaned_response)
            if isinstance(parsed_json, dict):
                # Check if it's wrapped in Ticker/Source/Response fields
                if "Response" in parsed_json and len(parsed_json) <= 3:
                    # Extract the Response field content
                    inner_response = parsed_json.get("Response", "")
                    if isinstance(inner_response, str):
                        # Try to parse the inner response
                        try:
                            parsed_json = json.loads(inner_response)
                        except:
                            # If inner response is escaped JSON string
                            if inner_response.strip().startswith('"') and inner_response.strip().endswith('"'):
                                unescaped = json.loads(inner_response.strip())
                                if isinstance(unescaped, str):
                                    parsed_json = json.loads(unescaped)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Method 2: Try if it's an escaped JSON string (starts and ends with quotes)
        if not parsed_json:
            try:
                if cleaned_response.startswith('"') and cleaned_response.endswith('"'):
                    # Unescape the JSON string
                    unescaped = json.loads(cleaned_response)
                    if isinstance(unescaped, str) and unescaped.strip().startswith('{'):
                        # Parse the unescaped string as JSON
                        parsed_json = json.loads(unescaped)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Method 3: Try direct parsing after cleaning \r\n
        if not parsed_json:
            try:
                # Replace \r\n with \n, then try parsing
                cleaned = cleaned_response.replace('\\r\\n', '\n').replace('\\n', '\n')
                parsed_json = json.loads(cleaned)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Save the result
        if parsed_json and isinstance(parsed_json, dict):
            # Validate: Check if JSON has expected structure
            expected_keys = ['What', 'When', 'Where', 'How', 'Who']
            found_keys = [key for key in expected_keys if key in parsed_json]
            
            if len(found_keys) < 3:
                print(f"⚠️ Warning: Extracted JSON only has {len(found_keys)}/{len(expected_keys)} expected sections: {found_keys}")
                print("   This might be a partial response. Trying to extract complete JSON...")
                # Try to find complete JSON in the response text
                # Look for the outermost/largest JSON object
                brace_start = cleaned_response.find('{')
                if brace_start != -1:
                    brace_count = 0
                    brace_end = -1
                    for i in range(brace_start, len(cleaned_response)):
                        if cleaned_response[i] == '{':
                            brace_count += 1
                        elif cleaned_response[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                brace_end = i
                                break
                    if brace_end != -1:
                        complete_json_str = cleaned_response[brace_start:brace_end + 1]
                        try:
                            complete_json = json.loads(complete_json_str)
                            if isinstance(complete_json, dict):
                                complete_found_keys = [key for key in expected_keys if key in complete_json]
                                if len(complete_found_keys) > len(found_keys):
                                    print(f"✅ Found more complete JSON with {len(complete_found_keys)} sections")
                                    parsed_json = complete_json
                                    found_keys = complete_found_keys
                        except:
                            pass
            
            # Save the clean parsed JSON object directly (no wrapper fields)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(parsed_json, f, ensure_ascii=False, indent=4)
            
            if len(found_keys) >= 4:
                print(f"\n✅ Company profile saved to {output_file} (complete JSON with {len(found_keys)}/{len(expected_keys)} sections)\n")
            else:
                print(f"\n⚠️ Company profile saved to {output_file} (partial JSON with {len(found_keys)}/{len(expected_keys)} sections)\n")
        else:
            # If not valid JSON, try to extract JSON from the response text using balanced braces
            # Find all potential JSON objects (multiple { } pairs)
            brace_starts = []
            for i, char in enumerate(cleaned_response):
                if char == '{':
                    brace_starts.append(i)
            
            # Try each potential JSON object, prioritizing the largest/outermost one
            parsed_json = None
            json_candidates = []
            
            # First pass: collect all valid JSON candidates with their sizes
            for brace_start in brace_starts:
                brace_count = 0
                brace_end = -1
                for i in range(brace_start, len(cleaned_response)):
                    if cleaned_response[i] == '{':
                        brace_count += 1
                    elif cleaned_response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            brace_end = i
                            break
                
                if brace_end != -1:
                    json_str = cleaned_response[brace_start:brace_end + 1]
                    # Skip if too short (likely not the main JSON)
                    if len(json_str) < 100:
                        continue
                    
                    try:
                        # Try parsing as-is
                        candidate_json = json.loads(json_str)
                        if isinstance(candidate_json, dict):
                            json_candidates.append((len(json_str), candidate_json, json_str))
                    except:
                        try:
                            # Try cleaning escaped characters
                            json_str_clean = json_str.replace('\\r\\n', '\n').replace('\\n', '\n')
                            candidate_json = json.loads(json_str_clean)
                            if isinstance(candidate_json, dict):
                                json_candidates.append((len(json_str_clean), candidate_json, json_str_clean))
                        except:
                            pass
            
            # Sort candidates by size (largest first) and find the one with all expected keys
            json_candidates.sort(reverse=True, key=lambda x: x[0])
            
            expected_keys = ['What', 'When', 'Where', 'How', 'Who']
            for size, candidate_json, json_str in json_candidates:
                # Check if it has ALL expected keys (complete response)
                if all(key in candidate_json for key in expected_keys):
                    parsed_json = candidate_json
                    break
                # If not complete, check if it has at least 4 out of 5 keys (mostly complete)
                elif sum(1 for key in expected_keys if key in candidate_json) >= 4:
                    parsed_json = candidate_json
                    break
            
            # If no complete JSON found, use the largest one (might be partial but better than nothing)
            if not parsed_json and json_candidates:
                parsed_json = json_candidates[0][1]
            
            if parsed_json and isinstance(parsed_json, dict):
                # Validate extracted JSON
                expected_keys = ['What', 'When', 'Where', 'How', 'Who']
                found_keys = [key for key in expected_keys if key in parsed_json]
                
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(parsed_json, f, ensure_ascii=False, indent=4)
                
                if len(found_keys) >= 4:
                    print(f"\n✅ Company profile saved to {output_file} (extracted complete JSON with {len(found_keys)}/{len(expected_keys)} sections)\n")
                else:
                    print(f"\n⚠️ Company profile saved to {output_file} (extracted partial JSON with {len(found_keys)}/{len(expected_keys)} sections)\n")
            else:
                # Last resort: try regex to find JSON-like structure
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned_response, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(0)
                        parsed_json = json.loads(json_str)
                        if isinstance(parsed_json, dict):
                            with open(output_file, "w", encoding="utf-8") as f:
                                json.dump(parsed_json, f, ensure_ascii=False, indent=4)
                            print(f"\n✅ Company profile saved to {output_file} (regex extracted JSON)\n")
                        else:
                            raise ValueError("Not a dict")
                    except:
                        # Save as plain text
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(cleaned_response)
                        print(f"\n⚠️ Company profile saved to {output_file} (as text - JSON extraction failed)\n")
                else:
                    # Save as plain text
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(cleaned_response)
                    print(f"\n⚠️ Company profile saved to {output_file} (as text - no JSON found)\n")
    else:
        print(f"\n❌ Failed to fetch company profile for {ticker}\n")


# ---------- Entry Point ----------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user.")
        sys.exit(0)

