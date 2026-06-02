console.log("RM Bakes Loaded Successfully");


// =========================
// TOGGLE PASSWORD
// =========================
function togglePassword() {

    const passwordInput = document.getElementById("password");

    if (passwordInput.type === "password") {

        passwordInput.type = "text";

    } else {

        passwordInput.type = "password";
    }
}

// =========================
// CONFIRM LOGOUT
// =========================
function confirmLogout() {

    const logoutConfirm = confirm(
        "Are you sure you want to logout?"
    );

    if (logoutConfirm) {

        window.location.href = "/logout";
    }
}