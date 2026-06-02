// ========================================
// RM BAKES - PROFILE JS
// ========================================



// ========================================
// TOAST
// ========================================

function showToast(message){

    const toast =
        document.createElement("div");

    toast.className =
        "custom-toast";

    toast.innerText =
        message;

    document.body.appendChild(toast);

    setTimeout(() => {

        toast.classList.add("show");

    }, 100);

    setTimeout(() => {

        toast.classList.remove("show");

        setTimeout(() => {

            toast.remove();

        }, 300);

    }, 2400);

}



// ========================================
// SAVE PROFILE DETAILS
// ========================================

const saveProfileBtn =
    document.getElementById(
        "saveProfileBtn"
    );



if(saveProfileBtn){

    saveProfileBtn.addEventListener(
        "click",
        async () => {

            const payload = {

                full_name:
                    document.getElementById(
                        "fullName"
                    ).value,

                phone_number:
                    document.getElementById(
                        "phoneNumber"
                    ).value,

                delivery_address:
                    document.getElementById(
                        "deliveryAddress"
                    ).value,

                landmark:
                    document.getElementById(
                        "landmark"
                    ).value,

                city:
                    document.getElementById(
                        "city"
                    ).value,

                pincode:
                    document.getElementById(
                        "pincode"
                    ).value,

                google_maps_link:
                    document.getElementById(
                        "googleMapsLink"
                    ).value,

                preferred_payment_method:
                    document.getElementById(
                        "paymentMethod"
                    ).value

            };



            try{

                const response =
                    await fetch(
                        "/profile/save-details",
                        {

                            method:"POST",

                            headers:{
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(
                                    payload
                                )

                        }
                    );



                const data =
                    await response.json();



                if(data.success){

                    showToast(
                        data.message
                    );

                }else{

                    showToast(
                        data.message ||
                        "Unable to save profile 😭"
                    );

                }

            }catch(error){

                console.log(error);

                showToast(
                    "Server connection failed 😭"
                );

            }

        }
    );

}



