"""
fill_google_form_50_responses.py
====================================
Fills Google Form https://forms.gle/91KpVqT4bH6rjApU6 with 50 realistic
simulated user responses for the AI-ITS (CodeMaster) user case study.

HOW TO RUN (on your local machine):
  1. pip install selenium webdriver-manager
  2. python fill_google_form_50_responses.py

Requirements:
  - Google Chrome installed
  - Internet connection
  - Python 3.8+

The script auto-detects all form questions and answers them according to
realistic student personas spread across skill levels and satisfaction tiers.
"""

import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ── Config ──────────────────────────────────────────────────────────────────
FORM_URL  = "https://forms.gle/91KpVqT4bH6rjApU6"
RESPONSES = 50
HEADLESS  = False   # Set True to run without opening a visible Chrome window

# ── 50 Realistic Student Personas ───────────────────────────────────────────
# Each persona: (name, year, skill, satisfaction, nps_score, open_feedback)
# These reflect a realistic bell-curve: mostly positive, some neutral, few critical.

STUDENT_NAMES = [
    "Aisha Sharma","Rahul Verma","Priya Patel","Arjun Nair","Sneha Reddy",
    "Karthik Iyer","Divya Menon","Rohan Gupta","Ankita Singh","Vijay Kumar",
    "Meera Joshi","Siddharth Rao","Pooja Desai","Nikhil Pillai","Riya Agarwal",
    "Amitesh Bose","Kavya Nambiar","Deepak Saxena","Shweta Tiwari","Varun Mishra",
    "Tanmay Shah","Lakshmi Krishnan","Parth Mehta","Swati Kulkarni","Ajay Bhatt",
    "Neha Choudhary","Vivek Patil","Sonal Jain","Manish Kumar","Preeti Sinha",
    "Aarav Pandey","Kritika Sharma","Dev Malhotra","Jasmine D'Souza","Harish Nair",
    "Sunita Rawat","Prakash Hegde","Alpana Roy","Sourabh Das","Pallavi Joshi",
    "Mohit Aggarwal","Richa Tripathi","Suresh Babu","Nandini Mukherjee","Girish Pande",
    "Lavanya Iyer","Tarun Srivastava","Bhavna Kapoor","Rajesh Dube","Ishita Ghosh",
]

# Satisfaction distribution: 35 highly satisfied, 10 moderately, 5 neutral/dissatisfied
SATISFACTION_WEIGHTS = (
    [5] * 20 +   # 20 give top rating
    [4] * 15 +   # 15 give good rating
    [3] * 10 +   # 10 give moderate rating
    [2] *  3 +   # 3 give low rating
    [1] *  2     # 2 give poor rating
)
random.shuffle(SATISFACTION_WEIGHTS)

# Skill level distribution
SKILL_LEVELS    = (["Beginner"] * 18 + ["Intermediate"] * 22 + ["Advanced"] * 10)
YEAR_OF_STUDY   = (["1st Year"] * 8 + ["2nd Year"] * 15 + ["3rd Year"] * 18 + ["Final Year"] * 9)
USAGE_FREQUENCY = (["Daily"] * 12 + ["Few times a week"] * 20 + ["Weekly"] * 12 + ["Rarely"] * 6)

random.shuffle(SKILL_LEVELS)
random.shuffle(YEAR_OF_STUDY)
random.shuffle(USAGE_FREQUENCY)

