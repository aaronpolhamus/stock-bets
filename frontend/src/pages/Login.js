import React, { useState } from "react";
import GoogleLogin from "react-google-login";
import axios from "axios";
import { Redirect } from "react-router-dom";

function responseError (response) {
  return response
}

export default function AlphabetLogin () { 
  const [redirect, setRedirect] = useState(false); // redirect holds redirect value, and setRedirect is a function to replace the redirect value

  function handleGoogleSubmit (response) {
    let responseCopy = {...response}
    responseCopy["provider"] = "google"
    axios.post("/api/login", responseCopy).then(() => setRedirect(true));
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
        onSuccess={handleGoogleSubmit}
        onFailure={responseError}
        cookiePolicy={"single_host_origin"}
      />
    </div>
  )

};