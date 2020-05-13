import React, { useState } from "react";
import GoogleLogin from "react-google-login";
import axios from "axios";
import { Redirect } from "react-router-dom";
import {Container, Row } from "react-bootstrap"; 

function responseError (response) {
  console.log(response)
  return response
}

export default function AlphabetLogin () { 
  const [redirect, setRedirect] = useState(false); // redirect holds redirect value, and setRedirect is a function to replace the redirect value

  const detectProvider = (response) => {
    if(Object.keys(response).includes("googleId")) return "google"
  }

  function handleSubmit (response) {
    const provider = detectProvider(response)
    let responseCopy = {...response}
    responseCopy["provider"] = provider
    axios.post("/api/login", responseCopy).then(() => setRedirect(true));
  }

  if (redirect) { 
    return(
      <Redirect to="/" />
    )
  }

  return (
    <Container fluid="md">
      <Row className="justify-content-md-center">
        <GoogleLogin
          clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}
          buttonText="Login with your gmail acccount"
          onSuccess={handleSubmit}
          onFailure={responseError}
          cookiePolicy={"single_host_origin"}
        />
      </Row>
    </Container>
  )

};