    
    
def get_joint_combinations(chosen_joint):
    if chosen_joint == "LEFT_SHOULDER":
        return "RIGHT_SHOULDER", "LEFT_ELBOW", "LEFT_SHOULDER"
    elif chosen_joint == "RIGHT_SHOULDER":
        return "LEFT_SHOULDER", "RIGHT_ELBOW", "RIGHT_SHOULDER"
    elif chosen_joint == "LEFT_ELBOW":
        return "LEFT_SHOULDER", "LEFT_WRIST", "LEFT_ELBOW"
    elif chosen_joint == "RIGHT_ELBOW":
        return "RIGHT_SHOULDER", "RIGHT_WRIST", "RIGHT_ELBOW"
    # Add more cases for other joints as needed
    else:
        return "LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_ELBOW"
