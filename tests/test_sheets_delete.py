from bcsd_api.sheets.client import SheetsClient


def test_delete_row_removes_matching_row(mocker):
    mock_ws = mocker.MagicMock()
    mock_ws.get_all_records.return_value = [
        {"id": "1", "name": "a"},
        {"id": "2", "name": "b"},
    ]
    client = SheetsClient.__new__(SheetsClient)
    client._spreadsheet = mocker.MagicMock()
    client._spreadsheet.worksheet.return_value = mock_ws
    client.delete_row("sheet", "id", "1")
    mock_ws.delete_rows.assert_called_once_with(2)


def test_delete_row_no_match(mocker):
    mock_ws = mocker.MagicMock()
    mock_ws.get_all_records.return_value = [{"id": "1"}]
    client = SheetsClient.__new__(SheetsClient)
    client._spreadsheet = mocker.MagicMock()
    client._spreadsheet.worksheet.return_value = mock_ws
    client.delete_row("sheet", "id", "99")
    mock_ws.delete_rows.assert_not_called()


def test_delete_rows_removes_all_matching(mocker):
    mock_ws = mocker.MagicMock()
    mock_ws.get_all_records.return_value = [
        {"id": "1", "link_id": "L1"},
        {"id": "2", "link_id": "L1"},
        {"id": "3", "link_id": "L2"},
    ]
    client = SheetsClient.__new__(SheetsClient)
    client._spreadsheet = mocker.MagicMock()
    client._spreadsheet.worksheet.return_value = mock_ws
    client.delete_rows("sheet", "link_id", "L1")
    assert mock_ws.delete_rows.call_count == 2
    mock_ws.delete_rows.assert_any_call(3)
    mock_ws.delete_rows.assert_any_call(2)
