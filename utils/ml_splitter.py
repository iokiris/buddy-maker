
import json

def ml_split_fields(d: dict):
    '''
    age = d["person"]["age"]
    hometown = d["person"]["hometown"]
    institute = d["study_info"]["institute"]
    course = d["study_info"]["course"]
    dorm = d["study_info"]["lives_in_dorm"]
    hobbies = " ".join(d["hobbies"])
    about_me = d["about_me"]
    splitted = f"{age} {hometown} {institute} {course} {dorm} {hobbies} {about_me}"
    return splitted
    '''
    r = dict(
        age = d["person"]["age"],
        hometown = d["person"]["hometown"],
        institute = d["study_info"]["institute"],
        course = d["study_info"]["course"],
        dorm = d["study_info"]["lives_in_dorm"],
        hobbies = {},
        about_me = d["about_me"]
    )
    for i in d["hobbies"]:
        ic = d["ignore_case"]
        if i not in ic:
            r["hobbies"][i] = d["hobbies"][i]
    return json.dumps(r)