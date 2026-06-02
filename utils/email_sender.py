import os
import requests

# =========================================
# RESEND API KEY
# =========================================

RESEND_API_KEY = os.getenv(
    "RESEND_API_KEY"
)

# =========================================
# SEND EMAIL
# =========================================

def send_email(

    receiver_email,
    subject,
    body

):

    try:

        response = requests.post(

            "https://api.resend.com/emails",

            headers={

                "Authorization":
                f"Bearer {RESEND_API_KEY}",

                "Content-Type":
                "application/json"

            },

            json={

                "from":
                "RM Bakes <onboarding@resend.dev>",

                "to":
                [receiver_email],

                "subject":
                subject,

                "text":
                body

            }

        )

        print(
            response.text
        )

        return response.status_code == 200

    except Exception as error:

        print(
            f"Email sending failed: {error}"
        )

        return False
