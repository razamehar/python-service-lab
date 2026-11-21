
from app.utils import get_welcome_message


def test_get_welcome_message():
    result = get_welcome_message()

    assert result == "Welcome to the AWS CI/CD Demo API"
    assert isinstance(result, str)
