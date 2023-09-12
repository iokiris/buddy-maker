
# All instances of the DataHandler class should be here
# Все экземпляры класса DataHandler должны находиться здесь

import asyncio
from asyncio import Task
import os
from utils.db_controller import DataHandler, User

PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


profiles = DataHandler(f"{PATH}/databases/profiles.db")


