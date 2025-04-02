# admin_utils.py

def get_user_count(collection):
    """Get the total number of users"""
    return collection.count_documents({})  # ✅ Use .count_documents() method

def get_exercise_count(collection):
    """Get the total number of exercise videos"""
    return collection.count_documents({})  # ✅ Correct usage

def get_food_count(collection):
    """Get the total number of food entries"""
    return collection.count_documents({})  # ✅ Correct usage

def get_meal_plan_count(collection):
    """Get the total number of meal plans"""
    return collection.count_documents({})  # ✅ Correct usage
