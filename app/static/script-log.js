function validateLogForm(e) {
    e.preventDefault();

    let username = document.getElementById("login").value;
    let password = document.getElementById("password").value;

    // validate username
    if (!/^[a-zA-Z0-9_]*$/.test(username)) {
        alert("Username can only contain letters, numbers, and underscores");
        return;
    }
    if (username.length < 8 || username.length > 20) {
        alert("Username must be between 8 and 20 characters long");
        return;
    }

    // validate password
    if (!/^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,20}$/.test(password)) {
        alert("Password must be 8-20 characters long and contain letters and numbers");
        return;
    }

    console.log("yeah i am here")
    // hash password
    let hashedPassword = CryptoJS.SHA256(password);
    document.getElementById("password").value = hashedPassword;
    document.getElementById("login-form").submit()
}

// add event listener to the form's submit buttons
document.getElementById("login-submittion").addEventListener("click", validateLogForm);