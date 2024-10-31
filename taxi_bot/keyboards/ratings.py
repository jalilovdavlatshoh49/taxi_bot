from db.database import DriverRating, AsyncSessionLocal
from sqlalchemy import select

# Функсияи кӯмакӣ барои ҳисоб кардани баҳои миёна
async def calculate_avg_rating(driver_id):
    session = AsyncSessionLocal()
    ratings_result = await session.execute(select(DriverRating).where(DriverRating.driver_id == driver_id))
    ratings = ratings_result.scalars().all()
    total_ratings = len(ratings)
    sum_ratings = sum(rating.rating for rating in ratings)

    if total_ratings > 0:
        return sum_ratings / total_ratings
    else:
        return 