from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

model = SentenceTransformer('inkoziev/sbert_synonymy')


async def study_sim(a, b):
    t = 0.0
    if a['institute'] == b['institute']:
        t += 0.05
    if a['dorm'] == b['dorm'] == True:
        t += 0.05
    t += 0.04 - (abs(a['course'] - b['course']) / 6)
    t += max(0, 0.05 - (abs(a['age'] - b['age']) * 0.01))
    return t
    

async def find_distance(user1, user2):
    sim_ratio = 0.0
    try:
        sim = set(user1["hobbies"].keys()) & set(user2["hobbies"].keys())
        for cat in sim:
            point_sim = set(user1["hobbies"][cat]) & set(user2["hobbies"][cat])
            sim_ratio += 0.0952 * len(point_sim) + 0.0714
        sim_ratio += await study_sim(user1, user2)
        
        about1, about2 = user1['about_me'], user2['about_me']
        embeddings = model.encode([about1, about2])
        for em in embeddings[1:]:
            sim_ratio += min(0.25, cos_sim(a = embeddings[0], b = em).item())
            
        return sim_ratio
    except Exception as e:
        print(e)
        return 0.0
    