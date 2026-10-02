import os

# 1. Force Hugging Face to use the D drive for permanent storage
os.environ["HF_HOME"] = "D:\\HuggingFace_Cache"

from PIL import Image
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

print("Loading Moondream2 model (will download to D:\\HuggingFace_Cache if not already there)...")

# 2. Load tokenizer and model
model_id = "vikhyatk/moondream2"
tokenizer = AutoTokenizer.from_pretrained(model_id, revision="2025-01-09")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    revision="2025-01-09",
    trust_remote_code=True,
    device_map={"": "cpu"}  # Change to "cuda" if using an NVIDIA GPU
).eval()

print("Success: Moondream2 model loaded from D drive successfully!")

# 3. Test with a food photo (update path to your actual photo)
image_path = "path_to_your_food_photo.jpg"

try:
    image = Image.open(image_path).convert("RGB")
    image_embeds = model.encode_image(image)
    
    prompt = "What specific dish is this? Name it and list its primary ingredients."
    answer = model.answer_question(image_embeds=image_embeds, question=prompt, tokenizer=tokenizer)
    
    print("\n--- Moondream2 Dish Identification Result ---")
    print(answer)

except FileNotFoundError:
    print(f"\n[Note] Model is successfully stored on your D drive! Place a photo at '{image_path}' to test.")