from enum import Enum
from enum import Enum
from typing import Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field # HttpUrl removed as image_url is str
from sqlalchemy.orm import Session

from app.services.image_generation_service import ImageGenerationService
from app.core.config import settings
from app.db import get_db
from app.models import User as UserModel # For current_user type hint
from app.services.auth_service import get_current_active_user # For auth dependency

router = APIRouter()

# --- Pydantic Models ---
class ImageModelName(str, Enum):
    DALLE = "dall-e"
    STABLE_DIFFUSION = "stable-diffusion"
    GEMINI = "gemini"

class ImageGenerationRequest(BaseModel):
    prompt: str
    model: ImageModelName = Field(ImageModelName.DALLE, description="The image generation model to use.")
    size: Optional[str] = Field(None, description="Desired image size. Varies by model. For Gemini, this is conceptual (e.g., '1024x1024').")
    quality: Optional[str] = Field(None, description="Desired image quality (e.g., 'hd', 'standard'). Mainly for DALL-E.")
    # Stable Diffusion specific parameters (optional)
    steps: Optional[int] = Field(None, description="Number of inference steps for Stable Diffusion.")
    cfg_scale: Optional[float] = Field(None, description="Classifier Free Guidance scale for Stable Diffusion.")
    # Gemini specific parameters (optional)
    gemini_model_name: Optional[str] = Field(None, description="Specific Gemini model to use, e.g., 'gemini-pro-vision'. Only used if 'model' is 'gemini'.")
    campaign_id: Optional[int] = Field(None, description="Optional campaign ID to associate the image with.")

class ImageGenerationResponse(BaseModel):
    image_url: str
    prompt_used: str
    model_used: ImageModelName # This will now include "gemini"
    size_used: str
    quality_used: Optional[str] = None # Quality may not apply to all models
    steps_used: Optional[int] = None # For Stable Diffusion
    cfg_scale_used: Optional[float] = None # For Stable Diffusion
    gemini_model_name_used: Optional[str] = Field(None, description="The specific Gemini model that was used for generation, if applicable.")

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
    summary="Generate an image using DALL-E, Stable Diffusion, or Gemini."
)
async def generate_image_endpoint(
    request: ImageGenerationRequest,
    service: Annotated[ImageGenerationService, Depends(get_image_generation_service)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_user)]
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
        - `gemini`: Uses a Google Gemini model.
            - `size` is conceptual (e.g., "1024x1024"), actual output size depends on the Gemini API.
            - `gemini_model_name` (Optional) to specify a particular Gemini model (e.g., "gemini-pro-vision").
    - **size**: (Optional) The size of the generated image. Behavior varies by model.
    - **quality**: (Optional) For DALL-E 3: "standard", "hd". (Ignored for others).
    - **steps**: (Optional) Number of inference steps for Stable Diffusion.
    - **cfg_scale**: (Optional) Classifier Free Guidance scale for Stable Diffusion.
    - **gemini_model_name**: (Optional) Specific Gemini model (e.g., "gemini-pro-vision").

    Returns the URL of the generated image and details of the generation parameters used.
    """
    # Docstring updated

    try:
        image_url: str
        final_size: str
        final_quality: Optional[str] = None
        final_steps: Optional[int] = None
        final_cfg_scale: Optional[float] = None
        final_gemini_model_name: Optional[str] = None

        if request.model == ImageModelName.DALLE:
            dalle_model_name = settings.OPENAI_DALLE_MODEL_NAME
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
                final_quality = "n/a (dall-e-2)"

            # user_id_to_pass = current_user.id # Removed

            image_url = await service.generate_image_dalle(
                prompt=request.prompt,
                db=db,
                model=dalle_model_name,
                size=final_size,
                quality=final_quality if dalle_model_name == "dall-e-3" else None,
                current_user=current_user,
                campaign_id=request.campaign_id
            )
            model_used_for_response = f"{request.model.value} ({dalle_model_name})" # Not used in response model directly

        elif request.model == ImageModelName.STABLE_DIFFUSION:
            # user_id_to_pass = current_user.id # Removed

            # Use Stable Diffusion specific defaults from settings if not provided in request,
            # or pass None to let the service layer handle defaults.
            final_size = request.size or settings.STABLE_DIFFUSION_DEFAULT_IMAGE_SIZE
            final_steps = request.steps # Service will use settings.STABLE_DIFFUSION_DEFAULT_STEPS if None
            final_cfg_scale = request.cfg_scale # Service will use settings.STABLE_DIFFUSION_DEFAULT_CFG_SCALE if None
            final_quality = "n/a (stable-diffusion)"
            # The specific SD model checkpoint is handled by the service (using settings.STABLE_DIFFUSION_DEFAULT_MODEL)
            # If we wanted to allow selecting SD model checkpoint via API:
            # sd_model_checkpoint_to_pass = request.sd_model_checkpoint # Assuming it's added to ImageGenerationRequest

            # Fetch user's preferred Stable Diffusion engine
            sd_engine_to_use = current_user.sd_engine_preference

            image_url = await service.generate_image_stable_diffusion(
                prompt=request.prompt,
                db=db,
                size=final_size,
                steps=final_steps,
                cfg_scale=final_cfg_scale,
                current_user=current_user,
                campaign_id=request.campaign_id,
                sd_engine_id=sd_engine_to_use
            )
            model_used_for_response = request.model.value

        elif request.model == ImageModelName.GEMINI:
            # For Gemini, size is conceptual. Pass what's given or a default string for logging.
            # The actual image dimensions will be determined by the Gemini API and model.
            final_size = request.size or "default_gemini_size" # Placeholder for logging if not provided
            final_gemini_model_name = request.gemini_model_name or "gemini-pro-vision" # Default if not specified by user

            image_url = await service.generate_image_gemini(
                prompt=request.prompt,
                db=db,
                current_user=current_user,
                size=request.size,
                model=final_gemini_model_name,
                user_id=current_user.id,
                campaign_id=request.campaign_id
            )
            model_used_for_response = request.model.value # This is 'gemini'
            # For Gemini, quality, steps, cfg_scale are not applicable in the same way
            final_quality = "n/a (gemini)"
            final_steps = None
            final_cfg_scale = None

        else:
            # This case should not be reached if Pydantic validation works correctly with Enum
            raise HTTPException(status_code=400, detail="Invalid image generation model selected.")

        return ImageGenerationResponse(
            image_url=image_url,
            prompt_used=request.prompt,
            model_used=request.model,
            size_used=final_size,
            quality_used=final_quality if request.model == ImageModelName.DALLE else None,
            steps_used=final_steps if request.model == ImageModelName.STABLE_DIFFUSION else None,
            cfg_scale_used=final_cfg_scale if request.model == ImageModelName.STABLE_DIFFUSION else None,
            gemini_model_name_used=final_gemini_model_name if request.model == ImageModelName.GEMINI else None
        )
    # HTTPException raised by the service (e.g., for API errors, bad params) will pass through.
    except HTTPException:
        raise # Re-raise HTTPException from the service
    except Exception as e:
        print(f"Unexpected error in image generation endpoint: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred while generating the image.")
