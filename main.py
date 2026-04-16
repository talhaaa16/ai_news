import asyncio
import requests
import os
from telegram import Bot
from datetime import datetime
from google import genai
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# ---------------- CONFIG ----------------

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

LAST_NEWS_FILE = "last_news.txt"
# ----------------------------------------

bot = Bot(token=TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

def get_ai_tech_news():
    """Fetch trending AI and Tech news articles."""
    query = "AI OR artificial intelligence OR machine learning OR technology"
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": NEWS_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("status") != "ok":
        print("⚠️ API Error:", data)
        return None

    articles = data.get("articles", [])
    if not articles:
        print("❌ No tech or AI news found.")
        return None

    # Load last sent URL
    last_url = None
    if os.path.exists(LAST_NEWS_FILE):
        with open(LAST_NEWS_FILE, "r") as f:
            last_url = f.read().strip()

    # Pick first unseen article
    for article in articles:
        if article.get("url") != last_url:
            with open(LAST_NEWS_FILE, "w") as f:
                f.write(article.get("url"))
            return article

    print("⚠️ No new articles found (all sent already).")
    return None


def summarize_news(title, description, content, url):
    """Summarize or explain the news using Gemini."""
    try:
        text = f"{title}\n\n{description}\n\n{content}"
        prompt = f"""
        You are a tech journalist. Explain this news in a simple, clear, and engaging way (5–6 lines max).
        Focus on what’s new in technology or AI, and why it matters.
        News:
        {text}
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        summary = response.text.strip()
        return f"🧠 *{title}*\n\n{summary}\n\n🔗 [Read more here]({url})"

    except Exception:
        # Fallback if Gemini not available
        short = description if description else "No description available."
        return f"🧠 *{title}*\n\n_{short}_\n\n🔗 [Read more here]({url})"


async def send_news():
    article = get_ai_tech_news()
    if not article:
        msg = "❌ No new AI/Tech news available right now."
    else:
        msg = summarize_news(
            article.get("title", ""),
            article.get("description", ""),
            article.get("content", ""),
            article.get("url", "")
        )

    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown", disable_web_page_preview=False)
    print(f"[{datetime.now()}] ✅ News sent successfully!")


async def main():
    scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")  # IST Timezone
    scheduler.add_job(send_news, "cron", hour=10, minute=27)  # 9:00 AM daily
    scheduler.start()

    print("🤖 Scheduler started. Waiting for jobs...")
    while True:
        await asyncio.sleep(3600)  # Keep the script alive


if __name__ == "__main__":
    asyncio.run(main())
