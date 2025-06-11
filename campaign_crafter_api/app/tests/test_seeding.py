import pytest
from unittest.mock import patch, mock_open, MagicMock
from sqlalchemy.orm import Session
import io # Required for StringIO

# Make sure the path to app is correct if tests are run from a different root
# For example, if tests are run from project root:
from app.core.seeding import seed_features
from app.models import FeatureCreate # For type checking if needed

# If crud methods directly add to session and expect commit outside,
# the db_mock doesn't need to do much.

@patch('app.core.seeding.crud.get_feature_by_name')
@patch('app.core.seeding.crud.create_feature')
@patch('app.core.seeding.FEATURES_CSV_PATH') # Mock the path to control file access
def test_seed_features_parses_quoted_templates_correctly(
    mock_csv_path,
    mock_create_feature,
    mock_get_feature_by_name
):
    # Arrange
    db_mock = MagicMock(spec=Session)

    # Simulate that no features currently exist in the DB
    mock_get_feature_by_name.return_value = None

    # CSV content with a feature template containing commas and enclosed in quotes
    csv_content = (
        "Feature Name,Template\n"
        "TestFeature1,\"This is a template, with commas, and newlines.\nIt should be parsed as one field.\"\n"
        "TestFeature2,Simple template without comma\n"
        "TestFeature3,\"Another template, also with commas\"\n"
    )

    # Mock FEATURES_CSV_PATH.is_file() to return True
    mock_csv_path.is_file.return_value = True

    # Use mock_open to simulate reading the CSV file
    # The mock_open().return_value is the file handle mock
    m_open = mock_open(read_data=csv_content)

    with patch('builtins.open', m_open):
        seed_features(db_mock)

    # Assert
    # Check that create_feature was called with correctly parsed templates

    # Expected calls to mock_create_feature:
    # Call 1: name="TestFeature1", template="This is a template, with commas, and newlines.
#It should be parsed as one field."
    # Call 2: name="TestFeature2", template="Simple template without comma"
    # Call 3: name="TestFeature3", template="Another template, also with commas"

    assert mock_create_feature.call_count == 3

    calls = mock_create_feature.call_args_list

    # Verify TestFeature1
    args_tf1, kwargs_tf1 = calls[0]
    created_feature_tf1 = kwargs_tf1.get('feature') # Assuming feature is passed as a keyword arg
    # Corrected: crud.create_feature(db, feature=feature_data), so feature_data is models.FeatureCreate
    assert created_feature_tf1.name == "TestFeature1"
    assert created_feature_tf1.template == "This is a template, with commas, and newlines.\nIt should be parsed as one field."

    # Verify TestFeature2
    args_tf2, kwargs_tf2 = calls[1]
    created_feature_tf2 = kwargs_tf2.get('feature')
    assert created_feature_tf2.name == "TestFeature2"
    assert created_feature_tf2.template == "Simple template without comma"

    # Verify TestFeature3
    args_tf3, kwargs_tf3 = calls[2]
    created_feature_tf3 = kwargs_tf3.get('feature')
    assert created_feature_tf3.name == "TestFeature3"
    assert created_feature_tf3.template == "Another template, also with commas"

    # Ensure get_feature_by_name was called for each feature
    assert mock_get_feature_by_name.call_count == 3


@patch('app.core.seeding.crud.get_feature_by_name')
@patch('app.core.seeding.crud.create_feature') # Mock create_feature as we are testing update path
@patch('app.core.seeding.FEATURES_CSV_PATH')
def test_seed_features_updates_existing_correctly(
    mock_csv_path,
    mock_create_feature, # Keep this mocked even if not expecting calls
    mock_get_feature_by_name
):
    # Arrange
    db_mock = MagicMock(spec=Session)

    # Simulate an existing feature
    existing_feature_name = "UpdatableFeature"
    original_template = "Original template content."
    updated_template = "Updated template content, with commas."

    # This is the mock for the SQLAlchemy model instance
    mock_existing_feature_obj = MagicMock() # spec=models.Feature if you have it imported
    mock_existing_feature_obj.name = existing_feature_name
    mock_existing_feature_obj.template = original_template

    # First call to get_feature_by_name returns the existing feature
    mock_get_feature_by_name.return_value = mock_existing_feature_obj

    csv_content_update = (
        "Feature Name,Template\n"
        f"{existing_feature_name},\"{updated_template}\"\n" # Note the quotes for the template
    )

    mock_csv_path.is_file.return_value = True
    m_open_update = mock_open(read_data=csv_content_update)

    with patch('builtins.open', m_open_update):
        seed_features(db_mock)

    # Assert
    # 1. create_feature should NOT have been called
    mock_create_feature.assert_not_called()

    # 2. get_feature_by_name should have been called once
    mock_get_feature_by_name.assert_called_once_with(db_mock, name=existing_feature_name)

    # 3. The existing feature's template should have been updated
    assert mock_existing_feature_obj.template == updated_template

    # 4. db.add should have been called with the updated feature object to stage it
    db_mock.add.assert_called_once_with(mock_existing_feature_obj)


@patch('app.core.seeding.crud.get_feature_by_name')
@patch('app.core.seeding.crud.create_feature')
@patch('app.core.seeding.FEATURES_CSV_PATH')
def test_seed_features_creates_features_with_none_user_id(
    mock_csv_path,
    mock_create_feature,
    mock_get_feature_by_name
):
    # Arrange
    db_mock = MagicMock(spec=Session)
    mock_get_feature_by_name.return_value = None  # Simulate no existing features

    csv_content = (
        "Feature Name,Template\n"
        "SystemFeature1,Template for system feature 1\n"
        "SystemFeature2,Template for system feature 2\n"
    )
    mock_csv_path.is_file.return_value = True
    m_open = mock_open(read_data=csv_content)

    with patch('builtins.open', m_open):
        seed_features(db_mock)

    # Assert
    assert mock_create_feature.call_count == 2

    calls = mock_create_feature.call_args_list

    # Check the first call
    args_call1, kwargs_call1 = calls[0]

    # crud.create_feature is called as: crud.create_feature(db, feature=feature_data)
    # So, db is the first positional arg, feature is a keyword arg.
    # user_id is not passed by seed_features, so it won't be in kwargs_call1.

    assert args_call1[0] == db_mock # db argument
    actual_feature_obj_call1 = kwargs_call1.get('feature')
    assert 'user_id' not in kwargs_call1 # Crucial: seed_features does not pass user_id

    assert actual_feature_obj_call1.name == "SystemFeature1"
    assert actual_feature_obj_call1.template == "Template for system feature 1"
    # The FeatureCreate object itself should have user_id as None by default
    # because seed_features creates it as FeatureCreate(name=fn, template=ft)
    # and FeatureCreate.user_id defaults to None.
    assert actual_feature_obj_call1.user_id is None

    # Check the second call
    args_call2, kwargs_call2 = calls[1]
    assert args_call2[0] == db_mock # db argument
    actual_feature_obj_call2 = kwargs_call2.get('feature')
    assert 'user_id' not in kwargs_call2 # Crucial: seed_features does not pass user_id

    assert actual_feature_obj_call2.name == "SystemFeature2"
    assert actual_feature_obj_call2.template == "Template for system feature 2"
    assert actual_feature_obj_call2.user_id is None

    # Also ensure get_feature_by_name was called for each feature
    assert mock_get_feature_by_name.call_count == 2
