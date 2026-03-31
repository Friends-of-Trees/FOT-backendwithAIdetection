# from ai_detector import is_ai_image_from_url
# from fastapi import FastAPI, UploadFile, File, Form, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel # <--- 1. Add this import
# from db import supabase
# import uuid
# import mimetypes
# import os # <--- 2. Add this import to read .env
# from dotenv import load_dotenv
# load_dotenv()

# app = FastAPI()

# import time

# def safe_supabase_call(func):
#     for attempt in range(3):
#         try:
#             return func()
#         except Exception as e:
#             print(f"Supabase error (attempt {attempt+1}):", str(e))
#             time.sleep(2)
#     return None


# # -------------------------------------------------
# # CORS
# # -------------------------------------------------
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # -------------------------------------------------
# # ADMIN LOGIN LOGIC
# # -------------------------------------------------

# # 3. Create the data model for the login request
# class AdminLogin(BaseModel):
#     username: str
#     password: str

# # 4. Create the login endpoint
# @app.post("/admin/login")
# async def admin_login(data: AdminLogin):
#     # Fetch values from your .env file
#     stored_username = os.getenv("ADMIN_USERNAME")
#     stored_password = os.getenv("ADMIN_PASSWORD")

#     # Verify credentials
#     if data.username == stored_username and data.password == stored_password:
#         return {"status": "success", "message": "Access Granted"}
#     else:
#         # 401 means "Unauthorized"
#         raise HTTPException(status_code=401, detail="Invalid ID or Password")
    
#     # 1. Define the model for awarding a winner
# class WinnerAssignment(BaseModel):
#     entry_id: str
#     winner_rank: str

# # 2. Create the route to update the entry in Supabase
# @app.post("/admin/assign-winner")
# async def assign_winner(data: WinnerAssignment):
#     try:
#         # Update the specific entry in Supabase using .update() and .eq() filter
#         response = (
#             supabase.table("competition_entries")
#             .update({"winner_rank": data.winner_rank}) # The new column you added
#             .eq("id", data.entry_id)                   # Target specific row
#             .execute()
#         )
        
#         # Check if the update was successful
#         if not response.data:
#             raise HTTPException(status_code=404, detail="Entry not found")
            
#         return {"status": "success", "message": f"Awarded {data.winner_rank} successfully"}
        
#     except Exception as e:
#         print(f"Error updating winner: {e}")
#         raise HTTPException(status_code=500, detail="Database update failed")

# # -------------------------------------------------
# # TEST ROUTE
# # -------------------------------------------------
# @app.get("/")
# def root():
#     return {"status": "backend working"}

# # -------------------------------------------------
# # SUBMIT ENTRY
# # -------------------------------------------------
# # ... existing imports and setup ...

# @app.post("/submit-entry")
# async def submit_entry(
#     competition_type: str = Form(...),
#     full_name: str = Form(...),
#     organization: str = Form(None),
#     address: str = Form(...),
#     city: str = Form(...),
#     contact: str = Form(...),
#     email: str = Form(...),
#     description: str = Form(None),
#     photos: list[UploadFile] = File(...)
# ):
#     print("SUBMIT ENTRY CALLED")

#     # ✅ SAFE INSERT
#     entry = safe_supabase_call(lambda: supabase.table("competition_entries").insert({
#         "competition_type": competition_type,
#         "full_name": full_name,
#         "organization": organization,
#         "address": address,
#         "city": city,
#         "contact": contact,
#         "email": email,
#         "description": description,
#     }).execute())

#     if not entry or not entry.data:
#         raise HTTPException(status_code=500, detail="Database insert failed")

#     entry_id = entry.data[0]["id"]

#     image_urls = []

#     # ✅ SAFE IMAGE UPLOAD LOOP
#     for photo in photos:
#         if not photo.filename:
#             continue

#         guessed_type, _ = mimetypes.guess_type(photo.filename)
#         mime_type = guessed_type or photo.content_type or "application/octet-stream"

#         if mime_type not in {"image/jpeg", "image/png"}:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Unsupported image type for file '{photo.filename}'"
#             )

#         file_bytes = await photo.read()
#         filename = f"{uuid.uuid4()}_{photo.filename}"
#         file_path = f"{competition_type}/{entry_id}/{filename}"

#         try:
#             supabase.storage.from_("competition-uploads").upload(
#                 file_path,
#                 file_bytes,
#                 {"content-type": mime_type},
#             )
#         except Exception as e:
#             print("UPLOAD ERROR:", str(e))
#             continue

