import os
import re
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from telegram.constants import ParseMode
from datetime import timedelta



from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from playwright.sync_api import sync_playwright
from typing import Optional  # Add this line

# Add this import at the top
from browser_pool import BrowserPool



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


DATA_ROOT = Path("data")  # top-level folder for all users

# ─── File Paths ──────────────────────────────────────────────────────────────
ARTICULES_FILE = Path("wb_articules.txt")
OUTPUT_FILE    = Path("wb_results.json")

# Add this after your imports, before the functions
# Global browser pool instance
browser_pool: Optional[BrowserPool] = None

# define users paths
def user_paths(user_id: int) -> tuple[Path, Path]:
    """
    Returns (articules_file, results_file) for the given user_id.
    Ensures the user directory exists.
    """
    user_dir = DATA_ROOT / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return (
        user_dir / "articules.txt",
        user_dir / "results.json"
    )

def load_articules_for(user_id: int) -> list[str]:
    articules_file, _ = user_paths(user_id)
    if not articules_file.exists():
        return []
    return [
        line.strip()
        for line in articules_file.read_text("utf-8").splitlines()
        if line.strip()
    ]

def append_articules_for(user_id: int, new_items: list[str]) -> tuple[int, int]:
    articules_file, _ = user_paths(user_id)
    existing = set(load_articules_for(user_id))
    added = skipped = 0

    with articules_file.open("a", encoding="utf-8") as f:
        for art in new_items:
            if art in existing:
                skipped += 1
            else:
                f.write(art + "\n")
                existing.add(art)
                added += 1

    return added, skipped

def load_results_for(user_id: int) -> list[dict]:
    _, results_file = user_paths(user_id)
    if not results_file.exists():
        return []
    return json.loads(results_file.read_text("utf-8"))

def save_results_for(user_id: int, data: list[dict]) -> None:
    _, results_file = user_paths(user_id)
    results_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

### Persisting Subscribers & Intervals ###
from pathlib import Path
import json

SUB_FILE      = Path("subscribers.txt")
INTERVAL_FILE = Path("intervals.json")

def load_subscribers() -> set[int]:
    if not SUB_FILE.exists():
        return set()
    return {int(u) for u in SUB_FILE.read_text().splitlines() if u}

def save_subscribers(subs: set[int]) -> None:
    SUB_FILE.write_text("\n".join(str(u) for u in subs) + "\n")

def load_intervals() -> dict[str, int]:
    if not INTERVAL_FILE.exists():
        return {}
    return json.loads(INTERVAL_FILE.read_text())

def save_intervals(data: dict[str, int]) -> None:
    INTERVAL_FILE.write_text(json.dumps(data, indent=2))
### Persisting Subscribers & Intervals ###


### Helper to (Re)Schedule a User’s Job ###
def schedule_compare_for(user_id: int, queue, interval: int):
    job_name = f"compare_{user_id}"
    # remove any existing job for this user
    for job in queue.get_jobs_by_name(job_name):
        job.schedule_removal()

    # schedule a new repeating job
    queue.run_repeating(
        callback=broadcast_one_user,
        interval=interval,
        first=interval,
        chat_id=user_id,
        name=job_name
    )

async def do_compare_for(user_id: int) -> list[str]:
    # 1) Load user’s existing data
    old_list = load_results_for(user_id)
    if not old_list:
        return ["❗ No previous data. Run /check first."]

    # 2) Build the old_map …
    old_map = {
        item["articule"]: (parse_price(item["final_price"]), idx)
        for idx, item in enumerate(old_list)
    }

    messages     = []
    updated_list = old_list.copy()

    # 3) Kick off parallel scrapes
    tasks = {
        art: asyncio.create_task(scrape_in_thread(art))
        for art in old_map
    }

    for art, task in tasks.items():
        try:
            new_data = await task
            now_ts   = datetime.utcnow().replace(microsecond=0).isoformat()
            new_data["last_execution"] = now_ts

            old_price, idx = old_map[art]
            new_price      = parse_price(new_data["final_price"])
            name           = new_data["product_name"]
            diff           = new_price - old_price
            sign           = "+" if diff > 0 else ""

            if new_price != old_price:
                messages.append(
                    f"🔔 {name}: {old_price:.2f} → <b>{new_price:.2f}</b> ({sign}{diff:.2f})"
                )
                updated_list[idx] = new_data
            else:
                messages.append(
                    f"ℹ️ {name}: unchanged at <b>{new_price:.2f}</b>"
                )
                updated_list[idx]["last_execution"] = now_ts

        except Exception as e:
            messages.append(f"❌ {art}: error: {e}")

    # 4) Persist the updated list
    save_results_for(user_id, updated_list)

    return messages
