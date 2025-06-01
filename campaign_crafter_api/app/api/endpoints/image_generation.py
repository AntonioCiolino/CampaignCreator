from enum import Enum
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from sqlalchemy.orm import Session

from app.services.image_generation_service import ImageGenerationService # STABLE_DIFFUSION_API_URL removed
from app.core.config import settings
from app.db import get_db
# from app.models import User # If you were to use current_user for user_id
# from app.api.dependencies import get_current_user # If you have a current user dependency

router = APIRouter()

# --- Pydantic Models ---
class ImageModelName(str, Enum):
    DALLE = "dall-e"
    STABLE_DIFFUSION = "stable-diffusion"

class ImageGenerationRequest(BaseModel):
    prompt: str
    model: ImageModelName = Field(ImageModelName.DALLE, description="The image generation model to use.")
    size: Optional[str] = Field(None, description="Desired image size (e.g., '1024x1024'). Varies by model.")
    quality: Optional[str] = Field(None, description="Desired image quality (e.g., 'hd', 'standard'). Mainly for DALL-E.")
    # Stable Diffusion specific parameters (optional)
    steps: Optional[int] = Field(None, description="Number of inference steps for Stable Diffusion.")
    cfg_scale: Optional[float] = Field(None, description="Classifier Free Guidance scale for Stable Diffusion.")
    # Add other DALL-E parameters if needed, e.g., style ('vivid', 'natural' for DALL-E 3)
    # style: Optional[str] = "vivid" # Example for DALL-E 3 for DALL-E model

