import React, { useState } from "react";
import GoogleLogin from "react-google-login";
import axios from "axios";
import { Redirect } from "react-router-dom";
import Cookie from "js-cookie";

function responseError (response) {
  return (
    <div>
      <h1>Google login failed. Here's the response that you got back:</h1>
      <p>{ response }</p>
    </div>
  )
}

export default function AlphabetLogin () { 

  const [redirect, setRedirect] = useState(false); // redirect holds redirect value, and setRedirect is a function to replace the redirect value

  function handleSubmit (response) {
    axios.post("/register", response).then(
      api_response => Cookie.set("session_token", api_response.data.session_token)
    ).then(() => setRedirect(true));
  }

  if (redirect) { 
    return(
      <Redirect to="/" />
    )
  }

  return (
    <div className="App">
      <GoogleLogin
        clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}
        buttonText="Login with your gmail acccount"
        onSuccess={handleSubmit}
        onFailure={responseError}
        cookiePolicy={"single_host_origin"}
      />
    </div>
  )

};