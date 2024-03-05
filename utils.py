#utils.py
def get_joint_combinations(chosen_joint):
    if chosen_joint == "LEFT_SHOULDER":
        return "RIGHT_SHOULDER", "LEFT_ELBOW", "LEFT_SHOULDER"
    elif chosen_joint == "RIGHT_SHOULDER":
        return "LEFT_SHOULDER", "RIGHT_ELBOW", "RIGHT_SHOULDER"

    elif chosen_joint == "LEFT_ELBOW":
        return "LEFT_SHOULDER", "LEFT_WRIST", "LEFT_ELBOW"
    elif chosen_joint == "RIGHT_ELBOW":
        return "RIGHT_SHOULDER", "RIGHT_WRIST", "RIGHT_ELBOW"

    elif chosen_joint == "RIGHT_WRIST":
        return "RIGHT_ELBOW", "RIGHT_INDEX", "RIGHT_WRIST"
    elif chosen_joint == "LEFT_WRIST":
        return "LEFT_ELBOW", "LEFT_INDEX", "LEFT_WRIST"
    
    elif chosen_joint == "RIGHT_HIP":
        return "RIGHT_SHOULDER", "RIGHT_KNEE", "RIGHT_HIP"
    elif chosen_joint == "LEFT_HIP":
        return "LEFT_SHOULDER", "LEFT_KNEE", "LEFT_HIP"

    elif chosen_joint == "RIGHT_KNEE":
        return "RIGHT_HIP", "RIGHT_ANKLE", "RIGHT_KNEE"
    elif chosen_joint == "LEFT_KNEE":
        return "LEFT_HIP", "LEFT_ANKLE", "LEFT_KNEE"
    
    elif chosen_joint == "RIGHT_ANKLE":
        return "RIGHT_KNEE", "RIGHT_HEEL", "RIGHT_ANKLE"
    elif chosen_joint == "LEFT_ANKLE":
        return "LEFT_KNEE", "LEFT_HEEL", "LEFT_ANKLE"


    # Add more cases for other joints as needed
    else:
        return "LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_ELBOW"
