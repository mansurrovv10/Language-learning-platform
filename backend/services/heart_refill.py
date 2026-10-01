import asyncio
import logging

from backend.config import HEART_REFILL_INTERVAL_SECONDS
from backend.database.db import SessionLocal
from backend.repositories.gamification_repo import GamificationRepository


logger = logging.getLogger(__name__)


async def refill_due_hearts() -> int:
    async with SessionLocal() as session:
        return await GamificationRepository(session).refill_due_hearts()


async def run_heart_refill_loop() -> None:
    while True:
        try:
            refilled = await refill_due_hearts()

            if refilled:
                logger.info("Refilled hearts for %s user(s)",refilled)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Heart refill pass failed")

        await asyncio.sleep(HEART_REFILL_INTERVAL_SECONDS)
