
# All instances of the DataHandler class should be here
# Все экземпляры класса DataHandler должны находиться здесь

import asyncio
import os
from utils.db_controller import DataHandler, User

PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


profiles = DataHandler(f"{PATH}/databases/profiles.db")


async def profiles_init():
    
    await profiles.add_tabble()
    await profiles.update_userlist()

async def init_all():
    print("[Data] Initialization started")
    await profiles_init()

asyncio.run(
    main = init_all()
)