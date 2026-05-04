from eos_security import classify_data_class


def test_gmail_raw_body_classified_sensitive() -> None:
    assert classify_data_class("gmail raw body: hello from inbox") == "Class 3"


def test_maps_location_history_classified_sensitive() -> None:
    assert classify_data_class("maps location history export") == "Class 3"


def test_drive_file_content_classified_sensitive() -> None:
    assert classify_data_class("drive file content: quarterly planning notes") == "Class 3"


def test_secret_values_classified_secret() -> None:
    assert classify_data_class("client_secret=GOCSPX-dummyClientSecretValue123") == "Class 4"
