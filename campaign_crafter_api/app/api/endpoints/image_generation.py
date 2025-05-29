from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl # HttpUrl for validating the image_url
from typing import Optional

from app.services.image_generation_service import ImageGenerationService
from app.core.config import settings # To get default model/size/quality for response

router = APIRouter()

# --- Pydantic Models ---
class ImageGenerationRequest(BaseModel):
    prompt: str
    size: Optional[str] = None
    quality: Optional[str] = None
    model: Optional[str] = None
    # Add other DALL-E parameters if needed, e.g., style ('vivid', 'natural' for DALL-E 3)
    # style: Optional[str] = "vivid" # Example for DALL-E 3

class ImageGenerationResponse(BaseModel):
    image_url: HttpUrl # Use HttpUrl for validation
    prompt_used: str
    model_used: str
    size_used: str
    quality_used: str
    # revised_prompt: Optional[str] = None # DALL-E 3 might return a revised prompt

# --- Dependency ---
# A simple dependency function to get the service instance.
# FastAPI will handle caching this for a single request if needed,
# though for a stateless service like this, it's straightforward.
def get_image_generation_service():
    try:
        return ImageGenerationService()
    except ValueError as e: # Catch initialization errors (e.g. API key not set)
        # This error during dependency resolution will prevent endpoint execution
        # and result in a 500 error by default.
        # We could raise HTTPException here, but it's often better to let
        # global exception handlers manage this if it's a config issue.
        # For clarity in this specific endpoint, we can catch and re-raise.
        raise HTTPException(status_code=503, detail=f"ImageGenerationService unavailable: {e}")


# --- API Endpoint ---
@router.post(
    "/images/generate", 
    response_model=ImageGenerationResponse, 
    tags=["Image Generation"],
    summary="Generate an image using DALL-E based on a text prompt."
)
async def generate_image_endpoint(
    request: ImageGenerationRequest,
    service: ImageGenerationService = Depends(get_image_generation_service) # Use the dependency
):
    """
    Generates an image using OpenAI's DALL-E API.

    - **prompt**: The text description of the image to generate.
    - **model**: (Optional) The DALL-E model to use (e.g., "dall-e-3", "dall-e-2"). 
                 Defaults to `OPENAI_DALLE_MODEL_NAME` from server settings.
    - **size**: (Optional) The size of the generated image. Defaults to server settings.
              Supported for DALL-E 3: "1024x1024", "1792x1024", "1024x1792".
              Supported for DALL-E 2: "256x256", "512x512", "1024x1024".
    - **quality**: (Optional) The quality of the image. Defaults to server settings.
                 Supported for DALL-E 3: "standard", "hd". (Ignored for DALL-E 2).
    
    Returns the URL of the generated image and details of the generation parameters used.
    """
    try:
        image_url = await service.generate_image(
            prompt=request.prompt,
            model=request.model, # Pass None if not provided, service handles default
            size=request.size,   # Pass None if not provided, service handles default
            quality=request.quality # Pass None if not provided, service handles default
        )
        
        # Determine what parameters were actually used (either from request or defaults in service/settings)
        final_model = request.model or settings.OPENAI_DALLE_MODEL_NAME
        final_size = request.size or settings.OPENAI_DALLE_DEFAULT_IMAGE_SIZE
        final_quality = request.quality or settings.OPENAI_DALLE_DEFAULT_IMAGE_QUALITY
        if final_model != "dall-e-3": # DALL-E 2 doesn't use 'quality' in the same way
            final_quality = "n/a (dall-e-2)"


        return ImageGenerationResponse(
            image_url=image_url,
            prompt_used=request.prompt, # Could also consider returning revised_prompt if DALL-E provides it
            model_used=final_model,
            size_used=final_size,
            quality_used=final_quality
        )
    # HTTPException raised by the service (e.g. for API errors, bad params) will pass through.
    # No need to re-catch them here unless adding more context.
    except HTTPException:
        raise # Re-raise HTTPException from the service
    except Exception as e:
        # Catch any other unexpected errors not already converted to HTTPException by the service
        print(f"Unexpected error in image generation endpoint: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred while generating the image.")
