function validateRegForm(e) {
    e.preventDefault();

    let username = document.getElementById("username").value;
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;
    let password2 = document.getElementById("password2").value;

    // validate username
    if (!/^[a-zA-Z0-9_]*$/.test(username)) {
        alert("Username can only contain letters, numbers, and underscores");
        return;
    }
    if (username.length < 8 || username.length > 20) {
        alert("Username must be between 8 and 20 characters long");
        return;
    }

    // validate email
    if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$/.test(email)) {
        alert("Please enter a valid email address");
        return;
    }

    // validate password
    if (!/^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,20}$/.test(password)) {
        alert("Password must be 8-20 characters long and contain letters and numbers");
        return;
    }

    // validate password confirmation
    if (password !== password2) {
        alert("Passwords do not match");
        return;
    }

    // hash password
    let hashedPassword = CryptoJS.SHA256(password);
    document.getElementById("password").value = hashedPassword;
    document.getElementById("password2").value = hashedPassword;

    document.getElementById("registration-form").submit()
}

// add event listener to the form's submit buttons
document.getElementById("registration-submittion").addEventListener("click", validateRegForm);