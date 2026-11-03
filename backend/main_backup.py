
import os
import time
from pathlib import Path
from io import BytesIO

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError
from dotenv import load_dotenv
from google import genai

# Load API key
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

app = FastAPI(title="Multimodal Construction Intelligence Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Construction Intelligence Platform is running!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):

    if not client:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Gemini API key is missing. Check backend/.env"
            }
        )

    allowed_types = ["image/jpeg", "image/png", "image/webp"]

    if file.content_type not in allowed_types:
        return {
            "success": False,
            "message": "Please upload a JPG, PNG, or WEBP image."
        }

    contents = await file.read()

    if len(contents) > 10 * 1024 * 1024:
        return {
            "success": False,
            "message": "Image must be smaller than 10 MB."
        }

    try:
        image = Image.open(BytesIO(contents))
        image.verify()
        image = Image.open(BytesIO(contents)).convert("RGB")

    except (UnidentifiedImageError, OSError):
        return {
            "success": False,
            "message": "The uploaded file is not a valid image."
        }

    prompt = """
You are an assistant for a Construction Intelligence Platform.

Analyze the uploaded construction site image.

Give your answer in simple English using these sections:

1. SITE DESCRIPTION:
Describe what is visible in the image.

2. MATERIALS AND EQUIPMENT:
Identify visible construction materials, tools and equipment.

3. WORKER SAFETY:
Mention visible workers and safety equipment.
Do not assume something is absent if it is not clearly visible.

4. VISIBLE SAFETY RISKS:
Identify possible hazards supported by the image.

5. RECOMMENDATIONS:
Give practical suggestions to improve site safety.

IMPORTANT:
Do not invent details.
Do not claim that the site is completely safe.
This is only a preliminary visual assessment,
not a certified construction safety inspection.
"""

    # Gemini request with automatic retry
    try:
        response = None

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=[prompt, image]
                )
                break

            except Exception as error:
                error_message = str(error)

                if "503" in error_message and attempt < 2:
                    wait_time = 3 * (attempt + 1)
                    print(f"Gemini busy. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise

        analysis = response.text if response else None

        if not analysis:
            return {
                "success": False,
                "message": "Gemini did not return an analysis. Please try again."
            }

        return {
            "success": True,
            "filename": file.filename,
            "message": "AI image analysis completed successfully!",
            "analysis": analysis
        }

    except Exception as error:
        print("Gemini API error:", str(error))

        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "message": "Gemini analysis failed. Please try again later. Check backend terminal for details."
            }
        )
