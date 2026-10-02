import json
from db import vector_store

def validate_food_lookup(query_name: str, weight_grams: float = 100.0):
    print(f"\n--- Searching AstraDB for: '{query_name}' ---")
    
    # 1. Fetch top match
    results = vector_store.similarity_search(query_name, k=1)
    if not results:
        print("❌ No matching document found.")
        return

    doc = results[0]
    meta = doc.metadata
    
    matched_name = meta.get("food_name", "Unknown")
    raw_protein = meta.get("protein_g", 0)
    raw_carbs = meta.get("carb_g", 0)
    raw_fat = meta.get("fat_g", 0)
    
    print(f"Matched Food: {matched_name}")
    print(f"Baseline (per 100g): {raw_protein}g Protein | {raw_carbs}g Carbs | {raw_fat}g Fat")
    
    # 2. Compute scaled values
    factor = weight_grams / 100.0
    scaled_protein = round(raw_protein * factor, 2)
    scaled_carbs = round(raw_carbs * factor, 2)
    scaled_fat = round(raw_fat * factor, 2)
    
    print(f"\nCalculated for {weight_grams}g (factor {factor}x):")
    print(f"-> Protein: {scaled_protein}g")
    print(f"-> Carbs:   {scaled_carbs}g")
    print(f"-> Fat:     {scaled_fat}g")

if __name__ == "__main__":
    # Test 100g (should match raw values exactly)
    validate_food_lookup("palak paneer", weight_grams=100.0)
    
    # Test custom weight
    validate_food_lookup("palak paneer", weight_grams=250.0)