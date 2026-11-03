
import os
import base64
from pathlib import Path
from io import BytesIO

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from PIL import Image, UnidentifiedImageError
from dotenv import load_dotenv
from groq import Groq


# 1. Load environment variables
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY) if API_KEY else None

MODEL = "qwen/qwen3.8-27b"


# 2. Create FastAPI application
app = FastAPI(
    title="Multimodal Construction Intelligence Platform",
    description="AI-powered construction site image analysis",
    version="1.0.0"
)


# 3. Enable CORS
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


# 4. Home route
@app.get("/")
def home():
    return {
        "message": "Construction Intelligence Platform is running!"
    }


# 5. Health check
@app.get("/health")
def health():
    return {"status": "healthy"}


# 6. Image analysis
@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):

    # Check API key
    if not client:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_type": "API_KEY_MISSING",
                "message": "Groq API key is missing. Check backend/.env"
            }
        )

    # Check image format
    allowed_types = {
        "image/jpeg": "jpeg",
        "image/png": "png",
        "image/webp": "webp"
    }

    if file.content_type not in allowed_types:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error_type": "INVALID_FORMAT",
                "message": "Please upload a JPG, PNG, or WEBP image."
            }
        )

    # Read image
    contents = await file.read()

    if not contents:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error_type": "EMPTY_FILE",
                "message": "Uploaded image is empty."
            }
        )

    # Check 10 MB limit
    if len(contents) > 10 * 1024 * 1024:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error_type": "FILE_TOO_LARGE",
                "message": "Image must be smaller than 10 MB."
            }
        )

    # Validate image
    try:
        image = Image.open(BytesIO(contents))
        image.verify()

        image = Image.open(BytesIO(contents))
        image_format = image.format

        if image_format not in ["JPEG", "PNG", "WEBP"]:
            raise ValueError("Unsupported image format")

    except (UnidentifiedImageError, OSError, ValueError):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error_type": "INVALID_IMAGE",
                "message": "The uploaded file is not a valid JPG, PNG, or WEBP image."
            }
        )

    # 7. Convert image to Base64
    image_base64 = base64.b64encode(contents).decode("utf-8")
    mime_type = file.content_type

    image_url = (
        f"data:{mime_type};base64,{image_base64}"
    )

    # 8. Construction analysis prompt
    prompt = """
You are an assistant for a Construction Intelligence Platform.

Analyze the uploaded construction site image.

Give your answer in simple English using these sections:

1. SITE DESCRIPTION:
Describe what is visible in the image.

2. MATERIALS AND EQUIPMENT:
Identify visible construction materials, tools and equipment.

3. WORKER SAFETY:
Mention whether workers are visible and identify visible
safety equipment such as helmets, safety vests and gloves.
Do not assume something is absent if it is not clearly visible.

4. VISIBLE SAFETY RISKS:
Identify possible hazards supported by the image.
If something cannot be confirmed, clearly mention that.

5. RECOMMENDATIONS:
Give practical suggestions to improve site safety.

IMPORTANT:
Do not invent details.
Do not claim that the site is completely safe.
This is only a preliminary visual assessment,
not a certified construction safety inspection.
"""

    # 9. Groq API request
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            temperature=0.2,
            max_completion_tokens=1500
        )

        analysis = response.choices[0].message.content

        if not analysis:
            return JSONResponse(
                status_code=502,
                content={
                    "success": False,
                    "error_type": "EMPTY_RESPONSE",
                    "message": "Groq did not return an analysis."
                }
            )

        return {
            "success": True,
            "filename": file.filename,
            "message": "AI image analysis completed successfully!",
            "analysis": analysis
        }

    except Exception as error:
        print("Groq API error:", str(error))

        status_code = getattr(error, "status_code", None)

        if status_code == 429:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error_type": "QUOTA_EXCEEDED",
                    "message": "Groq API rate limit or quota exceeded. Please try again later."
                }
            )

        if status_code in [401, 403]:
            return JSONResponse(
                status_code=502,
                content={
                    "success": False,
                    "error_type": "API_PERMISSION_ERROR",
                    "message": "Groq API key or model permission issue. Check your Groq account."
                }
            )

        if status_code == 404:
            return JSONResponse(
                status_code=502,
                content={
                    "success": False,
                    "error_type": "MODEL_NOT_FOUND",
                    "message": "Groq model is unavailable. Check the model ID."
                }
            )

        if status_code and status_code >= 500:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error_type": "PROVIDER_UNAVAILABLE",
                    "message": "Groq is temporarily unavailable. Please try again later."
                }
            )

        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "error_type": "GROQ_ERROR",
                "message": "Image analysis failed. Please check the backend terminal."
            }
        )
