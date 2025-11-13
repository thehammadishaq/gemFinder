# -*- coding: utf-8 -*-
"""
Gemini UI Scraper (Playwright, hardened)

- Extremely broad selector coverage with strong filtering to avoid wrong matches.
- Shadow DOM deep extraction.
- Stabilization logic (text length + time).
- Junk/JS/boilerplate filtering.
- Selector memory (persists the selectors that actually worked).
- Sentence-level de-duplication to avoid repeated content in outputs.
- Human-like mouse and typing simulation for natural browser automation.
- HTML snapshot saving removed for clean, silent operation.

NOTE: Automating third-party UIs can violate site terms; use APIs for production.
"""

from playwright.sync_api import sync_playwright
import threading, time, random, os, sys, json, re
from typing import List, Tuple, Dict

# ---------- CONFIG ----------
session_path_1 = "x_browser_session_gemini_1"
session_path_2 = "x_browser_session_gemini_2"
headless = False
CHROME_PATH = None
OUTPUT_RESULTS_FILE = "gemini_ai_responses_combined.json"
FINAL_RESUMES_FILE = "final_resumes.txt"
MOUSE_STEP_MS = 6
SELECTOR_MEMORY_FILE = "working_selectors.json"
DEBUG_SNAPSHOTS = True      # kept for compatibility, not used
STABILIZE_SECONDS = 7
MIN_ACCEPT_CHARS = 240
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
    r'(?<=[.?!])\s+(?=[A-Z0-9“"(\[])|(?<=\n)\s+'
)

