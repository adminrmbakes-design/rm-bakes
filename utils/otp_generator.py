import random

from datetime import (

    datetime,
    timedelta

)



# =========================================
# GENERATE OTP
# =========================================

def generate_otp():

    otp = str(

        random.randint(
            100000,
            999999
        )

    )

    return otp



# =========================================
# OTP EXPIRY
# =========================================

def generate_otp_expiry(

    minutes=5

):

    return datetime.utcnow() + timedelta(

        minutes=minutes

    )



# =========================================
# CHECK OTP EXPIRY
# =========================================

def is_otp_expired(

    expiry_time

):

    if not expiry_time:

        return True



    return datetime.utcnow() > expiry_time