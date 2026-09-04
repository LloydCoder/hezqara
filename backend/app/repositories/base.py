from sqlalchemy.ext.asyncio import AsyncSession

class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session
