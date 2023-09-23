'''
# DataBase controller. 
# All operations with database must be performed there
'''

import sqlite3
#from ml_splitter import MLSplitter

class DataHandler:

    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.cursor = self.db.cursor()

    async def update_userlist(self):
        query = "SELECT * FROM users"
        self.cursor.execute(query)
        self.users = self.cursor.fetchall()
    
    async def add_tabble(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            userid   INT  PRIMARY KEY,
            photo_id TEXT,
            profile  TEXT,
            ml_split TEXT
        );
            """)
        
    async def get_user(self, user_id):
        for r in self.users:
            if r[0] == user_id:
                return User(r[0], r[1], r[2], r[3])
        return None
    

    async def add_user(self, User):
        user = self.cursor.execute(
            f"SELECT 1 FROM users WHERE userid == {User.uid}"
        ).fetchone()
        if not user:
            self.cursor.execute(
                "INSERT INTO users VALUES(?, ?, ?, ?)",
                (User.uid, User.photo_id, User.profile, User.jstring)
            )
        else:
            self.cursor.execute(
                f"UPDATE users SET photo_id = ?, profile = ?, ml_split = ? WHERE userid = ?", (User.photo_id, User.profile, User.jstring, User.uid)
            )
        self.db.commit()
        await self.update_userlist()

    async def remove_user(self, uid):
        self.cursor.execute(
            "DELETE FROM users WHERE userid == ?",
            (uid, )
        )
        self.db.commit()
        await self.update_userlist()

class User:
    def __init__(self, uid, photo_id, profile, jstring):
        self.uid = uid
        self.photo_id = photo_id
        self.profile = profile
        self.jstring = jstring
