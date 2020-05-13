import React, { useState } from "react";
import GoogleLogin from "react-google-login";
import FacebookLogin from 'react-facebook-login';
import axios from "axios";
import { Redirect } from "react-router-dom";
import {Container, Row } from "react-bootstrap"; 

function responseError (response) {
  return response
}

export default function AlphabetLogin () { 
  const [redirect, setRedirect] = useState(false); // redirect holds redirect value, and setRedirect is a function to replace the redirect value

  const detectProvider = (response) => {
    if(Object.keys(response).includes("googleId")) return "google"
    if(response.graphDomain === "facebook") return "facebook"
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
          buttonText="Login with Google"
          onSuccess={handleSubmit}
          onFailure={responseError}
          cookiePolicy={"single_host_origin"}
        />
      </Row>
      <Row className="justify-content-md-center">
        <FacebookLogin
          appId={process.env.REACT_APP_FACEBOOK_APP_ID}
          fields="name,email,picture"
          callback={handleSubmit}
        />
      </Row>
    </Container>
  )

};