class ImageGenerationResponse(BaseModel):
    image_url: str # Changed from HttpUrl to str, to accommodate data URLs
    prompt_used: str
    model_used: ImageModelName
    size_used: str
    quality_used: Optional[str] = None # Quality may not apply to all models
    steps_used: Optional[int] = None # For Stable Diffusion
    cfg_scale_used: Optional[float] = None # For Stable Diffusion
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
    summary="Generate an image using a selected model (DALL-E or Stable Diffusion)."
)
async def generate_image_endpoint(
    request: ImageGenerationRequest,
    service: ImageGenerationService = Depends(get_image_generation_service),
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user) # Example if using authenticated user
):
    """
    Generates an image based on a text prompt using either DALL-E or Stable Diffusion.

    - **prompt**: The text description of the image to generate.
    - **model**: Selects the generation model:
        - `dall-e`: Uses OpenAI's DALL-E.
            - `size` defaults to `settings.OPENAI_DALLE_DEFAULT_IMAGE_SIZE`.
            - `quality` defaults to `settings.OPENAI_DALLE_DEFAULT_IMAGE_QUALITY`.
        - `stable-diffusion`: Uses a Stable Diffusion model via its configured API.
            - `size` defaults to `settings.STABLE_DIFFUSION_DEFAULT_IMAGE_SIZE`.
            - `steps` defaults to `settings.STABLE_DIFFUSION_DEFAULT_STEPS`.
            - `cfg_scale` defaults to `settings.STABLE_DIFFUSION_DEFAULT_CFG_SCALE`.
    - **size**: (Optional) The size of the generated image (e.g., "1024x1024").
              Supported sizes vary by model. Check DALL-E or Stable Diffusion documentation.
    - **quality**: (Optional) For DALL-E 3: "standard", "hd". (Ignored for DALL-E 2 and Stable Diffusion).
    - **steps**: (Optional) Number of inference steps for Stable Diffusion.
    - **cfg_scale**: (Optional) Classifier Free Guidance scale for Stable Diffusion.

    The specific Stable Diffusion API endpoint and model checkpoint are configured on the server.
    Returns the URL of the generated image and details of the generation parameters used.
    """
    # Docstring updated, no need for dynamic replacement of STABLE_DIFFUSION_API_URL


    try:
        image_url: str
        final_size: str
        final_quality: Optional[str] = None
        final_steps: Optional[int] = None
        final_cfg_scale: Optional[float] = None

        if request.model == ImageModelName.DALLE:
            # Use DALL-E specific defaults from settings if not provided in request
            dalle_model_name = settings.OPENAI_DALLE_MODEL_NAME # e.g. "dall-e-3"
            final_size = request.size or settings.OPENAI_DALLE_DEFAULT_IMAGE_SIZE
            final_quality = request.quality or settings.OPENAI_DALLE_DEFAULT_IMAGE_QUALITY

            # Validate DALL-E specific parameters (service also does this, but good for early feedback)
            if dalle_model_name == "dall-e-3":
                if final_size not in ["1024x1024", "1792x1024", "1024x1792"]:
                    raise HTTPException(status_code=400, detail=f"Invalid size for DALL-E 3. Supported: 1024x1024, 1792x1024, 1024x1792. Got: {final_size}")
                if final_quality not in ["standard", "hd"]:
                    raise HTTPException(status_code=400, detail=f"Invalid quality for DALL-E 3. Supported: 'standard', 'hd'. Got: {final_quality}")
            elif dalle_model_name == "dall-e-2":
                if final_size not in ["256x256", "512x512", "1024x1024"]:
                    raise HTTPException(status_code=400, detail=f"Invalid size for DALL-E 2. Supported: 256x256, 512x512, 1024x1024. Got: {final_size}")
                final_quality = "n/a (dall-e-2)" # Quality param not used by DALL-E 2 in the same way

            # user_id_to_pass = current_user.id if current_user else None # Example
            user_id_to_pass = None # For now, as user auth is not confirmed for this step

            image_url = await service.generate_image_dalle(
                prompt=request.prompt,
                db=db,
                model=dalle_model_name,
                size=final_size,
                quality=final_quality if dalle_model_name == "dall-e-3" else None,
                user_id=user_id_to_pass
            )
            model_used_for_response = f"{request.model.value} ({dalle_model_name})"

        elif request.model == ImageModelName.STABLE_DIFFUSION:
            # user_id_to_pass = current_user.id if current_user else None # Example
            user_id_to_pass = None # For now

            # Use Stable Diffusion specific defaults from settings if not provided in request,
            # or pass None to let the service layer handle defaults.
            final_size = request.size or settings.STABLE_DIFFUSION_DEFAULT_IMAGE_SIZE
            final_steps = request.steps # Service will use settings.STABLE_DIFFUSION_DEFAULT_STEPS if None
            final_cfg_scale = request.cfg_scale # Service will use settings.STABLE_DIFFUSION_DEFAULT_CFG_SCALE if None
            final_quality = "n/a (stable-diffusion)"
            # The specific SD model checkpoint is handled by the service (using settings.STABLE_DIFFUSION_DEFAULT_MODEL)
            # If we wanted to allow selecting SD model checkpoint via API:
            # sd_model_checkpoint_to_pass = request.sd_model_checkpoint # Assuming it's added to ImageGenerationRequest


            image_url = await service.generate_image_stable_diffusion(
                prompt=request.prompt,
                db=db,
                size=final_size, # Pass the determined size (request or default)
                steps=final_steps, # Pass request value (can be None)
                cfg_scale=final_cfg_scale, # Pass request value (can be None)
                user_id=user_id_to_pass
                # sd_model_checkpoint=sd_model_checkpoint_to_pass # If allowing selection
            )
            model_used_for_response = request.model.value # This is 'stable-diffusion'
        else:
            # This case should not be reached if Pydantic validation works correctly with Enum
            raise HTTPException(status_code=400, detail="Invalid image generation model selected.")

        return ImageGenerationResponse(
            image_url=image_url,
            prompt_used=request.prompt,
            model_used=request.model, # Return the enum value (e.g. "dall-e" or "stable-diffusion")
            size_used=final_size,
            quality_used=final_quality if request.model == ImageModelName.DALLE else None,
            steps_used=final_steps if request.model == ImageModelName.STABLE_DIFFUSION else None,
            cfg_scale_used=final_cfg_scale if request.model == ImageModelName.STABLE_DIFFUSION else None
        )
    # HTTPException raised by the service (e.g., for API errors, bad params) will pass through.
    except HTTPException:
        raise # Re-raise HTTPException from the service
    except Exception as e:
        print(f"Unexpected error in image generation endpoint: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred while generating the image.")
