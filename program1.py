import time
import random

class SendSMS:
    def __init__(self, phone_number, proxy):
        self.phone_number = phone_number
        self.proxy = proxy

    def SendOtp(self):
        # Simulate sending SMS via a proxy
        print(f"Sending OTP to {self.phone_number} using proxy {self.proxy}")
        # Simulate response for demonstration (random success/failure)
        response = "sent successfully" if random.choice([True, False]) else "failed"
        if 'sent successfully' in response:
            print("OTP sent successfully")
            return True
        else:
            print("OTP sending failed")
            return False

class SubmitSMS:
    def SubmitOtp(self, trigger_id, SMS_code):
        # Simulate submitting the SMS code
        print(f"Submitting OTP code {SMS_code} for trigger ID {trigger_id}")
        # Simulate response for demonstration (random success/failure)
        response = "submitted successfully" if random.choice([True, False]) else "failed"
        if 'submitted successfully' in response:
            print("OTP submitted successfully")
            return True
        else:
            print("OTP submission failed")
            return False

# Define the list of country-operator pairs managed by this program
country_operator_pairs = ["Uzbekistan_UzMobile", "Ukraine_3Mob"]

def run_sms_trigger():
    while True:
        for pair in country_operator_pairs:
            # Generate mock phone number and proxy (replace with real values as needed)
            phone_number = f"+99890{random.randint(1000000, 9999999)}"  # Random phone number
            proxy = f"http://proxy.example.com"  # Proxy placeholder

            # Create SendSMS instance and send OTP
            sms_sender = SendSMS(phone_number, proxy)
            otp_sent = sms_sender.SendOtp()

            if otp_sent:
                # If OTP was sent, simulate receiving an SMS code and submitting it
                trigger_id = random.randint(1000, 9999)
                SMS_code = random.randint(100000, 999999)  # Simulate a 6-digit OTP code
                sms_submitter = SubmitSMS()
                sms_submitter.SubmitOtp(trigger_id, SMS_code)

            # Limit SMS sending rate to 10 per minute per country
            time.sleep(6)  # Pause to respect the rate limit

if __name__ == "__main__":
    print("Starting SMS service for pairs:", country_operator_pairs)
    run_sms_trigger()
