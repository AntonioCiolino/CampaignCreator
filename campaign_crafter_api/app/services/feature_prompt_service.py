from typing import Optional, List
from sqlalchemy.orm import Session
from app import crud, models, orm_models # Ensure orm_models is available if crud returns them

class FeaturePromptService:
    def __init__(self):
        """
        Service to fetch feature prompts from the database.
        CSV loading logic has been removed.
        """
        pass

    def get_prompt(self, feature_name: str, db: Session) -> Optional[str]:
        """
        Retrieves a feature prompt template by its name from the database.
        """
        db_feature = crud.get_feature_by_name(db, name=feature_name)
        if db_feature:
            return db_feature.template
        return None

    def get_all_features(self, db: Session) -> List[orm_models.Feature]:
        """
        Retrieves all features from the database.
        Returns a list of ORM Feature objects.
        """
        return crud.get_features(db)

# Example usage (for testing - requires database setup and data):
# if __name__ == '__main__':
#     from app.db import SessionLocal, engine, Base
#     # Create tables if they don't exist (e.g., by running the migration script first)
#     # Base.metadata.create_all(bind=engine)
# 
#     db = SessionLocal()
#     service = FeaturePromptService()
# 
#     # Example: Create a feature if it doesn't exist (or use migration script)
#     # existing_feature = crud.get_feature_by_name(db, name="Sample Feature")
#     # if not existing_feature:
#     #     crud.create_feature(db, models.FeatureCreate(name="Sample Feature", template="This is a {{description}}."))
# 
#     prompt = service.get_prompt("Sample Feature", db)
#     if prompt:
#     else:
# 
#     prompt_non_existent = service.get_prompt("NonExistentFeature", db)
#     if prompt_non_existent:
#     else:
# 
#     all_features = service.get_all_features(db)
#     if all_features:
#         for feature in all_features:
#     else:
# 
#     db.close()
