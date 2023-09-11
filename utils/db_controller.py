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
    def add_tabble(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            userid   INT  PRIMARY KEY,
            photo_id TEXT,
            profile  TEXT,
            ml_split TEXT
        );
            """)
    def add_user(self, User):
        user = self.cursor.execute(
            f"SELECT 1 FROM users WHERE userid == {User.uid}"
        ).fetchone()
        if not user:
            self.cursor.execute(
                "INSERT INTO users VALUES(?, ?, ?, ?)",
                (User.uid, User.photo_id, User.profile, User.ml_split)
            )
        else:
            #FIXME выдает  near "18.": syntax error
            self.cursor.execute(
                f"UPDATE users SET photo_id={User.photo_id}, profile={User.profile}, ml_split={User.ml_split} WHERE userid == {User.uid}"
            )
        self.db.commit()
    def get_user(self, user_id):
        query = "SELECT * FROM users"
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        for r in result:
            if r[0] == user_id:
                return User(r[0], r[1], r[2], r[3])
        return None
class User:
    def __init__(self, uid, photo_id, profile, ml_split):
        self.uid = uid
        self.photo_id = photo_id
        self.profile = profile
        self.ml_split = ml_split