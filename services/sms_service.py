"""
SMS gateway abstraction.

IMPORTANT: No real SMS account/API key was provided when this project was
generated, so the default 'console' provider does NOT send a real text
message. It logs the OTP to logs/otp.log and to the console so you can test
the full signup/login/reset flow locally.

To go live:
1. Sign up with a provider (Twilio, MSG91, Fast2SMS, etc.) and get an API key.
2. Put the credentials in .env (SMS_PROVIDER, SMS_API_KEY, SMS_API_SECRET, SMS_SENDER_ID).
3. Implement the matching branch below (each is stubbed with a TODO and the
   provider's typical request shape as a comment).
"""
import logging
import subprocess
from flask import current_app

logger = logging.getLogger("rtk.sms")


def send_sms(mobile_number, message):
    provider = current_app.config.get("SMS_PROVIDER", "console")

    if provider == "console":
        try:
            subprocess.run(
                ["termux-sms-send","-n",mobile_number,message],
                check=True
            )
            logger.info("SMS sent to %s", mobile_number)
            return True
        except Exception as e:
            logger.exception("SMS send failed")
            return False

    if provider == "twilio":
        # TODO: implement with the `twilio` package:
        # from twilio.rest import Client
        # client = Client(current_app.config["SMS_API_KEY"], current_app.config["SMS_API_SECRET"])
        # client.messages.create(body=message, from_=current_app.config["SMS_SENDER_ID"], to=mobile_number)
        logger.warning("Twilio provider selected but not implemented yet; falling back to console log.")
        print(f"[SMS SIMULATION - twilio not wired up] To: {mobile_number} | Message: {message}")
        return True

    if provider == "msg91":
        # TODO: implement with MSG91's HTTP API using requests.post(...) and SMS_API_KEY.
        logger.warning("MSG91 provider selected but not implemented yet; falling back to console log.")
        print(f"[SMS SIMULATION - msg91 not wired up] To: {mobile_number} | Message: {message}")
        return True

    logger.error("Unknown SMS provider '%s'; message not sent.", provider)
    return False


def send_otp_sms(mobile_number, otp_code, purpose="verification"):
    if purpose == "password_reset":
        message = f"Your RTK Rural Market password reset OTP is {otp_code}. Valid for a few minutes. Do not share it."
    else:
        message = f"Your RTK Rural Market signup OTP is {otp_code}. Valid for a few minutes. Do not share it."
    return send_sms(mobile_number, message)
