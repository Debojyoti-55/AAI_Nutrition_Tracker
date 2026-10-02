import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient

# ==========================================
# 1. DATABASE SETUP & CONNECTION
# ==========================================

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI is missing. Please check your .env file.")

# Connect to MongoDB and select the specific database and collections
db = MongoClient(MONGO_URI)["nutrition_agent_db"]

users_col = db["users"]                  # Stores biometrics (weight, height, goals)
logs_col = db["intake_logs"]             # Stores every individual meal eaten
summaries_col = db["daily_summaries"]    # Stores the running total for today


# ==========================================
# 2. USER PROFILE FUNCTIONS
# ==========================================

def save_user_profile(user_id: str, weight_kg: float, height_cm: float, preferences: list = None, target_protein_g: float = 120.0, target_calories: float = 2000.0) -> dict:
    """Calculates BMI and saves the user's baseline goals."""
    
    height_meters = height_cm / 100.0
    bmi = round(weight_kg / (height_meters ** 2), 2)

    profile_data = {
        "user_id": user_id,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "bmi": bmi,
        "preferences": preferences or ["vegetarian"], 
        "targets": {
            "calories": target_calories,
            "protein_g": target_protein_g
        },
        "updated_at": datetime.now(timezone.utc)
    }

    # Upsert means: Update the user if they exist, create them if they don't
    users_col.update_one({"user_id": user_id}, {"$set": profile_data}, upsert=True)
    return profile_data

def get_user_profile(user_id: str) -> dict:
    """Retrieves the user's profile data."""
    return users_col.find_one({"user_id": user_id}, {"_id": 0})


# ==========================================
# 3. MEAL LOGGING & TRACKING FUNCTIONS
# ==========================================

def log_meal_intake(user_id: str, dish_name: str, weight_grams: float, nutrients: dict) -> dict:
    """Saves the meal to history and adds the macros to today's running total."""
    
    now = datetime.now(timezone.utc)
    today_date = now.strftime("%Y-%m-%d")

    # STEP A: Save this specific meal for the history charts
    meal_entry = {
        "user_id": user_id,
        "dish_name": dish_name,
        "weight_g": weight_grams,
        "nutrients": nutrients,
        "timestamp": now
    }
    result = logs_col.insert_one(meal_entry)
    meal_entry["_id"] = str(result.inserted_id)

    # STEP B: Add these macros to today's running total
    # The "$inc" operator tells MongoDB to mathematically ADD these numbers to the existing database values
    summaries_col.update_one(
        {"user_id": user_id, "date": today_date},
        {
            "$inc": {
                "total_meals": 1,
                "total_protein_g": nutrients.get("protein_g", 0.0),
                "total_carbs_g": nutrients.get("carbs_g", 0.0),
                "total_fat_g": nutrients.get("fat_g", 0.0),
                "total_vitc_mg": nutrients.get("vitc_mg", 0.0),
                "total_iron_mg": nutrients.get("iron_mg", 0.0)
            }
        },
        upsert=True # If this is the first meal of the day, create a new document starting at 0
    )

    return meal_entry

def get_daily_intake_summary(user_id: str) -> dict:
    """Quickly fetches today's running totals."""
    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return summaries_col.find_one({"user_id": user_id, "date": today_date}, {"_id": 0}) or {}

def get_daily_status_and_gaps(user_id: str) -> dict:
    """Compares what the user has eaten today against their daily goals."""
    
    profile = get_user_profile(user_id)
    if not profile:
        return {"error": "User profile not found."}

    todays_totals = get_daily_intake_summary(user_id)

    # Extract today's eaten macros (default to 0 if nothing eaten yet)
    eaten_protein = todays_totals.get("total_protein_g", 0.0)
    eaten_carbs = todays_totals.get("total_carbs_g", 0.0)
    eaten_fat = todays_totals.get("total_fat_g", 0.0)

    # Standard formula to convert macros to calories
    eaten_calories = round((eaten_protein * 4) + (eaten_carbs * 4) + (eaten_fat * 9), 1)

    # Calculate what is left for the day
    protein_left = round(profile["targets"]["protein_g"] - eaten_protein, 1)
    calories_left = round(profile["targets"]["calories"] - eaten_calories, 1)

    return {
        "user_id": user_id,
        "bmi": profile["bmi"],
        "preferences": profile.get("preferences", []),
        "eaten_today": {
            "calories": eaten_calories,
            "protein_g": eaten_protein,
        },
        "remaining_targets": {
            "protein_deficit_g": protein_left,
            "calorie_deficit_kcal": calories_left
        }
    }


# ==========================================
# 4. TESTING BLOCK
# ==========================================
if __name__ == "__main__":
    test_user = "user_01"

    print("1. Saving User Profile...")
    save_user_profile(test_user, weight_kg=72.0, height_cm=175.0, target_protein_g=140.0)
    
    print("2. Logging a test meal...")
    log_meal_intake(
        user_id=test_user,
        dish_name="Palak Paneer",
        weight_grams=250.0,
        nutrients={"protein_g": 10.08, "carbs_g": 11.07, "fat_g": 11.91, "iron_mg": 3.2, "vitc_mg": 14.5}
    )

    print("3. Checking today's status...")
    status = get_daily_status_and_gaps(test_user)
    print(status)