### Helper to (Re)Schedule a User’s Job ###

### Core Broadcast Callback ###
async def broadcast_one_user(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.chat_id
    #messages = await compute_compare_messages_for(user_id)
    messages = await do_compare_for(user_id)

    if messages:
        await context.bot.send_message(
            chat_id=user_id,
            text="\n".join(messages),
            parse_mode=ParseMode.HTML
        )
### Core Broadcast Callback ###

### /subscribe, /unsubscribe, /setinterval Handlers ###
async def subscribe_command(update, ctx):
    user_id = update.effective_user.id
    subs    = load_subscribers()
    if user_id in subs:
        return await update.message.reply_text("✅ Already subscribed.")

    subs.add(user_id)
    save_subscribers(subs)

    # pick their stored interval or default to 300s
    intervals = load_intervals()
    interval  = intervals.get(str(user_id), 300)
    schedule_compare_for(user_id, ctx.job_queue, interval)

    await update.message.reply_text(f"🟢 Subscribed! You’ll get updates every {interval//60} min.")

async def unsubscribe_command(update, ctx):
    user_id = update.effective_user.id
    subs    = load_subscribers()
    if user_id not in subs:
        return await update.message.reply_text("ℹ️ You’re not subscribed.")

    subs.remove(user_id)
    save_subscribers(subs)

    # remove their scheduled job
    for job in ctx.job_queue.get_jobs_by_name(f"compare_{user_id}"):
        job.schedule_removal()

    await update.message.reply_text("🔴 Unsubscribed from periodic updates.")

async def setinterval_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        # 1) Ensure the user supplied an argument
        if not ctx.args:
            return await update.message.reply_text(
                "Usage: /setinterval <minutes>"
            )

        # 2) Parse & validate
        try:
            minutes = int(ctx.args[0])
            if minutes <= 0:
                raise ValueError()
        except ValueError:
            return await update.message.reply_text(
                "Please provide a positive integer for minutes."
            )

        user_id = update.effective_user.id

        # 3) Store the interval preference (don't schedule job yet!)
        intervals = load_intervals()
        intervals[str(user_id)] = minutes * 60  # Convert to seconds
        save_intervals(intervals)

        # 4) Only schedule job if user is already subscribed
        subs = load_subscribers()
        if user_id in subs:
            # User is subscribed, update their existing job
            schedule_compare_for(user_id, ctx.job_queue, minutes * 60)
            await update.message.reply_text(
                f"⏰ Interval updated to {minutes} min. Updates will continue."
            )
        else:
            # User is not subscribed, just store the preference
            await update.message.reply_text(
                f"⏰ Interval set to {minutes} min. Use /subscribe to start receiving updates."
            )

    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text(
            f"❌ Failed to set interval: {e}"
        )

# async def setinterval_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
#     try:
#         # 1) Ensure the user supplied an argument
#         if not ctx.args:
#             return await update.message.reply_text(
#                 "Usage: /setinterval <minutes>"
#             )

#         # 2) Parse & validate
#         try:
#             minutes = int(ctx.args[0])
#             if minutes <= 0:
#                 raise ValueError()
#         except ValueError:
#             return await update.message.reply_text(
#                 "Please provide a positive integer for minutes."
#             )

#         user_id = update.effective_user.id

#         # 3) Remove any existing job(s) named for this user
#         existing = ctx.job_queue.get_jobs_by_name(str(user_id))
#         for job in existing:
#             job.schedule_removal()

#         # 4) Schedule the repeating job with the new interval
#         ctx.job_queue.run_repeating(
#             broadcast_one_user,               # your callback
#             interval=timedelta(minutes=minutes),
#             first=0,                          # run immediately
#             chat_id=update.effective_chat.id,   # ← pass the chat ID here
#             name=str(update.effective_chat.id),
#             # name=str(user_id),                # so get_jobs_by_name() finds it
#             # data=user_id                      # passed into context.job.data
#         )

#         # 5) Confirm to the user
#         await update.message.reply_text(
#             f"⏰ Interval set to {minutes} min."
#         )

#     except Exception as e:
#         # Log full traceback to console
#         traceback.print_exc()
#         # Inform the user something went wrong
#         await update.message.reply_text(
#             f"❌ Failed to set interval: {e}"
#         )
### /subscribe, /unsubscribe, /setinterval Handlers ###

# ─── Sync Scraper ────────────────────────────────────────────────────────────
async def get_wb_product_details_by_articule(art: str) -> dict:
    """Async version using browser pool"""
    global browser_pool
    
    if not browser_pool:
        raise RuntimeError("Browser pool not initialized")
    
    async with browser_pool.get_page() as page:
        url = f"https://www.wildberries.by/catalog/{art}/detail.aspx"
        
        try:
            # Navigate to page with more reliable wait strategy
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            # Wait for either the title or price to appear (whichever comes first)
            try:
                await page.wait_for_selector(".product-page__title, .price-block__final-price", 
                                           timeout=10000, state="visible")
            except:
                # If that fails, just wait a bit
                await asyncio.sleep(3)
            
            # Wait a bit for dynamic content to load
            await asyncio.sleep(2)
            
            # Wait for product name with multiple selectors
            name_selectors = [
                ".product-page__title",
                "h1.product-page__title", 
                "[data-testid='product-title']",
                "h1",
                ".product-page__title-text",
                ".product-page__title h1",
                ".product-page__title span"
            ]
            
            product_name = None
            for selector in name_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    product_name = await element.text_content()
                    if product_name and product_name.strip():
                        break
                except:
                    continue
            
            if not product_name:
                # Try JavaScript as fallback
                try:
                    product_name = await page.evaluate("""
                        () => {
                            const selectors = [
                                '.product-page__title',
                                'h1.product-page__title',
                                '[data-testid="product-title"]',
                                'h1',
                                '.product-page__title-text'
                            ];
                            for (const selector of selectors) {
                                const el = document.querySelector(selector);
                                if (el && el.textContent.trim()) {
                                    return el.textContent.trim();
                                }
                            }
                            return null;
                        }
                    """)
                except:
                    pass
                
            if not product_name:
                raise Exception(f"Product name not found for {art}")
            
            # Wait for price with multiple selectors
            price_selectors = [
                "ins.price-block__final-price.red-price",
                ".price-block__final-price",
                "[data-testid='price']",
                ".price",
                ".price-block__final-price ins",
                ".price-block__final-price .red-price",
                ".price-block__final-price span",
                ".price-block__final-price .price",
                ".product-page__price .price",
                ".product-page__price ins",
                ".product-page__price .red-price"
            ]
            
            final_price = None
            for selector in price_selectors:
                try:
                    # Try locator first
                    element = await page.locator(selector).first
                    await element.wait_for(state="visible", timeout=3000)
                    final_price = await element.text_content()
                    if final_price and final_price.strip():
                        break
                except:
                    try:
                        # Try direct selector
                        element = await page.wait_for_selector(selector, timeout=3000)
                        final_price = await element.text_content()
                        if final_price and final_price.strip():
                            break
                    except:
                        continue
            
            if not final_price:
                # Try JavaScript as fallback
                try:
                    final_price = await page.evaluate("""
                        () => {
                            const selectors = [
                                'ins.price-block__final-price.red-price',
                                '.price-block__final-price',
                                '[data-testid="price"]',
                                '.price',
                                '.price-block__final-price ins',
                                '.price-block__final-price .red-price',
                                '.product-page__price .price',
                                '.product-page__price ins'
                            ];
                            for (const selector of selectors) {
                                const el = document.querySelector(selector);
                                if (el && el.textContent.trim()) {
                                    return el.textContent.trim();
                                }
                            }
                            return null;
                        }
                    """)
                except:
                    pass
                
            if not final_price:
                # Log the page content for debugging
                page_content = await page.content()
                logger.error(f"Price not found for {art}. Page title: {await page.title()}")
                logger.error(f"Page URL: {page.url}")
                raise Exception(f"Price not found for {art}")
            
            return {
                "articule": art,
                "product_name": product_name.strip(),
                "final_price": final_price.strip(),
                "last_execution": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Error scraping {art}: {e}")
            raise

# def get_wb_product_details_by_articule(art: str) -> dict:
#     with sync_playwright() as p:
#         browser = p.chromium.launch(channel="chrome", headless=False, args=["--log-level=3"])
#         page    = browser.new_page()
#         url     = f"https://www.wildberries.by/catalog/{art}/detail.aspx"
#         page.goto(url, wait_until="load")

#         name_el  = page.wait_for_selector(".product-page__title",       state="visible", timeout=60000)
#         final_el = page.locator("ins.price-block__final-price.red-price").first
#         final_el.wait_for(state="visible", timeout=60000)

#         data = {
#             "articule":       art,
#             "product_name":   name_el.text_content().strip(),
#             "final_price":    final_el.text_content().strip(),
#             "last_execution": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
#         }
#         browser.close()
#         return data

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

# async def scrape_in_thread(art: str) -> dict:
#     loop = asyncio.get_running_loop()
#     return await loop.run_in_executor(None, get_wb_product_details_by_articule, art)

async def scrape_in_thread(art: str) -> dict:
    """Wrapper for backward compatibility"""
    return await get_wb_product_details_by_articule(art)

# ─── Bot Handlers ────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = (
        f"Hi {user.mention_markdown_v2()}\\!  \n"
        "To start using this bot, you have to prepare your data:\n"
        "1\. Add product with `add` command\n"
        "2\. Execute `check` command to collect data about interested product\n"
        "3\. Read instructions below to manage your tracking list\n\n\n"
        "Send `/check <articule>` to fetch product details\.\n"
        "`/add <id1,id2,…>` to add new articules\.\n"
        "`/remove <art1,art2,…> or /remove art1 art2` to remove some products from you tracking list\.\n"
        "`/show` to get articule: product name that you are currently tracking\.\n"
        "`/compare` to compare latest prices with current ones\.\n"
        "`/subscribe` to start product tracking \(default value is evey 5 mins\)\.\n"
        "`/unsubscribe` to stop product tracking\.\n"
        "`/setinterval <minutes>` to set up your own tracking interval if you are subscribed\.\n"
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
    user_id = update.effective_user.id
    raw     = " ".join(ctx.args).strip()
    if not raw:
        return await update.message.reply_text("Usage: /add <art1,art2 …>")

    parts    = re.split(r"[,\s;]+", raw)
    new_ids  = [p for p in (pt.strip() for pt in parts) if p]
    added, skipped = append_articules_for(user_id, new_ids)

    await update.message.reply_text(
        f"✅ Added {added} articule(s), skipped {skipped} duplicates."
    )

async def scrape_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # 1. Load their articules
    arts = load_articules_for(user_id)
    if not arts:
        return await update.message.reply_text("❗ You have no articules. Use /add first.")

    # 2. Kick off parallel scrapes with rate limiting
    semaphore = asyncio.Semaphore(2)  # Limit concurrent requests
    
    async def scrape_with_rate_limit(art: str):
        async with semaphore:
            try:
                result = await scrape_in_thread(art)
                await asyncio.sleep(1)  # Rate limiting
                return result
            except Exception as e:
                return {"error": str(e), "articule": art}
    
    tasks = [scrape_with_rate_limit(art) for art in arts]
    results, replies = [], []

    for coro in asyncio.as_completed(tasks):
        try:
            data = await coro
            if "error" in data:
                replies.append(f"❌ {data['articule']}: {data['error']}")
            else:
                results.append(data)
                replies.append(f"✅ {data['product_name']}: <b>{data['final_price']}</b>")
        except Exception as e:
            replies.append(f"❌ error: {e}")

    # 3. Persist per-user JSON (only successful results)
    if results:
        save_results_for(user_id, results)

    # 4. Send summary
    await update.message.reply_text(
        "\n".join(replies),
        parse_mode=ParseMode.HTML
    )

# async def scrape_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
#     user_id = update.effective_user.id

#     # 1. Load their articules
#     arts = load_articules_for(user_id)
#     if not arts:
#         return await update.message.reply_text("❗ You have no articules. Use /add first.")

#     # 2. Kick off parallel scrapes
#     tasks = [scrape_in_thread(art) for art in arts]
#     results, replies = [], []

#     for coro in asyncio.as_completed(tasks):
#         try:
#             data = await coro
#             results.append(data)
#             replies.append(f"✅ {data['product_name']}: <b>{data['final_price']}</b>")
#         except Exception as e:
#             replies.append(f"❌ error: {e}")

#     # 3. Persist per-user JSON
#     save_results_for(user_id, results)

#     # 4. Send summary
#     await update.message.reply_text(
#         "\n".join(replies),
#         parse_mode=ParseMode.HTML
#     )

async def echo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

async def compare_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id  = update.effective_user.id
    messages = await do_compare_for(user_id)

    await update.message.reply_text(
        "\n".join(messages),
        parse_mode=ParseMode.HTML
    )

### SHOW
async def show_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    results = load_results_for(user_id)
    if not results:
        return await update.message.reply_text("❗ No products tracked yet.")

    lines = [
        f"📦 <b>{item['articule']}</b>: {item['product_name']}"
        for item in results
    ]
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

async def remove_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    raw     = " ".join(ctx.args).strip()
    if not raw:
        return await update.message.reply_text("Usage: /remove <art1,art2 …>")

    parts     = re.split(r"[,\s;]+", raw)
    to_remove = {p.strip() for p in parts if p.strip()}

    existing = load_articules_for(user_id)
    if not existing:
        return await update.message.reply_text("❗ No articules to remove.")

    kept, removed = [], []
    for art in existing:
        if art in to_remove:
            removed.append(art)
        else:
            kept.append(art)

    if not removed:
        return await update.message.reply_text(
            f"ℹ️ None of {', '.join(to_remove)} found."
        )

    articules_file, results_file = user_paths(user_id)
    articules_file.write_text("\n".join(kept) + "\n", encoding="utf-8")

    if results_file.exists():
        data = load_results_for(user_id)
        data = [item for item in data if item["articule"] not in to_remove]
        save_results_for(user_id, data)

    await update.message.reply_text(
        f"✅ Removed {len(removed)} articule(s): {', '.join(removed)}"
    )

# ─── Main Entrypoint ─────────────────────────────────────────────────────────
def main():

    global browser_pool

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
    app.add_handler(CommandHandler("show", show_command))
    app.add_handler(CommandHandler("remove", remove_command))
    app.add_handler(CommandHandler("subscribe",   subscribe_command))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    app.add_handler(CommandHandler("setinterval", setinterval_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Restore jobs for existing subscribers
    subs      = load_subscribers()
    intervals = load_intervals()
    for uid in subs:
        interval = intervals.get(str(uid), 300)
        schedule_compare_for(uid, app.job_queue, interval)

    # Initialize browser pool in the same event loop
    async def setup_and_run():
        global browser_pool
        browser_pool = BrowserPool(max_browsers=3)
        await browser_pool.initialize()
        logger.info("Browser pool initialized successfully")
        
        try:
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            
            # Keep the bot running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            await app.stop()
            if browser_pool:
                await browser_pool.cleanup()

    # Run everything in one event loop
    asyncio.run(setup_and_run())
    # app.run_polling()

if __name__ == "__main__":
    main()