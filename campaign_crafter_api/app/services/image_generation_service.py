from typing import Optional
import openai # Direct import of the openai library
import requests
# import os # No longer needed for Azure saving
import base64 # Added base64 import
import uuid
# import shutil # No longer needed for Azure saving
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
from io import BytesIO # Restored for Azure
from azure.storage.blob import BlobServiceClient # Restored for Azure
from azure.identity import DefaultAzureCredential # Restored for Azure

# Added imports
from app.models import User as UserModel # Changed import path
from ..core.security import decrypt_key # Changed to relative import
# settings is already imported below
# openai is already imported above
# HTTPException is already imported above

from app.core.config import settings
from app.orm_models import GeneratedImage
from app import crud # Added crud import

class ImageGenerationService:
    def __init__(self):
        # OpenAI client is no longer initialized here.
        # Stable Diffusion API key is no longer initialized here.
        # Keys will be fetched per-user, per-request.

        self.stable_diffusion_api_url = settings.STABLE_DIFFUSION_API_URL

        # Warnings for system-level placeholders are still relevant for superuser fallback.
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY in ["YOUR_OPENAI_API_KEY", "YOUR_API_KEY_HERE"]:
            print("Warning: System-level OpenAI API key (settings.OPENAI_API_KEY) is not configured or is a placeholder. Superuser fallback for OpenAI may not work.")

        if not settings.STABLE_DIFFUSION_API_KEY or settings.STABLE_DIFFUSION_API_KEY == "YOUR_STABLE_DIFFUSION_API_KEY_HERE":
            print("Warning: System-level Stable Diffusion API key (settings.STABLE_DIFFUSION_API_KEY) is not configured or is a placeholder. Superuser fallback for Stable Diffusion may not work.")

        if not self.stable_diffusion_api_url or self.stable_diffusion_api_url == "YOUR_STABLE_DIFFUSION_API_URL_HERE":
            print("Warning: Stable Diffusion API URL (settings.STABLE_DIFFUSION_API_URL) is not configured or is a placeholder.")
            self.stable_diffusion_api_url = None # Ensure it's None if it's the placeholder, so calls will fail clearly.
        elif self.stable_diffusion_api_url and not (self.stable_diffusion_api_url.startswith("http://") or self.stable_diffusion_api_url.startswith("https://")):
            print(f"Warning: STABLE_DIFFUSION_API_URL ('{self.stable_diffusion_api_url}') does not look like a valid URL. Proceeding with caution.")

    async def _get_openai_api_key_for_user(self, current_user: UserModel, db: Session) -> str: # Added db
        """
        Retrieves the appropriate OpenAI API key for the given user from DB.
        1. User's own key (decrypted from ORM user model)
        2. Superuser fallback (from settings.OPENAI_API_KEY)
        Raises HTTPException if no valid key is found or user not found.
        """
        orm_user = crud.get_user(db, user_id=current_user.id)
        if not orm_user:
            raise HTTPException(status_code=404, detail="User not found in database for OpenAI key retrieval.")

        if orm_user.encrypted_openai_api_key:
            decrypted_user_key = decrypt_key(orm_user.encrypted_openai_api_key) # Ensure decrypt_key is called
            if decrypted_user_key:
                return decrypted_user_key
            else:
                print(f"Warning: Failed to decrypt stored OpenAI API key for user {orm_user.id}. Checking superuser fallback.")

        if orm_user.is_superuser: # Use orm_user for superuser status
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ["YOUR_OPENAI_API_KEY", "YOUR_API_KEY_HERE", ""]:
                return settings.OPENAI_API_KEY
            else:
                print("Warning: Superuser attempted to use OpenAI for images, but system settings.OPENAI_API_KEY is not configured or is a placeholder.")

        raise HTTPException(status_code=403, detail="OpenAI API key for image generation not available for this user, and no valid fallback key is configured.")

    async def _get_sd_api_key_for_user(self, current_user: UserModel, db: Session) -> str: # Added db
        """
        Retrieves the appropriate Stable Diffusion API key for the given user from DB.
        1. User's own key (decrypted from ORM user model)
        2. Superuser fallback (from settings.STABLE_DIFFUSION_API_KEY)
        Raises HTTPException if no valid key is found or user not found.
        """
        orm_user = crud.get_user(db, user_id=current_user.id)
        if not orm_user:
            raise HTTPException(status_code=404, detail="User not found in database for SD key retrieval.")

        if orm_user.encrypted_sd_api_key:
            decrypted_user_key = decrypt_key(orm_user.encrypted_sd_api_key) # Ensure decrypt_key is called
            if decrypted_user_key:
                return decrypted_user_key
            else:
                print(f"Warning: Failed to decrypt stored Stable Diffusion API key for user {orm_user.id}. Checking superuser fallback.")

        if orm_user.is_superuser: # Use orm_user for superuser status
            if settings.STABLE_DIFFUSION_API_KEY and settings.STABLE_DIFFUSION_API_KEY not in ["YOUR_STABLE_DIFFUSION_API_KEY_HERE", ""]:
                return settings.STABLE_DIFFUSION_API_KEY
            else:
                print("Warning: Superuser attempted to use Stable Diffusion, but system settings.STABLE_DIFFUSION_API_KEY is not configured or is a placeholder.")

        raise HTTPException(status_code=403, detail="Stable Diffusion API key not available for this user, and no valid fallback key is configured.")

    async def _save_image_and_log_db(
        self,
        prompt: str,
        model_used: str,
        size_used: str,
        db: Session,
        temporary_url: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        user_id: Optional[int] = None,
        original_filename_from_api: Optional[str] = None
    ) -> str:
        """
        Downloads an image from a temporary URL or uses provided bytes,
        uploads to Azure Blob Storage, logs it in the database,
        and returns the permanent URL.
        """
        blob_service_client = None
        account_url = None # Will be set if using account name + credential

        if settings.AZURE_STORAGE_CONNECTION_STRING:
            try:
                blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
                # Try to determine account name from connection string for URL construction
                # This is a bit fragile; ideally, AZURE_STORAGE_ACCOUNT_NAME is also set.
                conn_parts = {part.split('=', 1)[0]: part.split('=', 1)[1] for part in settings.AZURE_STORAGE_CONNECTION_STRING.split(';') if '=' in part}
                account_name_from_conn_str = conn_parts.get('AccountName')
                if account_name_from_conn_str:
                    account_url = f"https://{account_name_from_conn_str}.blob.core.windows.net"
                # If account_url is still None here, permanent_image_url construction might fail later if AZURE_STORAGE_ACCOUNT_NAME is also not set.
            except Exception as e:
                print(f"Failed to connect to Azure Storage with connection string: {e}")
                raise HTTPException(status_code=500, detail="Azure Storage configuration error (connection string).")
        elif settings.AZURE_STORAGE_ACCOUNT_NAME:
            try:
                account_url = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
                default_credential = DefaultAzureCredential()
                blob_service_client = BlobServiceClient(account_url, credential=default_credential)
            except Exception as e:
                print(f"Failed to connect to Azure Storage with DefaultAzureCredential: {e}")
                raise HTTPException(status_code=500, detail="Azure Storage configuration error (account name/auth).")
        else:
            raise HTTPException(status_code=500, detail="Azure Storage is not configured (missing account name or connection string).")

        if not blob_service_client:
             raise HTTPException(status_code=500, detail="Failed to initialize Azure BlobServiceClient.")

        file_extension = ".png" # Default
        if original_filename_from_api:
            original_path = Path(original_filename_from_api)
            if original_path.suffix:
                file_extension = original_path.suffix
        elif temporary_url and not image_bytes: # Infer from URL if no bytes provided
            temp_path = Path(temporary_url.split('?')[0])
            if temp_path.suffix and len(temp_path.suffix) > 1:
                file_extension = temp_path.suffix

        if not file_extension.startswith(".") or len(file_extension) > 5: # Sanitize
            file_extension = ".png"

        blob_name = f"{uuid.uuid4().hex}{file_extension}"
        actual_image_bytes = None
        content_type = 'application/octet-stream' # Default

        if image_bytes:
            actual_image_bytes = image_bytes
            if file_extension == ".png": content_type = "image/png"
            elif file_extension in [".jpg", ".jpeg"]: content_type = "image/jpeg"
            elif file_extension == ".webp": content_type = "image/webp"
        elif temporary_url:
            try:
                response = requests.get(temporary_url, stream=True)
                response.raise_for_status()
                actual_image_bytes = response.content

                ct_from_header = response.headers.get('Content-Type')
                if ct_from_header:
                    content_type = ct_from_header
                    # Potentially refine file_extension based on content_type if it was default
                    if file_extension == ".png": # Only if it was default
                        if "image/jpeg" in content_type: file_extension = ".jpg"
                        elif "image/webp" in content_type: file_extension = ".webp"
                        elif "image/png" in content_type: file_extension = ".png"
                        # ... any other common types
                        blob_name = f"{uuid.uuid4().hex}{file_extension}" # Re-generate blob_name if extension changed
            except requests.exceptions.RequestException as e:
                print(f"Failed to download image from temporary URL {temporary_url}: {e}")
                raise HTTPException(status_code=502, detail=f"Failed to download image from source: {e}")
        else:
            raise HTTPException(status_code=400, detail="No image source provided (neither temporary_url nor image_bytes).")

        if not actual_image_bytes:
            raise HTTPException(status_code=500, detail="Failed to retrieve image bytes.")

        permanent_image_url = ""
        try:
            blob_client = blob_service_client.get_blob_client(container=settings.AZURE_STORAGE_CONTAINER_NAME, blob=blob_name)
            with BytesIO(actual_image_bytes) as stream:
                blob_client.upload_blob(stream, overwrite=True, headers={'Content-Type': content_type})
            
            print(f"Image uploaded to Azure Blob Storage: {blob_name} in container {settings.AZURE_STORAGE_CONTAINER_NAME}")

            # Construct permanent URL
            # Priority: 1. account_url (if derived from AZURE_STORAGE_ACCOUNT_NAME), 2. parsed from conn string, 3. settings.AZURE_STORAGE_ACCOUNT_NAME directly
            final_account_url_base = None
            if account_url: # This would be set if AZURE_STORAGE_ACCOUNT_NAME was used for DefaultAzureCredential or parsed from conn string.
                final_account_url_base = account_url.strip('/')
            elif settings.AZURE_STORAGE_ACCOUNT_NAME: # Fallback if not using conn string and account_url wasn't set by it.
                 final_account_url_base = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
            
            if not final_account_url_base:
                raise HTTPException(status_code=500, detail="Cannot determine Azure account URL for image link. Ensure AZURE_STORAGE_ACCOUNT_NAME is set.")

            permanent_image_url = f"{final_account_url_base}/{settings.AZURE_STORAGE_CONTAINER_NAME.strip('/')}/{blob_name}"

        except Exception as e:
            print(f"Failed to upload image to Azure Blob Storage: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload image to cloud storage: {str(e)}")

        db_image = GeneratedImage(
            filename=blob_name,
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

    async def generate_image_dalle(
        self,
        prompt: str,
        db: Session,
        current_user: UserModel, # Added current_user
        size: Optional[str] = None,
        quality: Optional[str] = None,
        model: Optional[str] = None,
        user_id: Optional[int] = None # Kept for logging, will be derived from current_user if None
    ) -> str:
        """
        Generates an image using OpenAI's DALL-E API, saves it, logs to DB, and returns the permanent image URL.
        """
        openai_api_key = await self._get_openai_api_key_for_user(current_user, db) # Pass db
        # Initialize client locally
        dalle_client = openai.OpenAI(api_key=openai_api_key)

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

        # Ensure user_id for logging is consistent with the authenticated user
        log_user_id = current_user.id if user_id is None or user_id != current_user.id else user_id
        if user_id is not None and user_id != current_user.id:
            print(f"Warning: generate_image_dalle called with user_id {user_id} but current_user is {current_user.id}. Using current_user.id for logging.")


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
            api_response = dalle_client.images.generate(
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
                permanent_url = await self._save_image_and_log_db(
                    temporary_url=temporary_url,
                    prompt=prompt,
                    model_used=final_model_name,
                    size_used=final_size,
                    db=db,
                    user_id=log_user_id # Use consistent user_id for logging
                )
                return permanent_url
                # return temporary_url # Return temporary URL directly
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
        db: Session,
        current_user: UserModel, # Added current_user
        size: Optional[str] = None,
        steps: Optional[int] = None,
        cfg_scale: Optional[float] = None,
        user_id: Optional[int] = None, # Kept for logging, will be derived
        sd_model_checkpoint: Optional[str] = None
    ) -> str:
        """
        Generates an image using a Stable Diffusion API, saves it, logs to DB, and returns the permanent image URL.
        """
        sd_api_key = await self._get_sd_api_key_for_user(current_user, db) # Pass db
        # self.stable_diffusion_api_key check removed. sd_api_key is now fetched.

        if not self.stable_diffusion_api_url: # This check remains, as URL is from system settings
            raise HTTPException(status_code=503, detail="Stable Diffusion API URL is not configured or is invalid. Check server settings.")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

        # Ensure user_id for logging is consistent with the authenticated user
        log_user_id = current_user.id if user_id is None or user_id != current_user.id else user_id
        if user_id is not None and user_id != current_user.id:
            print(f"Warning: generate_image_stable_diffusion called with user_id {user_id} but current_user is {current_user.id}. Using current_user.id for logging.")

        # Use defaults from settings if not provided by the caller
        # final_size is still available if needed for logging or aspect_ratio conversion, but not sent directly
        final_size = size or settings.STABLE_DIFFUSION_DEFAULT_IMAGE_SIZE 
        final_steps = steps or settings.STABLE_DIFFUSION_DEFAULT_STEPS
        final_cfg_scale = cfg_scale or settings.STABLE_DIFFUSION_DEFAULT_CFG_SCALE
        final_sd_model_name = sd_model_checkpoint or settings.STABLE_DIFFUSION_DEFAULT_MODEL # For logging

        headers = {
            "Authorization": f"Bearer {sd_api_key}", # Use fetched sd_api_key
            "Accept": "image/*",
        }
        
        form_data = {
            "prompt": prompt,
            "output_format": "webp", # Or png, jpeg
            "steps": str(final_steps), # Ensure form data values are strings if API expects that
            "cfg_scale": str(final_cfg_scale),
            # "model": final_sd_model_name, # If API takes model in form-data
            # "aspect_ratio": "1:1", # Example if API uses aspect_ratio instead of width/height
                                     # Could derive from final_size if needed: e.g. "1024x768" -> "4:3"
        }
        
        # The Stability AI example uses `files` for `multipart/form-data` even if no actual file is uploaded,
        # it can be used to ensure the request is `multipart/form-data`.
        # An empty file part like this is often how you ensure multipart:
        files_payload = {'none': (None, '')} # Sends an empty part named "none"

        try:
            api_response = requests.post(
                self.stable_diffusion_api_url,
                headers=headers,
                data=form_data,
                files=files_payload 
            )

            if api_response.status_code == 200:
                image_bytes_sd = api_response.content
                mime_type = api_response.headers.get("content-type", "image/webp") # Default to webp if not specified
                
                print(f"Successfully received image bytes from Stable Diffusion API for prompt: '{prompt}'. Size: approx {len(image_bytes_sd)} bytes. Mime: {mime_type}")

                sd_filename_hint = "stable_diffusion_image.png" # Default hint
                if "image/webp" in mime_type: sd_filename_hint = "stable_diffusion_image.webp"
                elif "image/jpeg" in mime_type: sd_filename_hint = "stable_diffusion_image.jpg"
                elif "image/png" in mime_type: sd_filename_hint = "stable_diffusion_image.png"

                permanent_url = await self._save_image_and_log_db(
                    prompt=prompt,
                    model_used=final_sd_model_name,
                    size_used=final_size,
                    db=db,
                    image_bytes=image_bytes_sd,
                    user_id=log_user_id, # Use consistent user_id for logging
                    original_filename_from_api=sd_filename_hint
                )
                return permanent_url
            else:
                # Handle API errors
                try:
                    error_data = api_response.json()
                    # Stability AI errors are often in a list under "errors" or "name"/"message" at top level
                    if "errors" in error_data and isinstance(error_data["errors"], list):
                        detail = f"Stable Diffusion API Error: {'; '.join(error_data['errors'])}"
                    elif "name" in error_data and "message" in error_data:
                         detail = f"Stable Diffusion API Error: {error_data['name']} - {error_data['message']}"
                    else:
                        detail = f"Stable Diffusion API Error: {error_data}"
                except ValueError: # If response is not JSON
                    detail = f"Stable Diffusion API Error: {api_response.status_code} - {api_response.text}"
                
                print(f"Stable Diffusion API request failed with status {api_response.status_code}: {detail}")
                raise HTTPException(
                    status_code=api_response.status_code if api_response.status_code >= 400 else 503, 
                    detail=detail
                )

        except requests.exceptions.RequestException as e:
            print(f"Stable Diffusion API request failed: {e}")
            raise HTTPException(status_code=503, detail=f"Failed to connect to Stable Diffusion API: {str(e)}")
        except Exception as e:
            print(f"Unexpected error during Stable Diffusion image generation: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


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
