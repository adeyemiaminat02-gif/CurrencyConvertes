from sqlalchemy import select, desc, delete
from database import AsyncSessionLocal, UserPreference, ConversionHistory
from typing import List

class DatabaseService:
    @staticmethod
    async def add_history(user_id: int, amount: float, from_curr: str, to_curr: str, result: float):
        async with AsyncSessionLocal() as session:
            entry = ConversionHistory(
                user_id=user_id,
                amount=amount,
                from_currency=from_curr,
                to_currency=to_curr,
                converted_amount=result
            )
            session.add(entry)
            await session.commit()

            # Keep only the latest 10 records
            stmt = select(ConversionHistory).where(ConversionHistory.user_id == user_id).order_by(desc(ConversionHistory.timestamp))
            res = await session.execute(stmt)
            records = res.scalars().all()
            if len(records) > 10:
                for old in records[10:]:
                    await session.delete(old)
                await session.commit()

    @staticmethod
    async def get_history(user_id: int) -> List[ConversionHistory]:
        async with AsyncSessionLocal() as session:
            stmt = select(ConversionHistory).where(ConversionHistory.user_id == user_id).order_by(desc(ConversionHistory.timestamp)).limit(10)
            res = await session.execute(stmt)
            return res.scalars().all()

db_service = DatabaseService()