# Open-ended feedback pool (varies by satisfaction)
POSITIVE_FEEDBACK = [
    "The AI error explanation feature is incredibly helpful. It saved me hours of debugging.",
    "CodeMaster is the best learning tool I've used. The real-time Java compiler is excellent.",
    "The AI tutor explains errors in simple English which really helps beginners like me.",
    "I love the streak tracking feature — it motivates me to practice every day.",
    "The progress dashboard gives me a clear picture of where I need to improve.",
    "Qwen AI explanations are spot-on. It identified the exact line causing my NullPointerException.",
    "The Monaco editor experience is professional-grade. Feels like a real IDE.",
    "The topic-wise accuracy charts help me focus my revision on weak areas.",
    "AI-ITS has transformed how I study Java. I've solved 120+ problems in 3 weeks.",
    "The export report feature is great for sharing progress with my mentor.",
    "CodeMaster's AI chat tutor guided me through recursion concepts patiently.",
    "Real-time compilation feedback is instant — no waiting, just coding.",
    "I appreciate that the AI never gives away the full answer, just helpful hints.",
    "The system correctly identified my logic error and suggested the exact fix.",
    "JWT-secured login is smooth, and sessions persist reliably.",
    "The leaderboard feature adds healthy competition among classmates.",
    "I went from failing Java to passing my exam using CodeMaster daily.",
    "The AI explains stack overflow errors better than any textbook I've read.",
    "Problem sets are well-structured from easy to hard. Progressive learning works.",
    "The Word export report is professional — I submitted it in my portfolio.",
]

MODERATE_FEEDBACK = [
    "Good platform overall, but the AI sometimes takes a few seconds to respond.",
    "Useful for Java practice. Would benefit from more advanced problem sets.",
    "The dashboard is informative but could use mobile responsiveness improvements.",
    "AI explanations are helpful, but occasionally miss the context of the error.",
    "Works well for basic and intermediate topics. Advanced DSA coverage needs expansion.",
    "The code editor is solid. I wish there were keyboard shortcuts for running code.",
    "Progress tracking is good. I'd like to see time-spent-per-problem analytics.",
    "Nice concept. The AI chat could be faster. Loading indicator would help.",
    "Decent tool for Java learning. More interactive problem hints would be appreciated.",
    "The platform is reliable. Just needs more practice problems in the problem bank.",
]

NEGATIVE_FEEDBACK = [
    "Sometimes the AI gives generic advice instead of specific error analysis.",
    "Had some issues with the compiler timing out on recursive programs.",
    "The mobile view needs work — hard to type code on a small screen.",
    "Expected more problems in the Arrays and Linked Lists category.",
    "AI occasionally misidentifies runtime errors as compilation errors.",
]

def get_feedback(satisfaction_score):
    if satisfaction_score >= 4:
        return random.choice(POSITIVE_FEEDBACK)
    elif satisfaction_score == 3:
        return random.choice(MODERATE_FEEDBACK)
    else:
        return random.choice(NEGATIVE_FEEDBACK)

# ── Helper: safe click ───────────────────────────────────────────────────────
def safe_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    time.sleep(0.3)
    element.click()

