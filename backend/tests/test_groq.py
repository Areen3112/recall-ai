
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import AsyncGroq


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


async def main():
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing from backend/.env")

    client = AsyncGroq(api_key=api_key)

    try:
        print(f"Testing Groq model: {model}")

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful customer support assistant."
                },
                {
                    "role": "user",
                    "content": (
                        "A customer's Bluetooth headphones disconnect "
                        "every 10 minutes. Give one concise opening "
                        "sentence acknowledging their issue."
                    )
                }
            ],
            max_completion_tokens=150,
        )

        print("\n--- GROQ RESPONSE ---")
        print(response.choices[0].message.content)
        print("\nGROQ CONNECTION TEST PASSED")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
