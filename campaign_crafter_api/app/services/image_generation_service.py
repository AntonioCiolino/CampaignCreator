from typing import Optional
import openai # Direct import of the openai library
from fastapi import HTTPException # For raising HTTP errors directly from service in this case

from app.core.config import settings

class ImageGenerationService:
    def __init__(self):
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY in ["YOUR_OPENAI_API_KEY", "YOUR_API_KEY_HERE"]:
            raise ValueError("OpenAI API key is not configured or is a placeholder. Cannot initialize ImageGenerationService.")
        
        try:
            # Ensure client is initialized. 
            # For v1.0.0+ of openai library, client is instantiated.
            # If older versions were used, it might be just `openai.api_key = settings.OPENAI_API_KEY`
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            # Catch any error during client initialization
            raise ValueError(f"Failed to initialize OpenAI client: {e}")

    async def generate_image(
        self, 
        prompt: str, 
        size: Optional[str] = None, 
        quality: Optional[str] = None, 
        model: Optional[str] = None
    ) -> str:
        """
        Generates an image using OpenAI's DALL-E API and returns the image URL.
        """
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

        final_model = model or settings.OPENAI_DALLE_MODEL_NAME
        final_size = size or settings.OPENAI_DALLE_DEFAULT_IMAGE_SIZE
        final_quality = quality or settings.OPENAI_DALLE_DEFAULT_IMAGE_QUALITY

        # Validate size for DALL-E 3 if it's the selected model
        if final_model == "dall-e-3":
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
        elif final_model == "dall-e-2": # Example if DALL-E 2 was also an option
             if final_size not in ["256x256", "512x512", "1024x1024"]:
                 raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid size for DALL-E 2. Supported sizes are 256x256, 512x512, 1024x1024. Provided: {final_size}"
                )
             # DALL-E 2 does not use 'quality' parameter in the same way, so it might be ignored or error if sent.

        try:
            response = await self.client.images.generate( # Use await for async client call
                model=final_model,
                prompt=prompt,
                size=final_size, # type: ignore (OpenAI SDK uses Literal for size, but string is fine if validated)
                quality=final_quality, # type: ignore (Same for quality)
                n=1,
                response_format="url" # Get a temporary URL for the image
            )
            
            if response.data and len(response.data) > 0 and response.data[0].url:
                image_url = response.data[0].url
                return image_url
            else:
                # This case should ideally not be reached if API call was successful and n=1
                print(f"DALL-E API response did not contain expected data structure: {response}")
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
            # The error object 'e' often has a 'body' attribute with more details, e.g. e.body.get('message')
            detail_message = f"OpenAI API Bad Request: {e.body.get('message') if e.body and isinstance(e.body, dict) else str(e)}"
            raise HTTPException(status_code=400, detail=detail_message)
        except openai.APIError as e: # Generic OpenAI API error
            print(f"OpenAI API Error: {e}")
            # Attempt to get status code from the error object if available
            status_code = e.status_code if hasattr(e, 'status_code') else 500
            raise HTTPException(status_code=status_code, detail=f"OpenAI API returned an error: {e}")
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Unexpected error during image generation: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred during image generation: {str(e)}")

# Example Usage (for testing purposes, if run directly)
# if __name__ == "__main__":
#     import asyncio
#     # This requires .env to be in the same directory or loaded, and OPENAI_API_KEY to be set
#     # For direct execution, you might need to load dotenv explicitly if .env is not in project root relative to this script
#     # from dotenv import load_dotenv
#     # load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env") # Adjust path as needed
    
#     # settings.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Ensure settings object is updated if needed
    
#     async def main():
#         if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "YOUR_OPENAI_API_KEY":
#             print("Skipping ImageGenerationService direct test: OPENAI_API_KEY not configured.")
#             return

#         try:
#             service = ImageGenerationService()
#             print("ImageGenerationService initialized.")
#             prompt = "A whimsical fantasy landscape with floating islands and a friendly dragon, digital art"
#             print(f"Generating image for prompt: '{prompt}'")
            
#             # Test with DALL-E 3 defaults
#             image_url_d3 = await service.generate_image(prompt=prompt, model="dall-e-3")
#             print(f"DALL-E 3 Image URL: {image_url_d3}")

#             # Test with DALL-E 2 (if you want to support it and have access)
#             # image_url_d2 = await service.generate_image(prompt=prompt, model="dall-e-2", size="512x512")
#             # print(f"DALL-E 2 Image URL: {image_url_d2}")

#         except ValueError as ve:
#             print(f"Initialization Error: {ve}")
#         except HTTPException as he:
#             print(f"HTTP Exception during generation: {he.status_code} - {he.detail}")
#         except Exception as e:
#             print(f"An unexpected error occurred: {e}")

#     asyncio.run(main())
