import React from "react";
import ReactDOM from "react-dom";
import GoogleLogin from "react-google-login";

export default function App() {
    <GoogleLogin
        clientId="658977310896-knrl3gka66fldh83dao2rhgbblmd4un9.apps.googleusercontent.com"
        buttonText="Login"
        onSuccess={responseGoogle}
        onFailure={responseGoogle}
        cookiePolicy={'single_host_origin'}
    />
}

// f"<p>Hello, {current_user.name}! You're logged in! Email: {current_user.email}</p>"
// "<div><p>Google Profile Picture:</p>"
// f"<img src='{current_user.profile_pic}' alt='Google profile pic'></img></div>"
// "<a class='button' href='/logout'>Logout</a>"
