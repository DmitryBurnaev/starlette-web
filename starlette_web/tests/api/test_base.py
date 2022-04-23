from typing import Union, Optional

from requests import Response

from common.models import ModelMixin
from common.statuses import ResponseStatus


class BaseTestCase:
    @staticmethod
    def assert_called_with(mock_callable, *args, **kwargs):
        """Check mock object (callable) on call action with provided `args`, `kwargs`"""

        assert mock_callable.called
        mock_call_args = mock_callable.call_args_list[-1]
        if args:
            assert mock_call_args.args == args
        for key, value in kwargs.items():
            assert key in mock_call_args.kwargs, mock_call_args.kwargs
            assert mock_call_args.kwargs[key] == value


class BaseTestAPIView(BaseTestCase):
    url: str = NotImplemented
    default_fail_status_code = 500
    default_fail_response_status = ResponseStatus.INTERNAL_ERROR

    @staticmethod
    def assert_ok_response(response: Response, status_code: int = 200) -> Union[dict, list]:
        response_data = response.json()
        assert response.status_code == status_code
        assert "payload" in response_data, response_data
        assert response_data["status"] == ResponseStatus.OK
        return response_data["payload"]

    def assert_fail_response(
        self, response: Response, status_code: int = None, response_status: str = None
    ) -> Union[dict, list]:

        response_data = response.json()
        assert response.status_code == (status_code or self.default_fail_status_code)
        assert "payload" in response_data, response_data
        assert response_data["status"] == (response_status or self.default_fail_response_status)
        return response_data["payload"]

    @staticmethod
    def assert_bad_request(response: Response, error_details: dict):
        response_data = response.json()
        assert response.status_code == 400
        assert "payload" in response_data, response_data
        response_data = response_data["payload"]
        assert response_data["error"] == "Requested data is not valid."
        for error_field, error_value in error_details.items():
            assert error_field in response_data["details"]
            assert error_value in response_data["details"][error_field]

    @staticmethod
    def assert_not_found(response: Response, instance: ModelMixin):
        assert response.status_code == 404
        response_data = response.json()
        assert response_data["status"] == ResponseStatus.NOT_FOUND
        assert response_data["payload"] == {
            "error": "Requested object not found.",
            "details": (
                f"{instance.__class__.__name__} #{instance.id} "
                f"does not exist or belongs to another user"
            ),
        }

    def assert_unauth(self, response: Response):
        response_data = self.assert_fail_response(
            response, status_code=401, response_status=ResponseStatus.MISSED_CREDENTIALS
        )
        assert response_data == {
            "error": "Authentication is required.",
            "details": "Invalid token header. No credentials provided.",
        }

    def assert_auth_invalid(
        self,
        response_data: Union[Response, dict],
        details: Optional[str],
        response_status=ResponseStatus.AUTH_FAILED,
    ):
        if isinstance(response_data, Response):
            response_data = self.assert_fail_response(
                response_data, status_code=401, response_status=response_status
            )

        assert response_data == {
            "error": "Authentication credentials are invalid.",
            "details": details,
        }
