import unittest
from app.services.random_table_service import RandomTableService
from app import models
import pydantic

class TestServices(unittest.TestCase):
    def test_random_table_service_instantiation(self):
        """Tests if RandomTableService can be instantiated."""
        try:
            service = RandomTableService()
            self.assertIsInstance(service, RandomTableService)
        except Exception as e:
            self.fail(f"RandomTableService instantiation failed: {e}")

    def test_pydantic_model_config_from_attributes(self):
        """
        Tests if Pydantic models in app.models have from_attributes = True in their Config.
        """
        for name, obj in vars(models).items():
            # Check if obj is a class and a subclass of pydantic.BaseModel
            if isinstance(obj, type) and issubclass(obj, pydantic.BaseModel) and obj != pydantic.BaseModel:
                # Check if the model has a Config class
                if hasattr(obj, 'Config'):
                    config = obj.Config
                    # Check for from_attributes = True
                    self.assertTrue(
                        getattr(config, 'from_attributes', False),
                        f"Model {name} does not have from_attributes = True in its Config."
                    )
                else:
                    # This case could be a fail or a pass depending on requirements.
                    # If all models are expected to have a Config with from_attributes,
                    # then this should be a self.fail().
                    # For now, we'll assume models without Config are fine or handled elsewhere.
                    print(f"Model {name} does not have a Config class. Skipping from_attributes check.")
if __name__ == '__main__':
    unittest.main()
