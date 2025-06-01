from typing import Optional
import openai # Direct import of the openai library
import requests
import os
import uuid
import shutil
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.orm_models import GeneratedImage

class ImageGenerationService:
    def __init__(self):
        # Initialize OpenAI client
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY in ["YOUR_OPENAI_API_KEY", "YOUR_API_KEY_HERE"]:
            # Allowing service to initialize even if only one key is present.
            # Specific method calls will fail if their respective keys are missing.
            print("Warning: OpenAI API key is not configured or is a placeholder.")
            self.openai_client = None
        else:
            try:
                self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None

        # Stable Diffusion API Configuration
        self.stable_diffusion_api_key = settings.STABLE_DIFFUSION_API_KEY
        self.stable_diffusion_api_url = settings.STABLE_DIFFUSION_API_URL

        if not self.stable_diffusion_api_key or self.stable_diffusion_api_key == "YOUR_STABLE_DIFFUSION_API_KEY_HERE":
            print("Warning: Stable Diffusion API key is not configured or is a placeholder. Check STABLE_DIFFUSION_API_KEY in your .env file or environment variables.")
        if not self.stable_diffusion_api_url or self.stable_diffusion_api_url == "YOUR_STABLE_DIFFUSION_API_URL_HERE":
            print("Warning: Stable Diffusion API URL is not configured or is a placeholder. Check STABLE_DIFFUSION_API_URL in your .env file or environment variables.")
            self.stable_diffusion_api_url = None # Ensure it's None if it's the placeholder, so calls will fail clearly.
        elif self.stable_diffusion_api_url and not (self.stable_diffusion_api_url.startswith("http://") or self.stable_diffusion_api_url.startswith("https://")):
            print(f"Warning: STABLE_DIFFUSION_API_URL ('{self.stable_diffusion_api_url}') does not look like a valid URL. Proceeding with caution.")


    async def _save_image_and_log_db(
        self,
        temporary_url: str,
        prompt: str,
        model_used: str, # Specific model string, e.g. "dall-e-3" or "stable-diffusion-xl"
        size_used: str,
        db: Session,
        user_id: Optional[int] = None,
        original_filename_from_api: Optional[str] = None # If API provides a filename
    ) -> str:
        """
        Downloads an image from a temporary URL, saves it locally,
        logs it in the database, and returns the permanent URL.
        """
        try:
            # Ensure storage path exists
            storage_path = Path(settings.IMAGE_STORAGE_PATH)
            storage_path.mkdir(parents=True, exist_ok=True)

            # Generate a unique filename
            # Try to get extension from temp_url or original_filename, default to .png
            file_extension = ".png" # Default
            if original_filename_from_api:
                file_extension = Path(original_filename_from_api).suffix
            elif temporary_url:
                temp_path = Path(temporary_url.split('?')[0]) # Remove query params for suffix
                if temp_path.suffix and len(temp_path.suffix) > 1: # Ensure suffix is meaningful
                    file_extension = temp_path.suffix

            # Sanitize extension to ensure it starts with a dot and is reasonable
            if not file_extension.startswith(".") or len(file_extension) > 5:
                file_extension = ".png"


            filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = storage_path / filename
            permanent_image_url = f"{settings.IMAGE_BASE_URL.strip('/')}/{filename}"

            # Download the image
            # Note: for a truly async download with 'requests', it should be run in a thread pool.
            # httpx would be a better choice for native async.
            response = requests.get(temporary_url, stream=True)
            response.raise_for_status() # Check for download errors

            with open(file_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)

            print(f"Image saved to: {file_path}")

            # Create database record
            db_image = GeneratedImage(
                filename=filename,
                image_url=permanent_image_url,
                prompt=prompt,
                model_used=model_used,
                size=size_used,
                user_id=user_id
            )
            db.add(db_image)
            db.commit()
            db.refresh(db_image)

            return permanent_image_url

        except requests.exceptions.RequestException as e:
            print(f"Failed to download image from temporary URL {temporary_url}: {e}")
            # Potentially delete partially downloaded file if any
            if file_path.exists():
                try:
                    os.remove(file_path)
                except OSError as ose:
                    print(f"Error removing partial file {file_path}: {ose}")
            raise HTTPException(status_code=502, detail=f"Failed to download image from source: {e}")
        except Exception as e:
            # Catch any other error during file save or DB operation
            print(f"Error saving image or logging to DB: {e}")
            # Potentially delete partially downloaded file if any
            if 'file_path' in locals() and file_path.exists(): # Check if file_path was defined
                try:
                    os.remove(file_path)
                except OSError as ose:
                    print(f"Error removing file {file_path} after error: {ose}")
            raise HTTPException(status_code=500, detail=f"Failed to save image or log to database: {str(e)}")

    async def generate_image_dalle(
        self,
        prompt: str,
        db: Session, # Added db session
        size: Optional[str] = None,
        quality: Optional[str] = None,
        model: Optional[str] = None, # This is the DALL-E model, e.g. "dall-e-3"
        user_id: Optional[int] = None # Added user_id
    ) -> str:
        """
        Generates an image using OpenAI's DALL-E API, saves it, logs to DB, and returns the permanent image URL.
        """
        if not self.openai_client:
            raise HTTPException(status_code=500, detail="OpenAI client is not initialized. Check API key configuration.")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

        final_model_name = model or settings.OPENAI_DALLE_MODEL_NAME
        final_size = size or settings.OPENAI_DALLE_DEFAULT_IMAGE_SIZE
        final_quality = quality or settings.OPENAI_DALLE_DEFAULT_IMAGE_QUALITY

        # Validate size for DALL-E 3 if it's the selected model
        if final_model_name == "dall-e-3":
            if final_size not in ["1024x1024", "1792x1024", "1024x1792"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid size for DALL-E 3. Supported sizes are 1024x1024, 1792x1024, 1024x1792. Provided: {final_size}"
                )
            if final_quality not in ["standard", "hd"]:
                 raise HTTPException(
                    status_code=400,
                    detail=f"Invalid quality for DALL-E 3. Supported qualities are 'standard', 'hd'. Provided: {final_quality}"
                )
        elif final_model_name == "dall-e-2": # Example if DALL-E 2 was also an option
             if final_size not in ["256x256", "512x512", "1024x1024"]:
                 raise HTTPException(
                    status_code=400,
                    detail=f"Invalid size for DALL-E 2. Supported sizes are 256x256, 512x512, 1024x1024. Provided: {final_size}"
                )
             # DALL-E 2 does not use 'quality' parameter in the same way, so it might be ignored or error if sent.

        try:
            api_response = self.openai_client.images.generate( # Use await for async client call
                model=final_model_name,
                prompt=prompt,
                size=final_size, # type: ignore
                quality=final_quality, # type: ignore (Same for quality)
                n=1,
                response_format="url" # Get a temporary URL for the image
            )
            
            if api_response.data and len(api_response.data) > 0 and api_response.data[0].url:
                temporary_url = api_response.data[0].url
                # DALL-E might also return a revised prompt
                # revised_prompt = api_response.data[0].revised_prompt

                # Save image and log to DB
                # permanent_url = await self._save_image_and_log_db(
                #     temporary_url=temporary_url,
                #     prompt=prompt, # Or revised_prompt if available and desired
                #     model_used=final_model_name,
                #     size_used=final_size,
                #     db=db,
                #     user_id=user_id
                # )
                # return permanent_url
                return temporary_url # Return temporary URL directly
            else:
                # This case should ideally not be reached if API call was successful and n=1
                print(f"DALL-E API response did not contain expected data structure: {api_response}")
                raise HTTPException(status_code=500, detail="Image generation succeeded but no image URL was found in the response.")

        except openai.APIConnectionError as e:
            print(f"OpenAI API Connection Error: {e}")
            raise HTTPException(status_code=503, detail=f"Failed to connect to OpenAI API: {e}")
        except openai.RateLimitError as e:
            print(f"OpenAI API Rate Limit Error: {e}")
            raise HTTPException(status_code=429, detail=f"OpenAI API rate limit exceeded: {e}")
        except openai.AuthenticationError as e:
            print(f"OpenAI API Authentication Error: {e}")
            raise HTTPException(status_code=401, detail=f"OpenAI API authentication failed: {e}")
        except openai.BadRequestError as e: # Catching Bad Request specifically (e.g. invalid prompt, content policy)
            print(f"OpenAI API Bad Request Error (e.g. content policy, invalid param): {e}")
            detail_message = f"OpenAI API Bad Request: {e.body.get('message') if e.body and isinstance(e.body, dict) else str(e)}"
            raise HTTPException(status_code=400, detail=detail_message)
        except openai.APIError as e: # Generic OpenAI API error
            print(f"OpenAI API Error: {e}")
            status_code = e.status_code if hasattr(e, 'status_code') else 500
            raise HTTPException(status_code=status_code, detail=f"OpenAI API returned an error: {e}")
        except HTTPException: # Re-raise HTTPExceptions from _save_image_and_log_db
            raise
        except Exception as e:
            print(f"Unexpected error during DALL-E image generation: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred during DALL-E image generation: {str(e)}")

    async def generate_image_stable_diffusion(
        self,
        prompt: str,
        db: Session, # Added db session
        size: Optional[str] = None,
        steps: Optional[int] = None,
        cfg_scale: Optional[float] = None,
        user_id: Optional[int] = None,
        sd_model_checkpoint: Optional[str] = None # Parameter for specific SD model/checkpoint
    ) -> str:
        """
        Generates an image using a Stable Diffusion API, saves it, logs to DB, and returns the permanent image URL.
        """
        if not self.stable_diffusion_api_key or self.stable_diffusion_api_key == "YOUR_STABLE_DIFFUSION_API_KEY_HERE":
            raise HTTPException(status_code=503, detail="Stable Diffusion API key is not configured. Check server settings.")
        if not self.stable_diffusion_api_url: # Validated in __init__ to be None if placeholder or invalid
            raise HTTPException(status_code=503, detail="Stable Diffusion API URL is not configured or is invalid. Check server settings.")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

        headers = {
            # Common practice for API keys, but might vary (e.g., "X-Api-Key", or specific auth for some services)
            "Authorization": f"Bearer {self.stable_diffusion_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Use defaults from settings if not provided by the caller
        final_size = size or settings.STABLE_DIFFUSION_DEFAULT_IMAGE_SIZE
        final_steps = steps or settings.STABLE_DIFFUSION_DEFAULT_STEPS
        final_cfg_scale = cfg_scale or settings.STABLE_DIFFUSION_DEFAULT_CFG_SCALE
        # Use the provided sd_model_checkpoint or default from settings (can be None if API doesn't need it or uses its own default)
        final_sd_model_name = sd_model_checkpoint or settings.STABLE_DIFFUSION_DEFAULT_MODEL


        try:
            width, height = map(int, final_size.split('x'))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid size format for Stable Diffusion. Expected 'widthxheight'. Provided: {final_size}")

        payload = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": final_steps,
            "cfg_scale": final_cfg_scale,
            # Add other common SD parameters if needed, e.g., sampler_index, seed, etc.
        }

        # API-specific: How to specify a model/checkpoint.
        # For AUTOMATIC1111, it might be in "override_settings": { "sd_model_checkpoint": "model_name.safetensors" }
        # Or a top-level "model" field for other APIs. This is an example.
        if final_sd_model_name:
            # This is a placeholder for where you'd put the model if the API supports it.
            # Example for AUTOMATIC1111-like API:
            # if "override_settings" not in payload: payload["override_settings"] = {}
            # payload["override_settings"]["sd_model_checkpoint"] = final_sd_model_name
            # Or for other APIs:
            # payload["model"] = final_sd_model_name
            pass # Actual implementation depends on the specific SD API chosen.

        try:
            # Use self.stable_diffusion_api_url which is now configured from settings
            api_response = requests.post(self.stable_diffusion_api_url, headers=headers, json=payload)
            api_response.raise_for_status()
            response_json = api_response.json()

            temporary_url: Optional[str] = None
            original_filename: Optional[str] = None # If API provides filename/format info

            # Hypothetical response structures - adjust to actual API
            if response_json.get("artifacts") and isinstance(response_json["artifacts"], list) and len(response_json["artifacts"]) > 0:
                image_data = response_json["artifacts"][0]
                if image_data.get("url"): # Ideal: API gives a direct (temp) URL
                    temporary_url = image_data["url"]
                elif image_data.get("base64"):
                    # This service currently expects a URL to download from.
                    # Handling base64 directly would require saving the decoded string.
                    # For now, we state this is not directly supported by _save_image_and_log_db without a URL.
                    # A workaround could be to save base64 to a temp file and pass its file:// URL,
                    # or modify _save_image_and_log_db to accept base64.
                    # For this subtask, we assume the API gives a URL or we can't process it.
                    raise HTTPException(status_code=500, detail="Stable Diffusion API returned base64 image data; direct URL download is preferred by current implementation.")
                # Potentially, API might give filename hint or format
                # original_filename = image_data.get("filename") or image_data.get("format")

            elif response_json.get("image_url"): # Simpler case
                temporary_url = response_json["image_url"]

            if not temporary_url:
                print(f"Stable Diffusion API response did not contain expected image URL: {response_json}")
                raise HTTPException(status_code=500, detail="Image generation with Stable Diffusion succeeded but no image URL was found.")

            # Save image and log to DB
            # permanent_url = await self._save_image_and_log_db(
            #     temporary_url=temporary_url,
            #     prompt=prompt,
            #     model_used=f"stable-diffusion ({final_sd_model_name})" if final_sd_model_name else "stable-diffusion",
            #     size_used=final_size,
            #     db=db,
            #     user_id=user_id,
            #     original_filename_from_api=original_filename
            # )
            # return permanent_url
            return temporary_url # Return temporary URL directly

        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if e.response is not None:
                try: error_detail = f"{e.response.status_code} - {e.response.text}"
                except: pass
            raise HTTPException(status_code=503, detail=f"Failed to connect to Stable Diffusion API: {error_detail}")
        except HTTPException: # Re-raise HTTPExceptions from _save_image_and_log_db
            raise
        except Exception as e:
            print(f"Unexpected error during Stable Diffusion image generation: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred during Stable Diffusion image generation: {str(e)}")