def _normalize_sentence(s: str) -> str:
    s2 = s.strip()
    s2 = re.sub(r"\s+", " ", s2)
    s2 = s2.strip("“”\"'`•–- ").lower()
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
    out: List[str] = []
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
BASE_SELECTORS: List[str] = list(dict.fromkeys([
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
def collect_text_candidates(page, selectors: List[str]) -> List[str]:
    texts: List[str] = []
    for sel in selectors:
        try:
            els = page.query_selector_all(sel)
            if not els:
                continue
            for el in els:
                try:
                    if not el or not el.is_visible():
                        continue
                    role = (el.get_attribute("role") or "").lower()
                    if role in ("navigation", "banner", "complementary", "contentinfo"):
                        continue
                    t = el.inner_text().strip()
                    if not t or len(t) < 40 or looks_like_js_garbage(t):
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


def stabilize_text(current: str, last: str, stable_since: float) -> Tuple[str, float, bool]:
    """Return updated stability state for response text."""
    now = time.time()
    if current != last:
        return current, now, False
    if now - stable_since >= STABILIZE_SECONDS:
        return last, stable_since, True
    return last, stable_since, False
def scrape_gemini_response(page, timeout_ms=120000) -> str:
    """Scrape Gemini's response text from the UI, waiting until it stabilizes."""
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

    print(":hourglass_flowing_sand: Waiting for Gemini AI response...")
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
                print(":white_check_mark: Gemini output stabilized.")
                if successful:
                    try:
                        with open(SELECTOR_MEMORY_FILE, "w", encoding="utf-8") as f:
                            json.dump(sorted(list(successful)), f, indent=2, ensure_ascii=False)
                        print(f":floppy_disk: Saved {len(successful)} working selectors.")
                    except:
                        pass

                # :white_check_mark: Clean the output to only keep Gemini’s real reply (NO / Person ...)
                final_text = clean.strip()

                # Remove prompt echoes and UI noise
                final_text = re.sub(r"(?i)opens in a new window", "", final_text)
                final_text = re.sub(r"(?i)about gemini.*$", "", final_text)
                final_text = re.sub(r"(?i)tell me whether.*?nothing else\.?", "", final_text)
                final_text = final_text.strip()

                # --- STRICT LOGIC ---
                # If "NO" appears, return exactly "NO"
                if re.search(r"\bNO\b", final_text):
                    return "NO"

                # If "Person" appears, return from there onward
                m = re.search(r"\bPerson\b", final_text)
                if m:
                    return final_text[m.start():].strip()

                # Otherwise, fallback to the cleaned text
                return final_text

        time.sleep(1.0)

    print(":warning: No complete Gemini response detected (timeout). Returning best-effort text.")
    return last_clean


# ---------- Browser Worker ----------
def run_browser(instance_id, session_path, person, results):
    """Launch one Gemini browser instance, send prompts, collect responses."""
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=session_path,
            headless=headless,
            executable_path=CHROME_PATH if CHROME_PATH else None,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        page = ctx.new_page()
        page.set_viewport_size({"width": 1366, "height": 768})
        print(f"[Browser {instance_id}] :globe_with_meridians: Opening Gemini...")
        page.goto("https://gemini.google.com/app", timeout=60000)
        human_wait(2.0, 3.5)

        # Manual login if session not active
        if "accounts.google.com" in (page.url or "").lower():
            print(f"[Browser {instance_id}] :warning: Please log in manually; session will persist.")
            page.pause()

        # Query set (2-prompt setup)
        queries = [
            f"Tell me whether the given word or phrase clearly refers to a real individual's personal name. "
            f"If it does, respond with 'Person' and then answer concisely: Who is {person}? "
            f"Provide a short factual overview including their profession, industries, and public prominence. "
            f"If it does NOT refer to a person (for example, it is a concept, company, or topic), respond ONLY with 'NO' — nothing else.",

            
        ]

        # Loop through queries
        for q in queries:
            print(f"[Browser {instance_id}] :speech_balloon: Sending: {q}")
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
                print(f"[Browser {instance_id}] :x: Input box not found.")
                continue

            # Focus and send prompt
            human_click(page, input_box)
            human_wait(0.3, 0.8)
            try:
                input_box.fill("")
            except:
                pass
            human_type(input_box, q)
            human_wait(0.4, 1.0)
            page.keyboard.press("Enter")

            # Capture and clean Gemini response
            response_text = scrape_gemini_response(page)
            cleaned = strong_clean(response_text)
            cleaned = dedupe_sentences(cleaned)
            results.append({"browser": instance_id, "query": q, "response": cleaned})
            human_wait(1.0, 2.0)

        ctx.close()
        print(f"[Browser {instance_id}] :white_check_mark: Finished.")
# ---------- Postprocessor ----------
def summarize_results(input_file=OUTPUT_RESULTS_FILE, output_file=FINAL_RESUMES_FILE):
    """Combine and clean the results, producing a final deduped text summary."""
    if not os.path.exists(input_file):
        print(f":x: File not found: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    summaries = []
    for key in ["instance_1_results", "instance_2_results"]:
        if key in data:
            person = data.get(f"browser{key[-1]}_person", "")
            full_text = "\n".join(
                item.get("response", "") for item in data[key] if item.get("response")
            )
            cleaned = strong_clean(full_text)
            cleaned = dedupe_sentences(cleaned)
            if person:
                summaries.append(f"\n\n=== {person.upper()} ===\n{cleaned}")
            else:
                summaries.append(f"\n\n=== PERSON {key[-1]} ===\n{cleaned}")

    final_text = "\n".join(summaries)
    final_text = dedupe_sentences(final_text)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f":white_check_mark: Cleaned résumés saved to {output_file}")
# ----------------------------------------------------
def pretty_human_summary(input_file=OUTPUT_RESULTS_FILE, output_file="human_readable_summary.txt"):
    """Generate a clear, human-friendly report from the structured JSON results."""
    if not os.path.exists(input_file):
        print(f":x: File not found: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    out_lines = []

    # Helper function for each browser instance
    def write_browser_section(browser_key, instance_key):
        person = data.get(browser_key + "_person", "UNKNOWN")
        out_lines.append(f":compass: {browser_key.replace('_', ' ').title()} — Person Queried: “{person.upper()}”\n")

        for i, entry in enumerate(data.get(instance_key, []), start=1):
            out_lines.append(f"Query {i}\n")
            out_lines.append("\nPrompt:\n")
            out_lines.append(entry.get("query", "").strip() + "\n")
            out_lines.append("\nResponse:\n")
            response = entry.get("response", "").strip()
            if response:
                out_lines.append(response + "\n")
            else:
                out_lines.append("(No response)\n")
            out_lines.append("\n")

    # Write for both browser instances
    write_browser_section("browser1", "instance_1_results")
    write_browser_section("browser2", "instance_2_results")

    # Save the formatted text
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))

    print(f":white_check_mark: Human-readable summary saved to {output_file}")


# ---------- Main ----------
def main():
    """Main entry point for Gemini dual-browser scraper."""
    print("Enter the first person's name for Browser 1:")
    person1 = input("> ").strip()
    print("Enter the second person's name for Browser 2:")
    person2 = input("> ").strip()

    if not person1 or not person2 or person1.lower() == person2.lower():
        print(":x: You must enter two different names.")
        return

    # Ensure session folders exist
    os.makedirs(session_path_1, exist_ok=True)
    os.makedirs(session_path_2, exist_ok=True)

    results1, results2 = [], []
    print(":rocket: Launching both browsers...")

    # Run both browser threads
    t1 = threading.Thread(
        target=run_browser, args=(1, session_path_1, person1, results1), daemon=True
    )
    t2 = threading.Thread(
        target=run_browser, args=(2, session_path_2, person2, results2), daemon=True
    )

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Final cleaning of per-item responses
    for item in results1:
        if "response" in item:
            item["response"] = dedupe_sentences(strong_clean(item["response"]))
    for item in results2:
        if "response" in item:
            item["response"] = dedupe_sentences(strong_clean(item["response"]))

    combined = {
        "browser1_person": person1,
        "browser2_person": person2,
        "instance_1_results": results1,
        "instance_2_results": results2,
    }

    with open(OUTPUT_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"\n:floppy_disk: All done! Results saved in {OUTPUT_RESULTS_FILE}\n")
summarize_results()
pretty_human_summary()



# ---------- Entry Point ----------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user.")
        sys.exit(0)
# ----------------------------------------------------

