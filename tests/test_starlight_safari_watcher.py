import sys
import pathlib
from unittest.mock import Mock, patch

# add scripts directory to sys.path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))

import starlight_safari_watcher as watcher


def test_is_available():
    assert watcher.is_available('Check Availability here')
    assert not watcher.is_available('no slots')


@patch('starlight_safari_watcher.requests.get')
@patch('starlight_safari_watcher.send_alert')
def test_check_once_available(send_alert, mock_get):
    mock_get.return_value = Mock(status_code=200, text='Check Availability')
    assert watcher.check_once() is True
    send_alert.assert_called_once()


@patch('starlight_safari_watcher.requests.get')
def test_check_once_unavailable(mock_get):
    mock_get.return_value = Mock(status_code=200, text='no slots')
    assert watcher.check_once() is False


@patch('starlight_safari_watcher.requests.get')
def test_check_once_status_error(mock_get):
    mock_get.return_value = Mock(status_code=500, text='error')
    assert watcher.check_once() is None
