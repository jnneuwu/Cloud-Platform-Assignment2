/*
Replace this file with the exact firebase-login.js from your course example.

This starter expects the final script to:
1. Authenticate the user with Firebase Authentication.
2. Get the Firebase ID token from the signed-in user.
3. POST JSON to /auth/login in the form:
   { "idToken": "<firebase-id-token>" }
4. Redirect the browser to response.redirect_url when the server responds with { ok: true }.
*/

const loginButton = document.querySelector("[data-login]");

if (loginButton) {
    loginButton.addEventListener("click", () => {
        window.alert(
            "Replace static/js/firebase-login.js with the exact course example before testing login."
        );
    });
}
