import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
from config import settings
# explicitly set straico api key from environment if needed
settings.STRAICO_API_KEY = os.environ.get("STRAICO_API_KEY", "")

from intelligence.summarizer import summarize_allocation

async def main():
    print(f"API KEY length: {len(settings.STRAICO_API_KEY)}")
    res = await summarize_allocation({"test": "data"}, 4.2)
    print("Result:")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
