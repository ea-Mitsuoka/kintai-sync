import pytest
from unittest.mock import MagicMock, patch
from src.parser import MessageParser
from src.models import AttendanceInfo
from datetime import date

@pytest.fixture
def parser():
    # Patch aiplatform.init to avoid any side effects
    with patch("src.parser.aiplatform.init"):
        return MessageParser(project_id="test-project", location="us-central1")

@patch("src.parser.GenerativeModel")
def test_parse_success(mock_model_class, parser):
    mock_model = mock_model_class.return_value
    mock_response = MagicMock()
    mock_response.text = '{"target_date": "2026-06-28", "attendance_type": "full_day", "reason": "Holiday"}'
    mock_model.generate_content.return_value = mock_response
    
    # Ensure the parser uses the mocked model
    parser.model = mock_model
    
    result = parser.parse("Taking a holiday tomorrow")
    
    assert isinstance(result, AttendanceInfo)
    # The parser converts the string date to a date object
    assert result.target_date == date(2026, 6, 28)
    assert result.attendance_type == "full_day"

@patch("src.parser.GenerativeModel")
def test_parse_failure(mock_model_class, parser):
    mock_model = mock_model_class.return_value
    mock_model.generate_content.side_effect = Exception("Vertex AI Error")
    
    # Ensure the parser uses the mocked model
    parser.model = mock_model
    
    with pytest.raises(Exception) as excinfo:
        parser.parse("Taking a holiday tomorrow")
    
    assert "Vertex AI Error" in str(excinfo.value)

@patch("src.parser.GenerativeModel")
@patch("src.parser.aiplatform.init")
def test_parser_init_defaults(mock_init, mock_model_class):
    # Test initialization with default values from config/env
    with patch("os.getenv", return_value="env-project"):
        parser = MessageParser()
        mock_init.assert_called_with(project="env-project", location="us-central1")