# Example Usage (for testing purposes, if run directly)
# if __name__ == "__main__":
#     import asyncio
#     # This requires .env to be in the same directory or loaded, and OPENAI_API_KEY to be set
#     # For direct execution, you might need to load dotenv explicitly if .env is not in project root relative to this script
#     # from dotenv import load_dotenv
#     # load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env") # Adjust path as needed
    
#     # settings.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Ensure settings object is updated if needed
    
#     async def main():
#         # Test DALL-E
#         if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ["YOUR_OPENAI_API_KEY", "YOUR_API_KEY_HERE"]:
#             try:
#                 service_dalle = ImageGenerationService() # Re-init for this scope if needed or ensure global settings are picked up
#                 print("ImageGenerationService initialized for DALL-E test.")
#                 prompt_dalle = "A cute cat astronaut planting a flag on the moon, digital art"
#                 print(f"Generating DALL-E image for prompt: '{prompt_dalle}'")
#                 image_url_d3 = await service_dalle.generate_image_dalle(prompt=prompt_dalle, model="dall-e-3")
#                 print(f"DALL-E 3 Image URL: {image_url_d3}")
#             except ValueError as ve:
#                 print(f"DALL-E Initialization Error: {ve}")
#             except HTTPException as he:
#                 print(f"DALL-E HTTP Exception: {he.status_code} - {he.detail}")
#             except Exception as e:
#                 print(f"DALL-E unexpected error: {e}")
#         else:
#             print("Skipping DALL-E test: OPENAI_API_KEY not configured.")

