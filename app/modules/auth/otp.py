DEMO_OTP_CODE = "1234"


class MockOtpProvider:
    def send_code(self, phone: str) -> str:
        return DEMO_OTP_CODE