#         public_url = supabase.storage.from_("competition-uploads").get_public_url(file_path)

#         safe_supabase_call(lambda: supabase.table("entry_images").insert({
#             "entry_id": entry_id,
#             "image_url": public_url,
#         }).execute())

#         image_urls.append(public_url)

#     # ✅ SAFE AI DETECTION
#     ai_flag = None

#     for url in image_urls:
#         print("Checking AI for:", url)

#         try:
#             result = is_ai_image_from_url(url)
#             print("AI RESULT:", result)

#             if result is True:
#                 ai_flag = True
#                 break
#             elif result is False and ai_flag is None:
#                 ai_flag = False

#         except Exception as e:
#             print("AI ERROR:", str(e))
#             continue

#     print("FINAL AI FLAG:", ai_flag)

#     # ✅ SAFE UPDATE
#     safe_supabase_call(lambda: supabase.table("competition_entries").update({
#         "is_ai_generated": ai_flag
#     }).eq("id", entry_id).execute())

#     return {"status": "success", "entry_id": entry_id}


# # -------------------------------------------------
# # ADMIN ENTRIES (SAFE VERSION)
# # -------------------------------------------------

# @app.get("/admin/entries")
# def get_entries():
#     try:
#         response = safe_supabase_call(lambda: supabase.table("competition_entries")
#             .select("*")
#             .order("created_at", desc=True)
#             .execute()
#         )

#         entries = response.data if response and response.data else []

#     except Exception as e:
#         print("FETCH ENTRIES ERROR:", str(e))
#         return []

#     for entry in entries:
#         try:
#             images_res = safe_supabase_call(lambda: supabase.table("entry_images")
#                 .select("image_url")
#                 .eq("entry_id", entry["id"])
#                 .execute()
#             )

#             entry["images"] = images_res.data if images_res and images_res.data else []

#         except Exception as e:
#             print("FETCH IMAGES ERROR:", str(e))
#             entry["images"] = []

#     return entries

# @app.post("/detect-ai-batch")
# async def detect_ai_batch(data: dict):
#     image_urls = data.get("image_urls")

#     if not image_urls or not isinstance(image_urls, list):
#         return {"error": "image_urls must be a list"}

#     results = []

#     for url in image_urls:
#         print("Batch checking:", url)

#         try:
#             is_ai = is_ai_image_from_url(url)
#             print("Batch result:", is_ai)

#         except Exception as e:
#             print("Batch error:", str(e))
#             is_ai = None  # ✅ NEVER crash

#         results.append({
#             "image_url": url,
#             "is_ai": is_ai
#         })

#     return {"results": results}


import requests
from ai_detector import is_ai_image_from_url
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel # <--- 1. Add this import
from huggingface_hub import InferenceClient
from db import supabase
import uuid
import mimetypes
import os # <--- 2. Add this import to read .env
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

import time

def safe_supabase_call(func):
    for attempt in range(3):
        try:
            return func()
        except Exception as e:
            print(f"Supabase error (attempt {attempt+1}):", str(e))
            time.sleep(2)
    return None


# -------------------------------------------------
# CORS
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# ADMIN LOGIN LOGIC
# -------------------------------------------------

# 3. Create the data model for the login request
class AdminLogin(BaseModel):
    username: str
    password: str

# 4. Create the login endpoint
@app.post("/admin/login")
async def admin_login(data: AdminLogin):
    # Fetch values from your .env file
    stored_username = os.getenv("ADMIN_USERNAME")
    stored_password = os.getenv("ADMIN_PASSWORD")

    # Verify credentials
    if data.username == stored_username and data.password == stored_password:
        return {"status": "success", "message": "Access Granted"}
    else:
        # 401 means "Unauthorized"
        raise HTTPException(status_code=401, detail="Invalid ID or Password")
    
    # 1. Define the model for awarding a winner
class WinnerAssignment(BaseModel):
    entry_id: str
    winner_rank: str

# 2. Create the route to update the entry in Supabase
@app.post("/admin/assign-winner")
async def assign_winner(data: WinnerAssignment):
    try:
        # Update the specific entry in Supabase using .update() and .eq() filter
        response = (
            supabase.table("competition_entries")
            .update({"winner_rank": data.winner_rank}) # The new column you added
            .eq("id", data.entry_id)                   # Target specific row
            .execute()
        )
        
        # Check if the update was successful
        if not response.data:
            raise HTTPException(status_code=404, detail="Entry not found")
            
        return {"status": "success", "message": f"Awarded {data.winner_rank} successfully"}
        
    except Exception as e:
        print(f"Error updating winner: {e}")
        raise HTTPException(status_code=500, detail="Database update failed")

