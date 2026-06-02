import smtplib

from email.mime.text import MIMEText

from email.mime.multipart import MIMEMultipart



# =========================================
# SMTP CONFIG
# =========================================

SMTP_SERVER = "smtp.gmail.com"

SMTP_PORT = 587



# =========================================
# AUTH GMAIL
# =========================================

EMAIL_ADDRESS = "auth.rmbakes@gmail.com"



# IMPORTANT:
# Use Gmail App Password
# NOT normal Gmail password

EMAIL_PASSWORD = "myagkwqpcvefjsps"



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

        server = smtplib.SMTP(

            SMTP_SERVER,
            SMTP_PORT

        )



        server.starttls()



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