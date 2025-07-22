from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scraper(driver):

    # find elements by class name 'product-name'
    products = driver.find_elements(By.CLASS_NAME, "product-item")

    scraped_data = []

    # iterate over found elements and print their text content
    for product in products:
        product_name = product.find_element(By.CLASS_NAME, "product-name")
        product_price = product.find_element(By.CLASS_NAME, "product-price")

        data = {
            "name": product_name.text,
            "price": product_price.text,
        }

        # append the data to the empty list
        scraped_data.append(data)

    # return the scraped data
    return scraped_data


######## WORKIN SOLUTION WITH SELENIUM ########
# # instantiate options for Chrome
# options = webdriver.ChromeOptions()

# # run the browser in headless mode
# #options.add_argument("--headless=new")
# options.add_argument('--log-level=3')


# # instantiate Chrome WebDriver with options
# driver = webdriver.Chrome(options=options)

# # open the specified URL in the browser
# driver.get("https://www.wildberries.by/catalog/222664841/detail.aspx")

# driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

# wait = WebDriverWait(driver, 20)

# product_name = wait.until(
#     EC.visibility_of_element_located((By.CSS_SELECTOR, ".product-page__title"))
# )
# print("Product Name:", product_name.text)

# final_price_el = wait.until(
#     EC.visibility_of_element_located((By.CSS_SELECTOR, ".price-block__final-price"))
# )
# print("Final Price:", final_price_el.text)

# old_price_el = wait.until(
#     EC.visibility_of_element_located((By.CSS_SELECTOR, ".price-block__old-price"))
# )
# print("Old Price:", old_price_el.text)

# # close the browser
# driver.quit()
######## WORKIN SOLUTION WITH SELENIUM ########

######## WORKIN SOLUTION WITH PLAYWRIGHT ########
# import re
# import json
# from pathlib import Path
# from datetime import datetime
# from playwright.sync_api import sync_playwright

# ARTICULES_FILE = Path("wb_articules.txt")
# OUTPUT_FILE    = Path("wb_results.json")

# def load_articules() -> list[str]:
#     if not ARTICULES_FILE.exists():
#         return []
#     return [
#         line.strip()
#         for line in ARTICULES_FILE.read_text(encoding="utf-8").splitlines()
#         if line.strip()
#     ]

# def append_articules(new_items: list[str]) -> None:
#     existing = set(load_articules())
#     with ARTICULES_FILE.open("a", encoding="utf-8") as f:
#         for art in new_items:
#             if art not in existing:
#                 f.write(f"{art}\n")
#                 existing.add(art)

# def prompt_for_articules() -> list[str]:
#     raw = input("Enter new articules (comma/space separated), or press Enter to skip: ").strip()
#     if not raw:
#         return []
#     parts = re.split(r"[,\s;]+", raw)
#     return [p for p in (pt.strip() for pt in parts) if p]

# def parse_price(price_str: str) -> float:
#     """
#     Convert a price string like '1 234,00 BYN' or '1234,00' to float 1234.00.
#     """
#     # find the numeric part (digits, spaces, comma and decimal)
#     match = re.search(r"[\d\s]+,\d{2}", price_str)
#     if not match:
#         raise ValueError(f"Cannot parse price from '{price_str}'")
#     num = match.group().replace(" ", "").replace(",", ".")
#     return float(num)

# def get_wb_product_details_by_articule(articule: str) -> dict:
#     with sync_playwright() as p:
#         browser = p.chromium.launch(channel="chrome", headless=False, args=["--log-level=3"])
#         page    = browser.new_page()
#         url     = f"https://www.wildberries.by/catalog/{articule}/detail.aspx"
#         page.goto(url, wait_until="networkidle")

#         name_el  = page.wait_for_selector(".product-page__title",       state="visible")
#         final_el = page.wait_for_selector(".price-block__final-price", state="visible")

#         data = {
#             "articule":       articule,
#             "product_name":   name_el.text_content().strip(),
#             "final_price":    final_el.text_content().strip(),
#             "last_execution": datetime.now().isoformat()
#         }

#         browser.close()
#         return data

# def main():
#     # 1. Prompt & append new articules
#     new_items = prompt_for_articules()
#     if new_items:
#         append_articules(new_items)
#         print(f"Appended {len(new_items)} new articule(s).")

#     # 2. Load all articules
#     articules = load_articules()
#     if not articules:
#         print("No articules to process.")
#         return
#     print("Processing articules:", articules)

#     # 3. Load previous results (if any) to detect price changes
#     if OUTPUT_FILE.exists():
#         old_results = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
#         old_prices  = {item["articule"]: parse_price(item["final_price"]) for item in old_results}
#     else:
#         old_prices = {}

#     # 4. Scrape and compare prices
#     results = []
#     for art in articules:
#         result = get_wb_product_details_by_articule(art)
#         current_price = parse_price(result["final_price"])
#         product_name = result["product_name"]

#         # check for price change
#         if art in old_prices:
#             old_price = old_prices[art]
#             if current_price != old_price:
#                 diff = current_price - old_price
#                 sign = "+" if diff > 0 else ""
#                 print(
#                     f"Price change detected for {product_name}: "
#                     f"{old_price:.2f} → {current_price:.2f} ({sign}{diff:.2f})"
#                 )

#         results.append(result)

#     # 5. Write updated results to JSON
#     with OUTPUT_FILE.open("w", encoding="utf-8") as f:
#         json.dump(results, f, ensure_ascii=False, indent=2)
#     print(f"Results written to {OUTPUT_FILE}")

