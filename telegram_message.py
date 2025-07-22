import os
import re
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from telegram.constants import ParseMode


from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from playwright.sync_api import sync_playwright

# ─── Logging Configuration ───────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# ─── File Paths ──────────────────────────────────────────────────────────────
ARTICULES_FILE = Path("wb_articules.txt")
OUTPUT_FILE    = Path("wb_results.json")

# ─── Sync Scraper ────────────────────────────────────────────────────────────
def get_wb_product_details_by_articule(art: str) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False, args=["--log-level=3"])
        page    = browser.new_page()
        url     = f"https://www.wildberries.by/catalog/{art}/detail.aspx"
        page.goto(url, wait_until="networkidle")

        name_el  = page.wait_for_selector(".product-page__title",       state="visible", timeout=50000)
        final_el = page.locator("ins.price-block__final-price.red-price").first
        final_el.wait_for(state="visible", timeout=50000)

        data = {
            "articule":       art,
            "product_name":   name_el.text_content().strip(),
            "final_price":    final_el.text_content().strip(),
            "last_execution": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        }
        browser.close()
        return data

# ─── Helpers ─────────────────────────────────────────────────────────────────
def load_articules() -> list[str]:
    if not ARTICULES_FILE.exists():
        return []
    return [l.strip() for l in ARTICULES_FILE.read_text("utf-8").splitlines() if l.strip()]

def append_articules(new_items: list[str]) -> tuple[int,int]:
    """
    Append each unique articule to the file.
    Returns (added_count, skipped_count).
    """
    existing = set(load_articules())
    added, skipped = 0, 0

    with ARTICULES_FILE.open("a", encoding="utf-8") as f:
        for art in new_items:
            if art in existing:
                skipped += 1
            else:
                f.write(art + "\n")
                existing.add(art)
                added += 1

    return added, skipped

def parse_price(price_str: str) -> float:
    m = re.search(r"[\d\s]+,\d{2}", price_str)
    return float(m.group().replace(" ", "").replace(",", "."))

async def scrape_in_thread(art: str) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_wb_product_details_by_articule, art)

# ─── Bot Handlers ────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = (
        f"Hi {user.mention_markdown_v2()}\\!  \n"
        "Send `/check <articule>` to fetch product details\.\n"
        "`/add <id1,id2,…>` to add new articules\.\n"
        "`/compare` to compare latest prices with current ones\."
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN_V2
    )


async def help_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await start(update, ctx)

async def add_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /add <id> or /add <id1,id2,id3> or /add id1 id2
    """
    raw = " ".join(ctx.args).strip()
    if not raw:
        return await update.message.reply_text("Usage: /add <articule1,articule2 ...>")

    # split on commas, semicolons or whitespace
    parts = re.split(r"[,\s;]+", raw)
    new_ids = [p for p in (pt.strip() for pt in parts) if p]

    added, skipped = append_articules(new_ids)
    await update.message.reply_text(
        f"✅ Added {added} articule(s), skipped {skipped} already present."
    )

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

async def scrape_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    # load your articules
    if ARTICULES_FILE.exists():
        arts = [l.strip() for l in ARTICULES_FILE.read_text("utf-8").splitlines() if l.strip()]
    else:
        return await update.message.reply_text("❗ No articules to scrape.")

    results = []
    replies = []

    # fire off scrapes in parallel
    tasks = [scrape_in_thread(art) for art in arts]
    for coro in asyncio.as_completed(tasks):
        try:
            data = await coro
            results.append(data)
            replies.append(f"✅ {data['product_name']}: {data['final_price']}")
        except Exception as e:
            replies.append(f"❌ error: {e}")

    # write JSON file
    OUTPUT_FILE.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # send summary back to user
    await update.message.reply_text("\n".join(replies))


async def echo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

async def compare_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    # 1) Load existing JSON
    if not OUTPUT_FILE.exists():
        return await update.message.reply_text(
            "❗ No previous data. Run /scrape first to create wb_results.json."
        )

    old_list = json.loads(OUTPUT_FILE.read_text("utf-8"))
    # Map articule -> (old_price, index)
    old_map = {
        item["articule"]: (parse_price(item["final_price"]), idx)
        for idx, item in enumerate(old_list)
    }
    if not old_map:
        return await update.message.reply_text(
            "❗ wb_results.json is empty. Run /check first."
        )

    messages     = []
    updated_list = old_list.copy()
    now_ts       = datetime.utcnow().replace(microsecond=0).isoformat()

    # 2) Scrape in parallel
    tasks = {
        art: asyncio.create_task(scrape_in_thread(art))
        for art in old_map
    }

    for art, task in tasks.items():
        try:
            new_data = await task
            # normalize timestamp (drop microseconds, no Z)
            new_data["last_execution"] = datetime.utcnow().replace(microsecond=0).isoformat()

            new_price = parse_price(new_data["final_price"])
            old_price, idx = old_map[art]

            if new_price != old_price:
                diff = new_price - old_price
                sign = "+" if diff > 0 else ""
                messages.append(
                    f"🔔 {art}: {old_price:.2f}→{new_price:.2f} ({sign}{diff:.2f})"
                )
                # replace entire record
                updated_list[idx] = new_data
            else:
                messages.append(f"ℹ️ {art}: unchanged at {new_price:.2f}")
                # just update timestamp in existing record
                updated_list[idx]["last_execution"] = new_data["last_execution"]

        except Exception as e:
            messages.append(f"❌ {art}: error: {e}")

    # 3) Overwrite JSON with updated_list
    OUTPUT_FILE.write_text(
        json.dumps(updated_list, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 4) Report back
    await update.message.reply_text("\n".join(messages))


# ─── Main Entrypoint ─────────────────────────────────────────────────────────
def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.critical("TELEGRAM_TOKEN environment variable is not set")
        return

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("help",   help_command))
    app.add_handler(CommandHandler("add",    add_command))
    app.add_handler(CommandHandler("check", scrape_command))
    app.add_handler(CommandHandler("compare", compare_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    app.run_polling()

if __name__ == "__main__":
    main()