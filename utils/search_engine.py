from utils.data import profiles
from utils import sentences
import json

async def searcher(self_uid, count, min_ratio = 0.6, ignore_list = []):
    userlist = profiles.users
    result = []

    self_profile = await profiles.get_user(self_uid)
    for other_user in userlist:
        if other_user[0] in ignore_list:
            continue
        elif other_user[0] != self_uid:
            sim = await sentences.find_distance(
                        user1 = json.loads(self_profile.jstring),
                        user2 = json.loads(other_user[-1])
                    )
            if sim >= min_ratio:
                result.append(
                    (
                        other_user[0],
                        min(1.0, sim)
                    )
                )

    return sorted(result)[:min(count, len(result))]
    #for i in range(count):