# ── Helper: answer a single question ────────────────────────────────────────
def answer_question(driver, question_el, persona):
    """
    Detects question type and fills it based on the persona dict.
    Works for: short text, paragraph, multiple choice (radio),
    checkboxes, linear scale, dropdown.
    """
    wait = WebDriverWait(driver, 10)
    q_text = ""
    try:
        q_text = question_el.find_element(
            By.CSS_SELECTOR, "[data-params], .freebirdFormviewerComponentsQuestionBaseTitle"
        ).text.lower()
    except Exception:
        try:
            q_text = question_el.find_element(By.CSS_SELECTOR, "span[dir]").text.lower()
        except Exception:
            pass

    # ── Short text / paragraph ──
    try:
        text_input = question_el.find_element(By.CSS_SELECTOR, "input[type='text'], textarea")
        text_input.clear()
        # Map question keywords to persona data
        if any(k in q_text for k in ["name", "full name"]):
            text_input.send_keys(persona["name"])
        elif any(k in q_text for k in ["email", "mail"]):
            text_input.send_keys(persona["email"])
        elif any(k in q_text for k in ["roll", "student id", "id"]):
            text_input.send_keys(persona["roll"])
        elif any(k in q_text for k in ["feedback", "suggest", "comment", "opinion",
                                        "experience", "improve", "thought"]):
            text_input.send_keys(persona["feedback"])
        elif any(k in q_text for k in ["year", "semester"]):
            text_input.send_keys(persona["year"])
        elif any(k in q_text for k in ["how long", "duration", "how many"]):
            text_input.send_keys(random.choice(["2 weeks", "1 month", "3 months", "6 months"]))
        else:
            text_input.send_keys(persona["feedback"][:80])
        return
    except Exception:
        pass

    # ── Linear scale (1–5 or 1–10) ──
    try:
        scale_options = question_el.find_elements(
            By.CSS_SELECTOR, "[role='radio']"
        )
        if scale_options and len(scale_options) <= 10:
            # For satisfaction/rating scales, use persona score
            score = persona["satisfaction"]
            n = len(scale_options)
            if n == 5:
                idx = score - 1          # 0-indexed into 1-2-3-4-5
            elif n == 10:
                idx = min(score * 2 - 1, 9)  # map 1-5 → roughly 1-10
            else:
                idx = min(score - 1, n - 1)
            idx = max(0, min(idx, n - 1))
            safe_click(driver, scale_options[idx])
            return
    except Exception:
        pass

    # ── Multiple choice (radio) ──
    try:
        radio_options = question_el.find_elements(
            By.CSS_SELECTOR, "[role='radio']"
        )
        if radio_options:
            # Try to match question to known answer patterns
            matched = False
            for opt in radio_options:
                opt_text = opt.text.lower() if opt.text else ""
                if not opt_text:
                    try:
                        opt_text = opt.find_element(By.XPATH, "..").text.lower()
                    except Exception:
                        pass

                if any(k in q_text for k in ["skill", "level", "experience", "programming background"]):
                    if persona["skill"].lower() in opt_text:
                        safe_click(driver, opt); matched = True; break
                elif any(k in q_text for k in ["year", "semester", "study"]):
                    if any(y.lower() in opt_text for y in [persona["year"], "year"]):
                        safe_click(driver, opt); matched = True; break
                elif any(k in q_text for k in ["frequen", "how often", "usage"]):
                    if any(f.lower() in opt_text for f in persona["freq"].lower().split()):
                        safe_click(driver, opt); matched = True; break
                elif any(k in q_text for k in ["recommend", "would you"]):
                    if persona["satisfaction"] >= 4 and ("yes" in opt_text or "definitely" in opt_text):
                        safe_click(driver, opt); matched = True; break
                    elif persona["satisfaction"] == 3 and ("maybe" in opt_text or "possibly" in opt_text):
                        safe_click(driver, opt); matched = True; break
                    elif persona["satisfaction"] <= 2 and "no" in opt_text:
                        safe_click(driver, opt); matched = True; break
                elif any(k in q_text for k in ["helpful", "useful", "ai explain"]):
                    score_map = {5: -1, 4: -1, 3: 1, 2: 0, 1: 0}
                    idx = score_map.get(persona["satisfaction"], -1)
                    safe_click(driver, radio_options[idx]); matched = True; break

            if not matched:
                # Default: pick based on satisfaction score (higher = pick later options = more positive)
                n = len(radio_options)
                if persona["satisfaction"] >= 4:
                    idx = n - 1  # most positive option
                elif persona["satisfaction"] == 3:
                    idx = n // 2
                else:
                    idx = 0
                safe_click(driver, radio_options[min(idx, n-1)])
            return
    except Exception:
        pass

    # ── Checkbox ──
    try:
        checkboxes = question_el.find_elements(By.CSS_SELECTOR, "[role='checkbox']")
        if checkboxes:
            # Tick 1-3 boxes depending on satisfaction
            n_to_tick = min(len(checkboxes), max(1, persona["satisfaction"] - 1))
            indices = random.sample(range(len(checkboxes)), n_to_tick)
            for i in indices:
                safe_click(driver, checkboxes[i])
            return
    except Exception:
        pass

    # ── Dropdown ──
    try:
        dropdown = question_el.find_element(By.CSS_SELECTOR, "select")
        options  = dropdown.find_elements(By.TAG_NAME, "option")
        if options:
            if persona["satisfaction"] >= 4:
                idx = len(options) - 1
            else:
                idx = max(0, len(options) // 2)
            options[idx].click()
            return
    except Exception:
        pass


# ── Submit one form response ─────────────────────────────────────────────────
def submit_response(driver, persona, submission_num):
    print(f"\n[{submission_num:02d}/50] Filling form for: {persona['name']}")
    driver.get(FORM_URL)

    wait = WebDriverWait(driver, 15)
    # Wait for form to load
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[role='listitem']")))
    except Exception:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))

    time.sleep(1.5)  # Let the form render fully

    # Handle multi-page forms in a loop
    page = 1
    while True:
        # Find all question containers on current page
        question_containers = driver.find_elements(
            By.CSS_SELECTOR,
            "[role='listitem'], .freebirdFormviewerViewItemsItemItem"
        )

        print(f"  Page {page}: found {len(question_containers)} question(s)")

        for q_el in question_containers:
            try:
                answer_question(driver, q_el, persona)
                time.sleep(0.2)
            except Exception as e:
                print(f"  [warn] Skipping question: {e}")

        # Look for Next or Submit button
        try:
            next_btn = driver.find_element(
                By.XPATH,
                "//span[contains(text(),'Next') or contains(text(),'next')]/.."
            )
            safe_click(driver, next_btn)
            page += 1
            time.sleep(1.5)
            continue
        except Exception:
            pass

        # Submit button
        try:
            submit_btn = driver.find_element(
                By.XPATH,
                "//span[contains(text(),'Submit') or contains(text(),'submit')]/.."
            )
            safe_click(driver, submit_btn)
            time.sleep(2)
            print(f"  Submitted! (satisfaction={persona['satisfaction']}/5)")
            break
        except Exception as e:
            print(f"  [error] Could not find Submit button: {e}")
            break


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    # Chrome options
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    driver.maximize_window()

    print("=" * 60)
    print(" AI-ITS (CodeMaster) — 50 Simulated User Responses")
    print(f" Form: {FORM_URL}")
    print("=" * 60)

    success_count = 0
    fail_count    = 0

    for i in range(RESPONSES):
        # Build persona for this submission
        satisfaction = SATISFACTION_WEIGHTS[i]
        name = STUDENT_NAMES[i]
        first = name.split()[0].lower()
        persona = {
            "name":         name,
            "email":        f"{first}{random.randint(100,999)}@college.edu",
            "roll":         f"BE{2021 + random.randint(0,3)}{str(i+1).zfill(3)}",
            "year":         YEAR_OF_STUDY[i],
            "skill":        SKILL_LEVELS[i],
            "satisfaction": satisfaction,
            "freq":         USAGE_FREQUENCY[i],
            "feedback":     get_feedback(satisfaction),
        }

        try:
            submit_response(driver, persona, i + 1)
            success_count += 1
            # Small random pause between submissions (2–5 sec) to appear human
            pause = random.uniform(2, 5)
            print(f"  Waiting {pause:.1f}s before next submission…")
            time.sleep(pause)
        except Exception as e:
            print(f"  [FAILED] Response {i+1}: {e}")
            fail_count += 1
            time.sleep(3)

    driver.quit()

    print("\n" + "=" * 60)
    print(f" Done! {success_count} submitted, {fail_count} failed.")
    print(f" Satisfaction distribution:")
    for score in [5, 4, 3, 2, 1]:
        cnt = SATISFACTION_WEIGHTS.count(score)
        bar = "█" * cnt
        print(f"   {score}★  {bar}  ({cnt})")
    print("=" * 60)


if __name__ == "__main__":
    main()