#         # Test Stable Diffusion
#         stable_diffusion_key = os.getenv("STABLE_DIFFUSION_API_KEY")
#         if stable_diffusion_key and stable_diffusion_key not in ["YOUR_STABLE_DIFFUSION_API_KEY", "YOUR_SD_API_KEY_PLACEHOLDER"]: # Added placeholder check
#             # Create a new service instance or ensure the existing one picks up the SD key
#             # For this example, assume ImageGenerationService() constructor handles both keys
#             service_sd = ImageGenerationService() # This will print warnings if keys are missing
            
#             # Check if service_sd has the SD key correctly (it should if the env var is set)
#             if not service_sd.stable_diffusion_api_key or service_sd.stable_diffusion_api_key == "YOUR_STABLE_DIFFUSION_API_KEY":
#                 print("Skipping Stable Diffusion test: API key not properly loaded by service.")
#             else:
#                 print("ImageGenerationService initialized for Stable Diffusion test.")
#                 prompt_sd = "A majestic eagle soaring over a futuristic city, photorealistic"
#                 print(f"Generating Stable Diffusion image for prompt: '{prompt_sd}'")
#                 try:
#                     # Note: generate_image_stable_diffusion is async but uses blocking 'requests.post'
#                     # For a real async application, use httpx or run 'requests.post' in a thread pool.
#                     image_url_sd = await service_sd.generate_image_stable_diffusion(prompt=prompt_sd, size="1024x1024", steps=30)
#                     print(f"Stable Diffusion Image URL: {image_url_sd}")
#                 except HTTPException as he:
#                     print(f"Stable Diffusion HTTP Exception: {he.status_code} - {he.detail}")
#                 except Exception as e:
#                     print(f"Stable Diffusion unexpected error: {e}")
#         else:
#             print("Skipping Stable Diffusion test: STABLE_DIFFUSION_API_KEY not configured or is a placeholder.")

#     asyncio.run(main())
