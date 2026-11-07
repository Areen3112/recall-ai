
import asyncio
import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from hindsight_client import Hindsight


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


async def main():
    api_key = os.getenv("HINDSIGHT_API_KEY")
    base_url = os.getenv(
        "HINDSIGHT_BASE_URL",
        "https://api.vectorize.io",
    )

    if not api_key:
        raise RuntimeError("HINDSIGHT_API_KEY is missing from backend/.env")

    client = Hindsight(
        base_url=base_url,
        api_key=api_key,
    )

    # A fresh bank ID makes this test safe to rerun.
    bank_id = f"recall-smoke-{uuid4().hex[:12]}"

    try:
        print("\n[1/3] Creating customer memory bank...")

        await client.acreate_bank(
            bank_id=bank_id,
            name="Recall AI - Sarah Mitchell",
            mission=(
                "Remember customer support history, "
                "previous troubleshooting attempts, "
                "preferences, and confirmed resolutions."
            ),
            background=(
                "This memory bank belongs to a fictional demo customer "
                "used to test Recall AI."
            ),
        )

        print("Memory bank created:", bank_id)

        print("\n[2/3] Retaining customer interaction...")

        await client.aretain(
            bank_id=bank_id,
            content=(
                "Sarah Mitchell reported that her Bluetooth headphones "
                "disconnect approximately every 10 minutes. Restarting "
                "Bluetooth did not solve the problem. She prefers "
                "step-by-step troubleshooting instructions."
            ),
            context="Customer support interaction from a previous session.",
            metadata={
                "customer": "Sarah Mitchell",
                "category": "bluetooth_connectivity",
                "source": "smoke_test",
            },
        )

        print("Customer interaction retained.")

        print("\n[3/3] Recalling customer history...")

        result = await client.arecall(
            bank_id=bank_id,
            query=(
                "What problem did Sarah experience, "
                "what troubleshooting has already failed, "
                "and how does she prefer receiving instructions?"
            ),
        )

        print("\n--- HINDSIGHT RECALL RESULT ---")
        print(result)

        print("\n--- RESULT DETAILS ---")
        print("Result type:", type(result).__name__)
        print("Results:", getattr(result, "results", None))

        print("\nHINDSIGHT CONNECTION TEST PASSED")

    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
