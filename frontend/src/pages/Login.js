import React, { useState } from "react";
import GoogleLogin from "react-google-login";
import FacebookLogin from "react-facebook-login/dist/facebook-login-render-props";
import axios from "axios";
import { Redirect } from "react-router-dom";
import { Container, Row, Col } from "react-bootstrap";
import { Content } from "components/layout/Layout";
import { ReactComponent as Logo } from "assets/logo.svg";
import styled from "styled-components";

const RightCol = styled(Col)`
  &::before {
    content: "";
    display: block;
    width: 150vh;
    height: 120vh;
    background: var(--color-secondary);
    position: fixed;
    bottom: 2vh;
    left: 50vw;
    border-radius: 50% 50% / 45% 50%;
    z-index: -1;
  }
  &::after {
    content: "";
    display: block;
    width: 100vh;
    height: 100vh;
    background: var(--color-primary);
    position: fixed;
    top: 50vh;
    left: 60vw;
    border-radius: 50% 50% / 45% 50%;
    z-index: -2;
  }
`;

const LoginButton = styled.button`
  background-color: transparent;
  font-family: "proxima-nova", Avenir, sans-serif !important;
  color: var(--color-light-gray) !important;
  text-transform: uppercase;
  font-size: var(--font-size-normal);
  font-weight: bold;
  border: none;
  padding: var(--space-100);
`;

const StyledLogo = styled(Logo)`
  max-width: 460px;
  width: 90%;
`;

function responseError(response) {
  return response;
}

export default function AlphabetLogin() {
  const [redirect, setRedirect] = useState(false);

  const detectProvider = (response) => {
    if (Object.keys(response).includes("googleId")) return "google";
    if (response.graphDomain === "facebook") return "facebook";
  };

  function handleSubmit(response) {
    const provider = detectProvider(response);
    let responseCopy = { ...response };
    responseCopy["provider"] = provider;
    axios.post("/api/login", responseCopy).then(() => setRedirect(true));
  }

  if (redirect) {
    return <Redirect to="/" />;
  }

  return (
    <Content height="100vh" alignItems="center" display="flex">
      <Container fluid>
        <Row noGutters sm={2}>
          <Col>
            <StyledLogo />
          </Col>
          <RightCol>
            <Row className="justify-content-md-center">
              <GoogleLogin
                clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}
                buttonText="Login with Google"
                onSuccess={handleSubmit}
                onFailure={responseError}
                cookiePolicy={"single_host_origin"}
                render={(renderProps) => (
                  <LoginButton
                    onClick={renderProps.onClick}
                    disabled={renderProps.disabled}
                  >
                    Login with Google
                  </LoginButton>
                )}
              />
            </Row>
            <Row className="justify-content-md-center">
              <FacebookLogin
                appId={process.env.REACT_APP_FACEBOOK_APP_ID}
                fields="name,email,picture"
                callback={handleSubmit}
                render={(renderProps) => (
                  <LoginButton onClick={renderProps.onClick}>
                    Login with Facebook
                  </LoginButton>
                )}
              />
            </Row>
          </RightCol>
        </Row>
      </Container>
    </Content>
  );
}
