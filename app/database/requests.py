from app.database.models import async_session
from app.database.models import User
from sqlalchemy import select

async def set_user(tg_id, user_name):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            session.add(User(tg_id=tg_id, user_name=user_name, question_count=0, scores=0, is_passing=False, is_passed=False))
            await session.commit()

async def set_is_passing(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        user.is_passing = True
        session.add(user)
        await session.commit()

async def set_is_passed(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        user.is_passing = False
        user.is_passed = True
        session.add(user)
        await session.commit()

async def get_is_passing(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
    return user.is_passing

async def get_is_passed(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
    return user.is_passed

async def set_default(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        user.scores = 0
        user.is_passing = False
        user.is_passed = False
        user.question_count = 0
        session.add(user)
        await session.commit()

async def set_scores(tg_id, score):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        user.scores += score
        session.add(user)
        await session.commit()

async def get_scores(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
    return user.scores

async def get_question_count(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user.question_count


async def set_question_count(tg_id, counter):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        user.question_count += counter
        session.add(user)
        await session.commit()