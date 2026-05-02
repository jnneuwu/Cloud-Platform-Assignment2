'use strict'

// import firebase
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.9.0/firebase-app.js"
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/12.9.0/firebase-auth.js"

// your web app's firebase configuration
// REPLACE the values below with the firebaseConfig from your Firebase project
// (Project settings > General > Your apps > Web app > Use a <script> tag).
// Do not modify any other part of this file. The assignment brief requires
// firebase-login.js to match the example exactly except for this object.
const firebaseConfig = {
    apiKey: "AIzaSyDNYbRO8DWwpIi-eCeBZSjs-SWGUFlKIYw",
    authDomain: "cp-assignment2.firebaseapp.com",
    projectId: "cp-assignment2",
    storageBucket: "cp-assignment2.firebasestorage.app",
    messagingSenderId: "355373000310",
    appId: "1:355373000310:web:67fd94523965d0d9eee157"
}

window.addEventListener("load", function () {
    const app = initializeApp(firebaseConfig)
    const auth = getAuth()
    updateUI(document.cookie)
    console.log("hello world load")

    // signup of a new user to firebase
    document.getElementById("sign-up").addEventListener('click', function () {
        const email = document.getElementById("email").value
        const password = document.getElementById("password").value

        createUserWithEmailAndPassword(auth, email, password)
            .then((userCredential) => {
                // we have created a user
                const user = userCredential.user

                // get the id token for the user who just logged in and force a redirect to /
                user.getIdToken().then((token) => {
                    document.cookie = "token=" + token + ";path=/;SameSite=Strict"
                    window.location = "/"
                })
            })
            .catch((error) => {
                // issue for signup that we will drop to console
                console.log(error.code + error.message)
            })
    })

    // login of a user to firebase
    document.getElementById("login").addEventListener('click', function () {
        const email = document.getElementById("email").value
        const password = document.getElementById("password").value

        signInWithEmailAndPassword(auth, email, password)
            .then((userCredential) => {
                // we have a signed in user
                const user = userCredential.user
                console.log("logged in")

                // get the id token for the user who just logged in and force a redirect to /
                user.getIdToken().then((token) => {
                    document.cookie = "token=" + token + ";path=/;SameSite=Strict"
                    window.location = "/"
                })
            })
            .catch((error) => {
                // issue with signup that we will drop to console
                console.log(error.code + error.message)
            })
    })

    // signout from firebase
    document.getElementById("sign-out").addEventListener('click', function () {
        signOut(auth)
            .then((output) => {
                // remove the ID token for the user and force a redirect to /
                document.cookie = "token=;path=/;SameSite=Strict"
                window.location = "/"
            })
    })
})

// function that will update the UI for the user depending on if they are logged in or not by checking the passed in cookie
// that contains the token
function updateUI(cookie) {
    var token = parseCookieToken(cookie)

    // if a user is logged in then disable the email, password, signup, and login UI elements and show the signout button and vice versa
    if (token.length > 0) {
        document.getElementById("login-box").hidden = true
        document.getElementById("sign-out").hidden = false
    } else {
        document.getElementById("login-box").hidden = false
        document.getElementById("sign-out").hidden = true
    }
}

// function that will take the cookie and will return the value associated with it to the caller
function parseCookieToken(cookie) {
    // split the cookie out on the basis of the semi-colon
    var strings = cookie.split(';')

    // go through each of the strings
    for (let i = 0; i < strings.length; i++) {
        // split the string based on the = sign. if the LHS is token then return the RHS immediately
        var temp = strings[i].split('=')
        if (temp[0].trim() == "token")
            return temp[1]
    }

    // if we get to this point then the token wasn't in the cookie so return the empty string
    return ""
}
