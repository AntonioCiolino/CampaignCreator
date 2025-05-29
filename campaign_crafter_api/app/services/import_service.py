import json
import zipfile
import io
import os # For path manipulation
from typing import List, Optional, Dict, Any, Union

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import crud
# Ensure correct import for ORM models if they are in a specific module like app.orm_models
# from app import orm_models 
from app.db.base_class import Base as OrmBase # Or wherever your ORM models are based / can be accessed
from app.models.campaign_models import CampaignCreate # Actual Pydantic model for creation
from app.models.import_models import ImportSummaryResponse, SectionStructure, CampaignStructure, ImportErrorDetail

# Placeholder for owner_id until auth is integrated
DEFAULT_OWNER_ID = 1 

class ImportService:
    def __init__(self):
        pass

    def _create_campaign_with_sections(
        self,
        db: Session,
        owner_id: int,
        campaign_title: str,
        campaign_concept: Optional[str],
        campaign_toc: Optional[str],
        sections_data: List[SectionStructure],
        summary: ImportSummaryResponse,
        source_filename: Optional[str] = None # For richer error reporting
    ) -> Any: # Return type should be your ORM Campaign model, e.g. orm_models.Campaign
        """
        Helper to create a new campaign and its sections.
        Prioritizes imported concept and TOC over LLM generation for these fields.
        """
        try:
            # Prepare data for CampaignCreate Pydantic model
            # If concept is provided, use a generic initial_user_prompt to avoid LLM generation for concept.
            # If concept is NOT provided, initial_user_prompt can be more descriptive if desired (though not used here for LLM).
            pydantic_campaign_create = CampaignCreate(
                title=campaign_title,
                initial_user_prompt=f"Imported: {campaign_title}" if not campaign_concept else "Imported campaign concept.",
                model_id_with_prefix_for_concept=None # Explicitly disable LLM generation for concept on import
            )
            
            # Create the campaign object using CRUD
            db_campaign = crud.create_campaign(
                db=db,
                campaign=pydantic_campaign_create,
                owner_id=owner_id,
                # Explicitly set concept and toc to None initially if crud op might try to generate them
                # This depends on crud.create_campaign's behavior.
                # For now, assuming crud.create_campaign won't auto-generate if model_id is None.
            )

            # Directly set imported concept and TOC if they exist
            if campaign_concept is not None:
                db_campaign.concept = campaign_concept
            if campaign_toc is not None:
                db_campaign.toc = campaign_toc
            
            # Commit to save campaign and get ID, then refresh
            db.commit()
            db.refresh(db_campaign)

            summary.imported_campaigns_count += 1
            summary.created_campaign_ids.append(db_campaign.id)
            
            current_section_order = 0
            for section_data in sections_data:
                try:
                    crud.create_campaign_section(
                        db=db,
                        campaign_id=db_campaign.id,
                        section_title=section_data.title,
                        section_content=section_data.content,
                        # Use provided order, or increment if not set
                        order=section_data.order if section_data.order is not None else current_section_order 
                    )
                    summary.imported_sections_count += 1
                    current_section_order = (section_data.order + 1) if section_data.order is not None else (current_section_order + 1)
                except Exception as e_sec:
                    summary.errors.append(ImportErrorDetail(
                        file_name=source_filename,
                        item_identifier=section_data.title or f"Section at index {sections_data.index(section_data)} in '{campaign_title}'",
                        error=f"Failed to create section: {str(e_sec)}"
                    ))
            return db_campaign
        except Exception as e_camp:
            summary.errors.append(ImportErrorDetail(
                file_name=source_filename,
                item_identifier=campaign_title,
                error=f"Failed to create campaign '{campaign_title}': {str(e_camp)}"
            ))
            return None


    def import_from_json_content(
        self, 
        parsed_json_data: Union[Dict[str, Any], List[Dict[str, Any]]], 
        owner_id: int, 
        db: Session, 
        target_campaign_id: Optional[int] = None,
        source_filename: Optional[str] = "Uploaded JSON" # For error reporting
    ) -> ImportSummaryResponse:
        summary = ImportSummaryResponse(created_campaign_ids=[], updated_campaign_ids=[], errors=[])

        if isinstance(parsed_json_data, list): 
            sections_to_import: List[SectionStructure] = []
            for i, item in enumerate(parsed_json_data):
                try:
                    sections_to_import.append(SectionStructure(**item))
                except Exception as e_parse:
                    summary.errors.append(ImportErrorDetail(file_name=source_filename, item_identifier=item.get('title', f"item at index {i}"), error=f"Invalid section structure: {e_parse}"))
            
            if not sections_to_import and not summary.errors:
                summary.errors.append(ImportErrorDetail(file_name=source_filename, error="JSON array was empty or contained no valid sections."))
                return summary

            if target_campaign_id:
                db_campaign_target = crud.get_campaign(db=db, campaign_id=target_campaign_id)
                if not db_campaign_target:
                    summary.errors.append(ImportErrorDetail(file_name=source_filename, error=f"Target campaign ID {target_campaign_id} not found."))
                else:
                    for section_data in sections_to_import:
                        try:
                            crud.create_campaign_section(db, campaign_id=target_campaign_id, section_title=section_data.title, section_content=section_data.content, order=section_data.order)
                            summary.imported_sections_count += 1
                        except Exception as e_sec:
                            summary.errors.append(ImportErrorDetail(file_name=source_filename, item_identifier=section_data.title, error=f"Failed to add section to campaign ID {target_campaign_id}: {str(e_sec)}"))
                    if sections_to_import and target_campaign_id not in summary.updated_campaign_ids:
                        summary.updated_campaign_ids.append(target_campaign_id)
            elif sections_to_import: # Create new campaign if sections exist and no target
                new_campaign_title = sections_to_import[0].title or "Imported Campaign from JSON Sections"
                # Remove the title from the first section if it was used for the campaign title and it's generic
                if sections_to_import[0].title == new_campaign_title and not parsed_json_data[0].get('title'): # Check if title was auto-generated
                     sections_to_import[0].title = "Introduction" # Or some other default or None

                self._create_campaign_with_sections(db, owner_id, new_campaign_title, None, None, sections_to_import, summary, source_filename=source_filename)

        elif isinstance(parsed_json_data, dict):
            try:
                campaign_data = CampaignStructure(**parsed_json_data)
            except Exception as e_parse:
                summary.errors.append(ImportErrorDetail(file_name=source_filename, item_identifier=parsed_json_data.get('title'), error=f"Invalid campaign structure in JSON: {e_parse}"))
                return summary

            if target_campaign_id: 
                db_campaign_target = crud.get_campaign(db=db, campaign_id=target_campaign_id)
                if not db_campaign_target:
                    summary.errors.append(ImportErrorDetail(file_name=source_filename, error=f"Target campaign ID {target_campaign_id} not found."))
                else: # Add sections from this campaign structure to an existing one
                    for section_data in campaign_data.sections:
                        try:
                            crud.create_campaign_section(db, campaign_id=target_campaign_id, section_title=section_data.title, section_content=section_data.content, order=section_data.order)
                            summary.imported_sections_count += 1
                        except Exception as e_sec:
                             summary.errors.append(ImportErrorDetail(file_name=source_filename, item_identifier=section_data.title, error=f"Failed to add section to campaign ID {target_campaign_id}: {str(e_sec)}"))
                    if campaign_data.sections and target_campaign_id not in summary.updated_campaign_ids:
                        summary.updated_campaign_ids.append(target_campaign_id)
            else: # Create new campaign from this CampaignStructure
                self._create_campaign_with_sections(
                    db, owner_id, campaign_data.title, campaign_data.concept, 
                    campaign_data.toc, campaign_data.sections, summary, source_filename=source_filename
                )
        else:
            summary.errors.append(ImportErrorDetail(file_name=source_filename, error="Invalid JSON root. Expected a single campaign object or a list of section objects."))
        
        if not summary.errors and summary.imported_campaigns_count == 0 and summary.imported_sections_count == 0:
            summary.message = "Import from JSON successful, but no new campaigns or sections were created (data might have been empty or all items had errors)."
        elif summary.errors:
            summary.message = "Import from JSON completed with errors."
        
        return summary


    def import_from_zip_file(
        self, 
        file_bytes: bytes, 
        owner_id: int, 
        db: Session, 
        target_campaign_id: Optional[int] = None,
        process_folders_as_structure: bool = False
    ) -> ImportSummaryResponse:
        summary = ImportSummaryResponse(created_campaign_ids=[], updated_campaign_ids=[], errors=[])
        
        # { "campaign_title_or_path": CampaignStructure, ... }
        parsed_campaigns_data: Dict[str, CampaignStructure] = {}
        # Sections for a flat import or to be added to target_campaign_id
        loose_sections: List[SectionStructure] = [] 

        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                file_list = sorted(zf.infolist(), key=lambda x: x.filename) # Process in predictable order

                for member in file_list:
                    if member.is_dir() or member.filename.startswith('__MACOSX/') or not member.filename.strip():
                        continue

                    file_name = member.filename
                    
                    try:
                        file_content_bytes = zf.read(member.name)
                        file_content_str = file_content_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            file_content_str = file_content_bytes.decode('latin-1', errors='replace')
                            summary.errors.append(ImportErrorDetail(file_name=file_name, error="File not UTF-8, decoded with replacements."))
                        except Exception as e_decode_fallback:
                            summary.errors.append(ImportErrorDetail(file_name=file_name, error=f"Failed to decode file: {e_decode_fallback}"))
                            continue
                    except Exception as e_read:
                        summary.errors.append(ImportErrorDetail(file_name=file_name, error=f"Failed to read file from zip: {e_read}"))
                        continue
                    
                    path_parts = [part for part in file_name.split('/') if part] # Clean empty parts
                    base_filename = path_parts[-1] if path_parts else file_name
                    title_from_filename = os.path.splitext(base_filename)[0]

                    # Determine target collection based on structure processing and path
                    current_collection_key = None
                    is_part_of_structured_campaign = False

                    if process_folders_as_structure and len(path_parts) > 1:
                        current_collection_key = path_parts[0] # Top-level folder name
                        is_part_of_structured_campaign = True
                        if current_collection_key not in parsed_campaigns_data:
                            parsed_campaigns_data[current_collection_key] = CampaignStructure(title=current_collection_key, sections=[])
                    
                    # Process file content
                    if base_filename.lower().endswith(".txt"):
                        section = SectionStructure(title=title_from_filename, content=file_content_str)
                        if is_part_of_structured_campaign and current_collection_key:
                            parsed_campaigns_data[current_collection_key].sections.append(section)
                        else:
                            loose_sections.append(section)
                    
                    elif base_filename.lower().endswith(".json"):
                        try:
                            json_content = json.loads(file_content_str)
                            if isinstance(json_content, dict) and "title" in json_content and "sections" in json_content: # CampaignStructure
                                campaign_struct = CampaignStructure(**json_content)
                                if is_part_of_structured_campaign and current_collection_key: # Campaign JSON inside a folder
                                    # Merge this campaign's data into the folder-campaign
                                    parsed_campaigns_data[current_collection_key].title = campaign_struct.title or current_collection_key # Prefer JSON title
                                    parsed_campaigns_data[current_collection_key].concept = campaign_struct.concept or parsed_campaigns_data[current_collection_key].concept
                                    parsed_campaigns_data[current_collection_key].toc = campaign_struct.toc or parsed_campaigns_data[current_collection_key].toc
                                    parsed_campaigns_data[current_collection_key].sections.extend(campaign_struct.sections)
                                else: # Top-level campaign JSON
                                    parsed_campaigns_data[campaign_struct.title or title_from_filename] = campaign_struct
                            elif isinstance(json_content, list): # List of SectionStructures
                                sections_from_json = [SectionStructure(**s) for s in json_content]
                                if is_part_of_structured_campaign and current_collection_key:
                                    parsed_campaigns_data[current_collection_key].sections.extend(sections_from_json)
                                else:
                                    loose_sections.extend(sections_from_json)
                            else:
                                summary.errors.append(ImportErrorDetail(file_name=file_name, error="JSON file is not a Campaign object or list of Sections."))
                        except json.JSONDecodeError:
                            summary.errors.append(ImportErrorDetail(file_name=file_name, error="Invalid JSON format."))
                        except Exception as e_parse: # Pydantic validation etc.
                            summary.errors.append(ImportErrorDetail(file_name=file_name, error=f"Error parsing JSON structure: {e_parse}"))
        except zipfile.BadZipFile:
            summary.errors.append(ImportErrorDetail(error="Invalid or corrupted Zip file."))
            return summary
        except Exception as e_zip:
            summary.errors.append(ImportErrorDetail(error=f"Error processing Zip file: {str(e_zip)}"))
            return summary

        # Create/update database entities from parsed_campaigns_data and loose_sections
        if target_campaign_id:
            db_campaign_target = crud.get_campaign(db=db, campaign_id=target_campaign_id)
            if not db_campaign_target:
                summary.errors.append(ImportErrorDetail(error=f"Target campaign ID {target_campaign_id} not found. Cannot add loose sections or folder contents."))
            else:
                # Add loose sections first
                for section_data in loose_sections:
                    try:
                        crud.create_campaign_section(db, campaign_id=target_campaign_id, section_title=section_data.title, section_content=section_data.content, order=section_data.order)
                        summary.imported_sections_count += 1
                    except Exception as e_sec:
                        summary.errors.append(ImportErrorDetail(item_identifier=section_data.title or "Untitled section from Zip root", error=f"Failed to add section to campaign ID {target_campaign_id}: {str(e_sec)}"))
                
                # If process_folders_as_structure, treat folders as new top-level sections in target_campaign_id
                if process_folders_as_structure:
                    for folder_name, campaign_data_from_folder in parsed_campaigns_data.items():
                        # Create a main section for the folder
                        folder_section_content = campaign_data_from_folder.concept or "" # Use concept as main content if available
                        if campaign_data_from_folder.toc: # Append TOC to folder section content
                            folder_section_content += f"\n\n## Table of Contents\n{campaign_data_from_folder.toc}"
                        
                        try:
                            # Create the folder as a section
                            db_folder_section = crud.create_campaign_section(db, campaign_id=target_campaign_id, section_title=folder_name, section_content=folder_section_content)
                            summary.imported_sections_count += 1
                            # Now add files from that folder as sub-content (e.g. appended to folder_section content)
                            # This part needs more thought: how to represent sub-sections?
                            # For now, just concatenating content from folder's sections into this one section for simplicity.
                            # A better approach might involve hierarchical sections if the model supports it.
                            additional_content = []
                            for s_data in campaign_data_from_folder.sections:
                                additional_content.append(f"\n\n### {s_data.title or 'Sub-section'}\n{s_data.content}")
                                summary.imported_sections_count +=1 # Counting these as imported conceptually
                            
                            if additional_content:
                                db_folder_section.content += "".join(additional_content)
                                db.commit()
                                db.refresh(db_folder_section)

                        except Exception as e_folder_sec:
                            summary.errors.append(ImportErrorDetail(item_identifier=folder_name, error=f"Failed to create section for folder '{folder_name}' in campaign ID {target_campaign_id}: {str(e_folder_sec)}"))
                
                if (loose_sections or (process_folders_as_structure and parsed_campaigns_data)) and target_campaign_id not in summary.updated_campaign_ids:
                    summary.updated_campaign_ids.append(target_campaign_id)

        else: # No target_campaign_id, create new campaigns
            if loose_sections:
                self._create_campaign_with_sections(db, owner_id, "Imported Loose Files from Zip", None, None, loose_sections, summary, source_filename="Zip Archive (Root)")
            for campaign_title_key, campaign_obj_data in parsed_campaigns_data.items():
                self._create_campaign_with_sections(
                    db, owner_id, campaign_obj_data.title or campaign_title_key, 
                    campaign_obj_data.concept, campaign_obj_data.toc, 
                    campaign_obj_data.sections, summary, source_filename=f"Zip Archive ({campaign_title_key})"
                )

        if not summary.errors and summary.imported_campaigns_count == 0 and summary.imported_sections_count == 0:
            summary.message = "Zip import successful, but no new campaigns or sections were created."
        elif summary.errors:
            summary.message = "Zip import process completed with errors."
            
        return summary