# if __name__ == "__main__":
#     main()
######## WORKIN SOLUTION WITH PLAYWRIGHT ########


##### TELEGRAM SMALL LOGIC #####
# import os
# import re
# import json
# import logging
# import asyncio
# from datetime import datetime
# from pathlib import Path
# from telegram.constants import ParseMode


# from telegram import ForceReply, Update
# from telegram.ext import (
#     Application,
#     CommandHandler,
#     ContextTypes,
#     MessageHandler,
#     filters,
# )

# from playwright.sync_api import sync_playwright

# # ─── Logging Configuration ───────────────────────────────────────────────────
# logging.basicConfig(
#     format="%(asctime)s %(name)s %(levelname)s %(message)s",
#     level=logging.INFO,
#     handlers=[
#         logging.StreamHandler(),
#         logging.FileHandler("bot.log", encoding="utf-8")
#     ]
# )
# logger = logging.getLogger(__name__)

# # ─── File Paths ──────────────────────────────────────────────────────────────
# ARTICULES_FILE = Path("wb_articules.txt")
# OUTPUT_FILE    = Path("wb_results.json")

# # ─── Sync Scraper ────────────────────────────────────────────────────────────
# def get_wb_product_details_by_articule(art: str) -> dict:
#     with sync_playwright() as p:
#         browser = p.chromium.launch(channel="chrome", headless=False, args=["--log-level=3"])
#         page    = browser.new_page()
#         url     = f"https://www.wildberries.by/catalog/{art}/detail.aspx"
#         page.goto(url, wait_until="networkidle")

#         name_el  = page.wait_for_selector(".product-page__title",       state="visible", timeout=30000)
#         final_el = page.locator("ins.price-block__final-price.red-price").first
#         final_el.wait_for(state="visible", timeout=30000)

#         data = {
#             "articule":       art,
#             "product_name":   name_el.text_content().strip(),
#             "final_price":    final_el.text_content().strip(),
#             "last_execution": datetime.utcnow().isoformat() + "Z"
#         }
#         browser.close()
#         return data

# # ─── Helpers ─────────────────────────────────────────────────────────────────
# def load_articules() -> list[str]:
#     if not ARTICULES_FILE.exists():
#         return []
#     return [l.strip() for l in ARTICULES_FILE.read_text("utf-8").splitlines() if l.strip()]

# def append_articules(new_items: list[str]) -> tuple[int,int]:
#     """
#     Append each unique articule to the file.
#     Returns (added_count, skipped_count).
#     """
#     existing = set(load_articules())
#     added, skipped = 0, 0

#     with ARTICULES_FILE.open("a", encoding="utf-8") as f:
#         for art in new_items:
#             if art in existing:
#                 skipped += 1
#             else:
#                 f.write(art + "\n")
#                 existing.add(art)
#                 added += 1

#     return added, skipped

# def parse_price(price_str: str) -> float:
#     m = re.search(r"[\d\s]+,\d{2}", price_str)
#     return float(m.group().replace(" ", "").replace(",", "."))

# async def scrape_in_thread(art: str) -> dict:
#     loop = asyncio.get_running_loop()
#     return await loop.run_in_executor(None, get_wb_product_details_by_articule, art)

# # ─── Bot Handlers ────────────────────────────────────────────────────────────
# async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
#     user = update.effective_user
#     text = (
#         f"Hi {user.mention_markdown_v2()}\\!  \n"
#         "Send `/scrape <articule>` to fetch product details\.\n"
#         "Or `/add <id1,id2,…>` to add new articules\."
#     )
#     await update.message.reply_text(
#         text,
#         parse_mode=ParseMode.MARKDOWN_V2
#     )


# async def help_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
#     await start(update, ctx)

# async def add_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
#     """
#     /add <id> or /add <id1,id2,id3> or /add id1 id2
#     """
#     raw = " ".join(ctx.args).strip()
#     if not raw:
#         return await update.message.reply_text("Usage: /add <articule1,articule2 ...>")

#     # split on commas, semicolons or whitespace
#     parts = re.split(r"[,\s;]+", raw)
#     new_ids = [p for p in (pt.strip() for pt in parts) if p]

#     added, skipped = append_articules(new_ids)
#     await update.message.reply_text(
#         f"✅ Added {added} articule(s), skipped {skipped} already present."
#     )

# async def scrape_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
#     arts = load_articules()
#     if not arts:
#         return await update.message.reply_text("❗ No articules to scrape. Add some with /add.")
#     messages = []
#     for art in arts:
#         try:
#             data = await scrape_in_thread(art)
#             messages.append(
#                 f"🛍️ {data['product_name']} ({art})\n"
#                 f"💰 {data['final_price']}  ⏰ {data['last_execution']}"
#             )
#         except Exception as e:
#             messages.append(f"❌ {art} – error: {e}")

#     await update.message.reply_text("\n\n".join(messages))

# async def echo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text(update.message.text)

# # ─── Main Entrypoint ─────────────────────────────────────────────────────────
# def main():
#     token = os.getenv("TELEGRAM_TOKEN")
#     if not token:
#         logger.critical("TELEGRAM_TOKEN environment variable is not set")
#         return

#     app = Application.builder().token(token).build()

#     app.add_handler(CommandHandler("start",  start))
#     app.add_handler(CommandHandler("help",   help_command))
#     app.add_handler(CommandHandler("add",    add_command))
#     app.add_handler(CommandHandler("scrape", scrape_command))
#     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

#     app.run_polling()

# if __name__ == "__main__":
#     main()
##### TELEGRAM SMALL LOGIC #####
