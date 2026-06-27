import pytest
from unittest.mock import MagicMock, patch
from src.history import HistoryManager

@patch("google.cloud.firestore.Client")
def test_get_user_settings_found(mock_firestore):
    # Mock firestore doc.exists and to_dict()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"morning_off_start": "08:30"}
    
    mock_firestore.return_value.collection.return_value.document.return_value.get.return_value = mock_doc
    
    manager = HistoryManager(project_id="test-project")
    settings = manager.get_user_settings("U123")
    
    assert settings["morning_off_start"] == "08:30"
    assert settings["timezone"] == "Asia/Tokyo"  # Default preserved

@patch("google.cloud.firestore.Client")
def test_get_user_settings_not_found(mock_firestore):
    mock_doc = MagicMock()
    mock_doc.exists = False
    
    mock_firestore.return_value.collection.return_value.document.return_value.get.return_value = mock_doc
    
    manager = HistoryManager(project_id="test-project")
    settings = manager.get_user_settings("U_UNKNOWN")
    
    assert settings["morning_off_start"] == "09:00"  # Default

@patch("google.cloud.firestore.Client")
def test_get_task_status_found(mock_firestore):
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"status": "success"}
    mock_firestore.return_value.collection.return_value.document.return_value.get.return_value = mock_doc
    
    manager = HistoryManager(project_id="test-project")
    status = manager.get_task_status("msg_123")
    assert status["status"] == "success"

@patch("google.cloud.firestore.Client")
def test_update_task_status(mock_firestore):
    mock_doc_ref = MagicMock()
    mock_firestore.return_value.collection.return_value.document.return_value = mock_doc_ref
    
    manager = HistoryManager(project_id="test-project")
    manager.update_task_status("msg_123", "processing", {"sub": "ok"})
    
    mock_doc_ref.set.assert_called_once()
    args, kwargs = mock_doc_ref.set.call_args
    assert args[0]["status"] == "processing"
    assert args[0]["subtasks"]["sub"] == "ok"
