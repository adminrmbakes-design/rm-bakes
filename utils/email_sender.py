import smtplib
import os
import socket

from email.mime.text import MIMEText

from email.mime.multipart import MIMEMultipart



# =========================================
# SMTP CONFIG
# =========================================

SMTP_SERVER = "smtp.gmail.com"

SMTP_PORT = 587

socket.setdefaulttimeout(10)



# =========================================
# AUTH GMAIL
# =========================================

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")



# =========================================
# SEND EMAIL
# =========================================

def send_email(

    receiver_email,
    subject,
    body

):

    try:

        # =================================
        # MESSAGE
        # =================================

        message = MIMEMultipart()

        message["From"] = EMAIL_ADDRESS

        message["To"] = receiver_email

        message["Subject"] = subject



        # =================================
        # BODY
        # =================================

        message.attach(

            MIMEText(
                body,
                "plain"
            )

        )



        # =================================
        # SMTP SERVER
        # =================================
        print("EMAIL:", EMAIL_ADDRESS)
        print("PASSWORD EXISTS:", bool(EMAIL_PASSWORD))
        server = smtplib.SMTP(

            SMTP_SERVER,
            SMTP_PORT,
            timeout=10

        )


        server.ehlo()
        server.starttls()
        server.ehlo()


        server.login(

            EMAIL_ADDRESS,
            EMAIL_PASSWORD

        )



        # =================================
        # SEND
        # =================================

        server.sendmail(

            EMAIL_ADDRESS,
            receiver_email,
            message.as_string()

        )



        # =================================
        # CLOSE
        # =================================

        server.quit()



        print(
            "Email sent successfully ✅"
        )



        return True



    except Exception as error:

        print(
            f"Email sending failed: {error}"
        )



        return False
