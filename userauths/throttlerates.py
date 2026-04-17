from rest_framework.throttling import UserRateThrottle

# OTP resend throttle
class OTPResendThrottle(UserRateThrottle):
    scope = 'otp_resend'

# Login attempts throttle
class LoginAttemptThrottle(UserRateThrottle):
    scope = 'login_attempt'

# Password reset requests throttle
class PasswordResetThrottle(UserRateThrottle):
    scope = 'password_reset'

# Optional: Registration throttle
class RegistrationThrottle(UserRateThrottle):
    scope = 'registration'