# -------------------------------------------------
# TEST ROUTE
# -------------------------------------------------
@app.get("/")
def root():
    return {"status": "backend working"}

# -------------------------------------------------
# SUBMIT ENTRY
# -------------------------------------------------
# ... existing imports and setup ...

@app.post("/submit-entry")
async def submit_entry(
    competition_type: str = Form(...),
    full_name: str = Form(...),
    organization: str = Form(None),
    address: str = Form(...),
    city: str = Form(...),
    contact: str = Form(...),
    email: str = Form(...),
    description: str = Form(None),
    photos: list[UploadFile] = File(...)
):
    print("SUBMIT ENTRY CALLED")

    # ✅ SAFE INSERT
    entry = safe_supabase_call(lambda: supabase.table("competition_entries").insert({
        "competition_type": competition_type,
        "full_name": full_name,
        "organization": organization,
        "address": address,
        "city": city,
        "contact": contact,
        "email": email,
        "description": description,
    }).execute())

    if not entry or not entry.data:
        raise HTTPException(status_code=500, detail="Database insert failed")

    entry_id = entry.data[0]["id"]

    image_urls = []

    # ✅ SAFE IMAGE UPLOAD LOOP
    for photo in photos:
        if not photo.filename:
            continue

        guessed_type, _ = mimetypes.guess_type(photo.filename)
        mime_type = guessed_type or photo.content_type or "application/octet-stream"

        if mime_type not in {"image/jpeg", "image/png"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type for file '{photo.filename}'"
            )

        file_bytes = await photo.read()
        filename = f"{uuid.uuid4()}_{photo.filename}"
        file_path = f"{competition_type}/{entry_id}/{filename}"

        try:
            supabase.storage.from_("competition-uploads").upload(
                file_path,
                file_bytes,
                {"content-type": mime_type},
            )
        except Exception as e:
            print("UPLOAD ERROR:", str(e))
            continue

        public_url = supabase.storage.from_("competition-uploads").get_public_url(file_path)

        safe_supabase_call(lambda: supabase.table("entry_images").insert({
            "entry_id": entry_id,
            "image_url": public_url,
        }).execute())

        image_urls.append(public_url)

    # ✅ SAFE AI DETECTION
    ai_flag = None

    for url in image_urls:
        print("Checking AI for:", url)

        try:
            result = is_ai_image_from_url(url)
            print("AI RESULT:", result)

            if result is True:
                ai_flag = True
                break
            elif result is False and ai_flag is None:
                ai_flag = False

        except Exception as e:
            print("AI ERROR:", str(e))
            continue

    print("FINAL AI FLAG:", ai_flag)

    # ✅ SAFE UPDATE
    safe_supabase_call(lambda: supabase.table("competition_entries").update({
        "is_ai_generated": ai_flag
    }).eq("id", entry_id).execute())

    return {"status": "success", "entry_id": entry_id}


# -------------------------------------------------
# ADMIN ENTRIES (SAFE VERSION)
# -------------------------------------------------

