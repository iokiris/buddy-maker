

def ml_split_fields(d: dict):
    age = d["person"]["age"]
    hometown = d["person"]["hometown"]
    institute = d["study_info"]["institute"]
    course = d["study_info"]["course"]
    dorm = d["study_info"]["lives_in_dorm"]
    hobbies = " ".join(d["hobbies"]["visual"]).lower()
    about_me = d["about_me"]
    splitted = f"{age} {hometown} {institute} {course} {dorm} {hobbies} {about_me}"
    return splitted