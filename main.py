import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# Import vector store for RAG, and our separate MongoDB function for memory
from db import vector_store
from userdb import log_meal_intake, get_daily_intake_summary, get_daily_status_and_gaps

# 1. Initialize Client
# Safely retrieve your API key from your environment setup
load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Hardcode a default user for console testing
CURRENT_USER_ID = "user_01"


# 2. Define the Functions
def retrieve_and_log_nutrition(dish_name: str, weight_grams: float) -> str:
    """Searches AstraDB, scales nutrients by weight, logs to MongoDB, and returns JSON."""
    
    # RAG: Semantic search in AstraDB for the closest food match
    results = vector_store.similarity_search(dish_name, k=1)
    
    if not results:
        return json.dumps({"error": f"Could not find a match for '{dish_name}' in the database."})
    
    # Extract metadata 
    best_match = results[0]
    meta = best_match.metadata
    found_name = meta.get("food_name", dish_name)
    
    # Scale nutrients based on weight
    factor = weight_grams / 100.0
    nutrients = {
        "protein_g": round(meta.get("protein_g", 0) * factor, 2),
        "carbs_g": round(meta.get("carb_g", 0) * factor, 2),
        "fat_g": round(meta.get("fat_g", 0) * factor, 2),
        "vitc_mg": round(meta.get("vitc_mg", 0) * factor, 2),
        "iron_mg": round(meta.get("iron_mg", 0) * factor, 2)
    }
    
    # Delegate logging to our dedicated MongoDB memory module
    saved_entry = log_meal_intake(
        user_id=CURRENT_USER_ID,
        dish_name=found_name,
        weight_grams=weight_grams,
        nutrients=nutrients
    )
    
    # Fetch the updated daily total that resets automatically at midnight
    daily_totals = get_daily_intake_summary(CURRENT_USER_ID)
    
    return json.dumps({
        "status": "success", 
        "logged_data": saved_entry,
        "daily_progress": daily_totals
    }, default=str)

def check_diet_progress_and_recommend(user_id: str = CURRENT_USER_ID) -> str:
    """Fetches user intake gaps, BMI status, and preferences for recommendation."""
    gap_data = get_daily_status_and_gaps(user_id)
    return json.dumps(gap_data)


# Define the tools array for the LLM schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_and_log_nutrition",
            "description": "Retrieve exact macro and micronutrients for a dish and log the meal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string"},
                    "weight_grams": {"type": "number"}
                },
                "required": ["dish_name", "weight_grams"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_diet_progress_and_recommend",
            "description": "Check current daily intake against targets, BMI, and dietary preferences to offer recommendations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The user ID to check."}
                }
            }
        }
    }
]

# 3. The Agent Loop
def run_nutrition_agent(user_query: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI Clinical Dietitian and Nutrition Coach.\n"
                "1. Use `retrieve_and_log_nutrition` to look up food and log it.\n"
                "2. Use `check_diet_progress_and_recommend` to check current progress and deficits.\n"
                "3. State exact deficits clearly (e.g., 'You are 12.5g short of your protein target').\n"
                "4. Respect dietary preferences strictly when offering food recommendations.\n"
                "Always base your final response strictly on the tool output."
            )
        },
        {"role": "user", "content": user_query}
    ]

    # Step 1: LLM decides which tool to invoke
    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    response_msg = response.choices[0].message
    
    # Step 2: Execute function call if requested
    if response_msg.tool_calls:
        messages.append(response_msg)
        
        # Apply the exact multi-tool routing logic used in the hospital admissions agent from the Agentic AI @BMSCE notebook
        for tool_call in response_msg.tool_calls:
            args = json.loads(tool_call.function.arguments)
            tool_name = tool_call.function.name
            
            if tool_name == "retrieve_and_log_nutrition":
                tool_result = retrieve_and_log_nutrition(
                    dish_name=args.get("dish_name", ""),
                    weight_grams=args.get("weight_grams", 100)
                )
            elif tool_name == "check_diet_progress_and_recommend":
                tool_result = check_diet_progress_and_recommend(
                    user_id=args.get("user_id", CURRENT_USER_ID)
                )
            else:
                tool_result = json.dumps({"error": "Unknown tool"})
                
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": tool_result})
                
        # Step 3: LLM generates final natural language summary
        final_response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=messages
        )
        return final_response.choices[0].message.content
        
    return response_msg.content

# 4. Interactive Console Interface
if __name__ == "__main__":
    print("=== Agentic AI Nutrition Tracker Ready ===")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        agent_response = run_nutrition_agent(user_input)
        print(f"Agent: {agent_response}\n" + "-"*50)