@app.get("/admin/entries")
def get_entries():
    try:
        response = safe_supabase_call(lambda: supabase.table("competition_entries")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        entries = response.data if response and response.data else []

    except Exception as e:
        print("FETCH ENTRIES ERROR:", str(e))
        return []

    for entry in entries:
        try:
            images_res = safe_supabase_call(lambda: supabase.table("entry_images")
                .select("image_url")
                .eq("entry_id", entry["id"])
                .execute()
            )

            entry["images"] = images_res.data if images_res and images_res.data else []

        except Exception as e:
            print("FETCH IMAGES ERROR:", str(e))
            entry["images"] = []

    return entries

@app.post("/detect-ai-batch")
async def detect_ai_batch(data: dict):
    image_urls = data.get("image_urls")

    if not image_urls or not isinstance(image_urls, list):
        return {"error": "image_urls must be a list"}

    results = []

    for url in image_urls:
        print("Batch checking:", url)

        try:
            is_ai = is_ai_image_from_url(url)
            print("Batch result:", is_ai)

        except Exception as e:
            print("Batch error:", str(e))
            is_ai = None  # ✅ NEVER crash

        results.append({
            "image_url": url,
            "is_ai": is_ai
        })

    return {"results": results}
# --- NEW CODE START ---
 
import json
import re
 
# ── Gemini optional import ─────────────────────────────────────
# Wrapped so that if the library is not installed yet, the rest
# of the backend still starts and falls back gracefully.
# try:
#     from google import genai
#     _GEMINI_LIB_AVAILABLE = True
# except ImportError:
#     _GEMINI_LIB_AVAILABLE = False
 
# ──────────────────────────────────────────────────────────────
# REQUEST MODEL
# ──────────────────────────────────────────────────────────────
class DesignRequest(BaseModel):          # BaseModel already imported above
    business_name: str
    category: str
    phone: str
 
# ──────────────────────────────────────────────────────────────
# FALLBACK CONTENT BANK
# Keyed by lowercase category; "default" is the catch-all.
# ──────────────────────────────────────────────────────────────
_FALLBACK_CONTENT: dict = {
    "bakery": {
        "tagline":              "Baked Fresh, Served With Love",
        "promo_text":           "Artisan breads, dreamy cakes & buttery pastries made from scratch every morning. Taste the warmth in every bite.",
        "call_to_action":       "Order Today & Get 10% Off!",
        "template_recommendation": ["template1", "template3", "template2"],
    },
    "gym": {
        "tagline":              "Forge Your Strongest Self",
        "promo_text":           "State-of-the-art equipment, certified coaches, and a community that never lets you quit. Your transformation starts now.",
        "call_to_action":       "Claim Your Free Trial Today!",
        "template_recommendation": ["template2", "template3", "template1"],
    },
    "restaurant": {
        "tagline":              "Where Every Meal Becomes a Memory",
        "promo_text":           "Farm-fresh ingredients, authentic recipes, and a warm ambiance that makes you feel right at home. Dine with us tonight.",
        "call_to_action":       "Reserve Your Table Now!",
        "template_recommendation": ["template3", "template1", "template2"],
    },
    "salon": {
        "tagline":              "Your Beauty, Reimagined",
        "promo_text":           "Expert stylists, premium products, and a relaxing experience tailored just for you. Leave looking and feeling stunning.",
        "call_to_action":       "Book Your Appointment Today!",
        "template_recommendation": ["template1", "template3", "template2"],
    },
    "retail": {
        "tagline":              "Quality You Can Count On",
        "promo_text":           "Curated products, unbeatable prices, and service that puts you first. Discover something new with every visit.",
        "call_to_action":       "Shop Now & Save Big!",
        "template_recommendation": ["template2", "template1", "template3"],
    },
    "tech": {
        "tagline":              "Smarter Solutions, Every Day",
        "promo_text":           "Cutting-edge technology, rapid support, and products designed to make your workflow effortlessly efficient.",
        "call_to_action":       "Get a Free Demo Today!",
        "template_recommendation": ["template2", "template3", "template1"],
    },
    "education": {
        "tagline":              "Unlock Your Full Potential",
        "promo_text":           "Expert-led courses, interactive sessions, and certifications that open real doors. Your future starts in our classroom.",
        "call_to_action":       "Enroll Now — Limited Seats!",
        "template_recommendation": ["template1", "template2", "template3"],
    },
    "default": {
        "tagline":              "Excellence in Every Detail",
        "promo_text":           "Trusted by thousands of happy customers, we deliver top-quality products and services tailored to your exact needs.",
        "call_to_action":       "Contact Us Today!",
        "template_recommendation": ["template1", "template2", "template3"],
    },
}
 
# ──────────────────────────────────────────────────────────────
# FALLBACK FUNCTION
# ──────────────────────────────────────────────────────────────
def _get_fallback(category: str) -> dict:
    """
    Return category-matched copy of fallback content.
    Tries exact match first, then substring match, then 'default'.
    """
    key = category.lower().strip()
 
    if key in _FALLBACK_CONTENT:
        return _FALLBACK_CONTENT[key].copy()
 
    # Substring match — e.g. "beauty salon" still hits "salon"
    for k in _FALLBACK_CONTENT:
        if k != "default" and k in key:
            return _FALLBACK_CONTENT[k].copy()
 
    return _FALLBACK_CONTENT["default"].copy()
 
 
# ──────────────────────────────────────────────────────────────
# GEMINI FUNCTION  (single API call, short prompt)
# ──────────────────────────────────────────────────────────────
# def call_gemini(business_name, category):
#     client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

#     prompt = f"""
#     Business: {business_name}
#     Category: {category}

#     Generate JSON:
#     {{
#       "tagline": "...",
#       "promo_text": "...",
#       "call_to_action": "...",
#       "template_recommendation": ["template1","template2"]
#     }}
#     """

#     response = client.models.generate_content(
#         model="gemini-2.0-flash",
#         contents=prompt
#     )

#     text = response.text

#     import json
#     return json.loads(text)


def _extract_text_from_hf_response(response):
    if response is None:
        return ""

    if isinstance(response, str):
        return response.strip()

    if isinstance(response, dict):
        return (
            response.get("generated_text") or
            response.get("text") or
            response.get("generated_text", "") or
            response.get("data", [{}])[0].get("generated_text", "") or
            ""
        ).strip()

    if isinstance(response, list):
        if not response:
            return ""
        return _extract_text_from_hf_response(response[0])

    try:
        if hasattr(response, "to_dict"):
            return _extract_text_from_hf_response(response.to_dict())
    except Exception:
        pass

    if hasattr(response, "generated_text"):
        return str(response.generated_text).strip()

    if hasattr(response, "text"):
        return str(response.text).strip()

    if hasattr(response, "choices"):
        choices = getattr(response, "choices")
        if choices:
            first = choices[0]
            if hasattr(first, "message") and getattr(first.message, "content", None):
                return str(first.message.content).strip()
            if hasattr(first, "content"):
                return str(first.content).strip()

    if hasattr(response, "__iter__"):
        try:
            iterator = iter(response)
            first_item = next(iterator)
        except StopIteration:
            return ""
        except Exception:
            return str(response).strip()
        return _extract_text_from_hf_response(first_item)

    return str(response).strip()


def call_huggingface(business_name, category):
    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        raise ValueError("Missing Hugging Face API key")

    model = os.getenv("HF_TEXT_MODEL", "HuggingFaceH4/zephyr-7b-beta")
    prompt = f"""
    You are a marketing expert.

    Create content for a {category} business named "{business_name}".

    Format EXACTLY like this:
    Tagline: ...
    Promo: ...
    CTA: ...
    """

    client = InferenceClient(api_key=api_key, provider="featherless-ai")
    response = client.chat_completion(
        messages=[
            {"role": "system", "content": "You are a marketing expert."},
            {"role": "user", "content": prompt},
        ],
        model=model,
        max_tokens=120,
    )

    text = _extract_text_from_hf_response(response)

    # Safe parsing
    tagline = "Quality you can trust"
    promo = "Serving you the best"
    cta = "Contact us today!"

    for line in text.split("\n"):
        line_lower = line.lower()
        if "tagline" in line_lower:
            tagline = line.split(":", 1)[-1].strip()
        elif "promo" in line_lower:
            promo = line.split(":", 1)[-1].strip()
        elif "cta" in line_lower or "call" in line_lower:
            cta = line.split(":", 1)[-1].strip()

    return {
        "tagline": tagline,
        "promo_text": promo,
        "call_to_action": cta,
        "template_recommendation": ["template1", "template2", "template3"]
    }
 
# ──────────────────────────────────────────────────────────────
# WRAPPER  — try Gemini, fall back on ANY exception
# ──────────────────────────────────────────────────────────────
def _generate_content_safe(business_name: str, category: str) -> dict:
    """
    Try Gemini first.  On ANY failure (missing key, network error,
    bad JSON, quota exceeded) use the local fallback immediately.
    The 'source' field tells the frontend which path was taken.
    """
    try:
        result = call_huggingface(business_name, category)
        result["source"] = "huggingface"
        print(f"[design-gen] Hugging Face OK — '{business_name}' / '{category}'")
        return result
    except Exception as exc:
        print(f"[design-gen] Hugging Face failed ({type(exc).__name__}: {exc}) — using fallback")
        result = _get_fallback(category)
        result["source"] = "fallback"
        return result
 
 
# ──────────────────────────────────────────────────────────────
# ENDPOINT  POST /generate-content
# ──────────────────────────────────────────────────────────────
@app.post("/generate-content")
async def generate_content(data: DesignRequest):
    """
    Accepts: { business_name, category, phone }
    Returns: { status, business_name, phone, content: { tagline,
               promo_text, call_to_action, template_recommendation,
               source } }
    """
    business_name = data.business_name.strip()
    category      = data.category.strip()
    phone         = data.phone.strip()
 
    if not business_name or not category:
        raise HTTPException(
            status_code=400,
            detail="business_name and category are required and cannot be empty",
        )
 
    content = _generate_content_safe(business_name, category)
 
    return {
        "status":        "success",
        "business_name": business_name,
        "phone":         phone,
        "content":       content,
    }
 
# --- NEW CODE END ---
