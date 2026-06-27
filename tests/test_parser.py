import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from src.parser import MessageParser

@patch("src.parser.aiplatform.init")
@patch("src.parser.GenerativeModel")
def test_parse_success(mock_model_class, mock_ai_init):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"target_date": "2026-06-28", "attendance_type": "full_day", "reason": "Rest"}'
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model

    parser = MessageParser(project_id="test-project")
    info = parser.parse("Taking off tomorrow", current_date=date(2026, 6, 27))
    
    assert info.target_date.isoformat() == "2026-06-28"
    assert info.attendance_type == "full_day"
    assert info.reason == "Rest"
