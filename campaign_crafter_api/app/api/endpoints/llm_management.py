from typing import List, Dict, Optional, Annotated # Dict might not be needed anymore, Optional added, Annotated added
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app import models as pydantic_models
from app.db import get_db
from app.services.llm_service import LLMServiceUnavailableError, LLMGenerationError
from app.services.llm_factory import get_llm_service, get_available_models_info
from app.core.config import settings
from app.services.auth_service import get_current_active_user
from app import crud, orm_models # For fetching orm_models.User

router = APIRouter()

# --- Pydantic Models for this endpoint file ---
class LLMConfigStatus(BaseModel):
    status: str
    message: str
    provider: str
    detail: Optional[str] = None

# --- Helper Functions ---
# Added _extract_provider_and_model helper
def _extract_provider_and_model(model_id_with_prefix: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if model_id_with_prefix and "/" in model_id_with_prefix:
        try:
            provider, model_id = model_id_with_prefix.split("/", 1)
            return provider.lower(), model_id
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid model_id_with_prefix format: '{model_id_with_prefix}'. Expected 'provider/model_name'.")
    elif model_id_with_prefix:
        # If no slash, assume it's a model_id for the default provider, or a provider name itself.
        # The get_llm_service factory can try to infer.
        return None, model_id_with_prefix
    return None, None


# --- Endpoints ---

@router.get("/models", response_model=pydantic_models.ModelListResponse, tags=["LLM Management"])
async def list_llm_models(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[pydantic_models.User, Depends(get_current_active_user)]
) -> pydantic_models.ModelListResponse:
    """
    Lists all available LLM models from all configured and available providers for the current user.
    The model IDs returned are prefixed with their provider (e.g., "openai/gpt-3.5-turbo")
    and can be used in other API endpoints that accept a 'model_id_with_prefix'.
    """
    try:
        # Pass db and current_user to get_available_models_info
        available_models_info: List[pydantic_models.ModelInfo] = await get_available_models_info(db=db, current_user=current_user)

        if not available_models_info:
            # This means no models are available for this specific user (e.g. no keys provided, no system keys)
            # or no providers are configured system-wide. Returning an empty list is valid.
            print(f"Warning: No LLM models available for user {current_user.id} from any configured and operational provider.")
            
        return pydantic_models.ModelListResponse(models=available_models_info)
    except HTTPException: # Re-raise HTTPExceptions (e.g. from key fetching in services)
        raise
    except Exception as e:
        print(f"Error fetching available LLM models in endpoint for user {current_user.id}: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve LLM models: {str(e)}")

@router.post("/generate-text", response_model=pydantic_models.LLMTextGenerationResponse, tags=["LLM Management"])
async def generate_text_endpoint( # Renamed to match existing, added db
    request_body: pydantic_models.LLMGenerationRequest, # Changed variable name for clarity
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[pydantic_models.User, Depends(get_current_active_user)]
) -> pydantic_models.LLMTextGenerationResponse:
    """
    Generates text using the specified LLM provider and model.
    """
    if not request_body.prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    provider_name, model_specific_id = _extract_provider_and_model(request_body.model_id_with_prefix)
        
    try:
        # Fetch the ORM user model
        current_user_orm = crud.get_user(db, user_id=current_user.id)
        if not current_user_orm:
            raise HTTPException(status_code=404, detail="User not found in database.")

        llm_service = get_llm_service(
            db=db,
            current_user_orm=current_user_orm,
            provider_name=provider_name,
            model_id_with_prefix=request_body.model_id_with_prefix
        )
        
        text_content = await llm_service.generate_text(
            prompt=request_body.prompt,
            model=model_specific_id,
            temperature=request_body.temperature, # Will use default from Pydantic model if None
            max_tokens=request_body.max_tokens,   # Will use default from Pydantic model if None
            current_user=current_user,
            db=db
        )

        # The response model pydantic_models.LLMTextGenerationResponse is { text: str }
        # The model_used field was removed as it's not in the Pydantic model.
        return pydantic_models.LLMTextGenerationResponse(text=text_content)
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except LLMGenerationError as e: # New block
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError:
        raise HTTPException(status_code=501, detail=f"The generation function for the selected LLM provider or model is not implemented.")
    except ValueError as e: # Catch other value errors, e.g. from service validation
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch-all for other unexpected errors from the LLM service
        print(f"Unexpected error during text generation: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while generating text.")

@router.get("/openai/test-config", response_model=LLMConfigStatus, tags=["LLM Management"])
async def test_openai_config(
    db: Annotated[Session, Depends(get_db)], # db might not be used but kept for consistency
    current_user: Annotated[pydantic_models.User, Depends(get_current_active_user)]
):
    """
    Tests the OpenAI LLM service configuration and availability.
    """
    provider_to_test = "openai"
    try:
        # Fetch the ORM user model
        current_user_orm = crud.get_user(db, user_id=current_user.id)
        if not current_user_orm:
            raise HTTPException(status_code=404, detail="User not found in database.")

        llm_service = get_llm_service(
            db=db,
            current_user_orm=current_user_orm,
            provider_name=provider_to_test
        )
        # The is_available() method for OpenAI now raises LLMServiceUnavailableError if the models.list() call fails
        # So, if get_llm_service succeeds, and is_available also succeeds by not raising, it's available.
        # However, is_available() itself returns True/False after its internal check.
        # The factory's get_llm_service already does some basic config checks.
        # is_available() does a live API call.

        if await llm_service.is_available(current_user=current_user, db=db): # Pass args
            return LLMConfigStatus(
                status="success",
                message="OpenAI configuration appears valid and service is reachable.",
                provider=provider_to_test
            )
        else:
            # This case might be rare if is_available() raises LLMServiceUnavailableError on failure.
            # But if it returns False gracefully, this handles it.
            return LLMConfigStatus(
                status="error",
                message="OpenAI service reported as unavailable after check. Check API key and network.",
                provider=provider_to_test,
                detail="is_available() returned false"
            )
            # If returning a response object for error, need to set status_code on response,
            # or raise HTTPException. For simplicity with response_model, we'll raise HTTPException for errors.
            # This part will effectively be bypassed if is_available() raises on failure.
            # raise HTTPException(status_code=503, detail={"status": "error", ...}) <- this is how you'd do it with HTTPException

    except LLMServiceUnavailableError as e:
        # This catches errors from get_llm_service (e.g. key not configured)
        # or from llm_service.is_available() (e.g. API call failed)
        return LLMConfigStatus(
            status="error",
            message=f"OpenAI configuration test failed for provider '{provider_to_test}'.",
            provider=provider_to_test,
            detail=str(e)
        )
        # To return a 503 status code with this Pydantic model, you'd have to catch and then
        # return a JSONResponse manually, or adjust the endpoint's success status code and
        # only raise HTTPExceptions for errors.
        # For now, this will return 200 OK with error status in body if not raising HTTPException.
        # Correct approach for non-200: raise HTTPException.
        # Let's adjust to raise HTTPException for errors to send proper status codes.

    # Re-evaluating the return for error cases based on typical API design:
    # It's better to raise HTTPExceptions for error statuses.
    # The above LLMConfigStatus return for errors will result in 200 OK.
    # The prompt asked for specific return objects, but HTTP status codes are more RESTful.
    # Let's refine the except block to raise HTTPException.

@router.get("/openai/test-config-v2", response_model=LLMConfigStatus, tags=["LLM Management"])
async def test_openai_config_v2(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[pydantic_models.User, Depends(get_current_active_user)]
):
    """
    Tests the OpenAI LLM service configuration and availability. (V2 with HTTPException for errors)
    """
    provider_to_test = "openai"
    try:
        # Fetch the ORM user model
        current_user_orm = crud.get_user(db, user_id=current_user.id)
        if not current_user_orm:
            raise HTTPException(status_code=404, detail="User not found in database.")

        llm_service = get_llm_service(
            db=db,
            current_user_orm=current_user_orm,
            provider_name=provider_to_test
        )

        if await llm_service.is_available(current_user=current_user, db=db): # Pass args. This now raises LLMServiceUnavailableError on failure
            return LLMConfigStatus(
                status="success",
                message="OpenAI configuration appears valid and service is reachable.",
                provider=provider_to_test
            )
        else:
            # This path should ideally not be reached if is_available raises LLMServiceUnavailableError on any failure.
            # If is_available can return False without raising, this is the case.
            # Given recent refactor of is_available, it should raise LLMServiceUnavailableError.
            # So, this 'else' might be unreachable if is_available is strict.
            raise HTTPException(
                status_code=503,
                detail={ # FastAPI can serialize dicts in HTTPException details
                    "status": "error",
                    "message": "OpenAI service reported as unavailable after explicit check (is_available returned false).",
                    "provider":provider_to_test
                }
            )

    except LLMServiceUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": f"OpenAI configuration test failed for provider '{provider_to_test}'.",
                "provider": provider_to_test,
                "detail": str(e)
            }
        )
    except Exception as e: # Catch-all for other unexpected issues
        print(f"Unexpected error during OpenAI config test: {type(e).__name__} - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "An unexpected internal server error occurred while testing OpenAI configuration.",
                "provider": provider_to_test,
                "detail": str(e)
            }
        )
