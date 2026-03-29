# from dotenv import load_dotenv
# import os

# # ✅ FORCE load .env from backend folder
# env_path = os.path.join(os.path.dirname(__file__), ".env")
# load_dotenv(env_path)

# HF_TOKEN = os.getenv("HF_TOKEN")
# AI_MODEL = os.getenv("AI_DETECTOR_MODEL", "Ateeqq/ai-vs-human-image-detector")
# # print("HF TOKEN:", HF_TOKEN)
# # print("AI detector model:", AI_MODEL)

# from transformers import pipeline
# from PIL import Image
# import requests
# from io import BytesIO

# cache = {}

# # Load model once
# detector = pipeline(
#     "image-classification",
#     model=AI_MODEL,
#     token=HF_TOKEN
# )

# def is_ai_image_from_url(image_url: str) -> bool:
#     if image_url in cache:
#         return cache[image_url]

#     try:
#         headers = {
#             "User-Agent": "Mozilla/5.0"
#         }

#         response = requests.get(image_url, headers=headers, timeout=10)
#         response.raise_for_status()

#         image = Image.open(BytesIO(response.content)).convert("RGB")
#         image = image.resize((512, 512))

#         result = detector(image)
#         print("MODEL OUTPUT:", result)

#         scores = {str(item["label"]).lower(): float(item["score"]) for item in result}
#         ai_score = scores.get("ai", scores.get("artificial", 0.0))
#         human_score = scores.get("hum", scores.get("human", 0.0))

#         # Balanced decision rule using both score values.
#         # - Strong AI probability should override human.
#         # - If human is clearly stronger, treat as not AI.
#         # - When scores are close, require a minimum AI confidence.
#         score_diff = ai_score - human_score

#         if ai_score >= 0.35 and score_diff > 0.05:
#             is_ai = True
#         elif human_score >= 0.35 and score_diff < -0.05:
#             is_ai = False
#         else:
#             is_ai = ai_score > human_score and ai_score >= 0.2

#         cache[image_url] = is_ai
#         return is_ai

#     except Exception as e:
#         print("ERROR while processing image:", image_url)
#         print("ERROR DETAILS:", str(e))
#         return None

from dotenv import load_dotenv
import os
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

HF_TOKEN = os.getenv("HF_TOKEN")
AI_MODEL = os.getenv("AI_DETECTOR_MODEL", "Ateeqq/ai-vs-human-image-detector")

API_URL = f"https://router.huggingface.co/hf-inference/models/{AI_MODEL}"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

cache = {}

# 🔁 Robust session with retry
session = requests.Session()
retries = Retry(total=3, backoff_factor=1)
session.mount("https://", HTTPAdapter(max_retries=retries))


def fetch_image_bytes(url):
    try:
        response = session.get(url, timeout=15, stream=True)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print("IMAGE DOWNLOAD ERROR:", str(e))
        return None


def is_ai_image_from_url(image_url: str):
    if not image_url:
        return None

    if image_url in cache:
        return cache[image_url]

    try:
        result = None

        for attempt in range(3):
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json={"inputs": image_url},
                timeout=30
            )

            try:
                result = response.json()
            except Exception:
                print("HF JSON ERROR")
                result = None

            print("HF RESPONSE RAW:", result)

            if isinstance(result, dict) and "error" in result:
                print("Model loading... retrying")
                time.sleep(3)
                continue

            break

        if not result or isinstance(result, dict):
            return None

        scores = {
            str(item["label"]).lower(): float(item["score"])
            for item in result
        }

        print("PARSED SCORES:", scores)

        # ✅ FIXED LABELS
        ai_labels = ["ai", "fake", "generated", "artificial"]
        human_labels = ["human", "real", "hum"]  # 🔥 THIS FIX

        ai_score = max([scores.get(label, 0) for label in ai_labels])
        human_score = max([scores.get(label, 0) for label in human_labels])

        # ✅ FIXED DECISION LOGIC
        if ai_score > human_score:
            is_ai = True
        else:
            is_ai = False

        cache[image_url] = is_ai

        print("FINAL AI RESULT:", is_ai)

        return is_ai

    except Exception as e:
        print("ERROR while processing image:", image_url)
        print("ERROR DETAILS:", str(e))
        return None
