import React, { useState } from 'react'
import { Link, Redirect } from 'react-router-dom'
import GoogleLogin from 'react-google-login'
import FacebookLogin from 'react-facebook-login/dist/facebook-login-render-props'
import api from 'services/api'

import { Container, Row, Col } from 'react-bootstrap'
import { Content } from 'components/layout/Layout'
import { ReactComponent as Logo } from 'assets/logo.svg'
import { SmallText } from 'components/textComponents/Text'
import styled from 'styled-components'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faGoogle, faFacebook } from '@fortawesome/free-brands-svg-icons'
import { breakpoints } from 'components/layout/Breakpoints'

const RightCol = styled(Col)`
  padding: 8vw;
  height: 50vh;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  text-align: center;

  &::before {
    background: var(--color-secondary);
    border-radius: 50% 50% / 45% 50%;
    content: "";
    display: block;
    height: 120vh;
    position: absolute;
    top: 0;
    width: 150vh;
    z-index: -1;

  }
  &::after {
    background: var(--color-primary);
    border-radius: 50% 50% / 45% 50%;
    content: "";
    display: block;
    height: 100vh;
    position: absolute;
    top: 70%;
    left: -15vw;
    width: 100vh;
    z-index: -1;
  }
  a {
    position: fixed;
    bottom: 2vh;
    right: 2vw;
  }
  @media screen and (min-width: ${breakpoints.md}){
    text-align: left;
    &::before {
      position: fixed;
      top: auto;
      bottom: 6vh;
      left: 50vw;
    }
    &::after {
      position: fixed;
      left: 60vw;
      top: 50vh;
      z-index: -2
    }
  }

`

const LeftCol = styled(Col)`
  display: flex;
  height: 50vh;
  flex-wrap: wrap;
  align-items: center;
`

const LoginButton = styled.button`
  background-color: transparent;
  font-family: "proxima-nova", Avenir, sans-serif !important;
  color: var(--color-light-gray) !important;
  text-transform: uppercase;
  font-size: var(--font-size-normal);
  font-weight: bold;
  border: none;
  padding: var(--space-100);
  span {
    position: relative;
    transition: all 0.2s;
    left: 0px;
  }
  &:hover span {
    left: var(--space-50);
  }
`

const StyledLogo = styled(Logo)`
  max-width: 460px;
  width: 100%;
`

const StyledFaIcon = styled(FontAwesomeIcon)`
  position: relative;
  top: 1px;
`

const LeftColContent = styled.div`
  width: 100%;
  text-align: center;
  p {
    color: var(--color-text-gray)
  }
  @media screen and (min-width: ${breakpoints.md}){
    text-align: left;
    p{
      margin-top: var(--space-200);
      font-size: var(--font-size-large)
    }
  }
`

function responseError (response) {
  return response
}

export default function AlphabetLogin () {
  const [redirect, setRedirect] = useState(false)

  const detectProvider = (response) => {
    if (Object.keys(response).includes('googleId')) return 'google'
    if (response.graphDomain === 'facebook') return 'facebook'
  }

  const handleSubmit = async (response) => {
    const provider = detectProvider(response)
    const responseCopy = { ...response }
    responseCopy.provider = provider
    try {
      await api
        .post('/api/login', responseCopy)
        .then((r) => console.log({ r }) || setRedirect(true))
    } catch (error) {
      window && window.alert(
        "stockbets is in super-early beta, and we're whitelisting it for now. We'll open to everyone at the end of June, but email contact@stockbets.io for access before that :)"
      )
    }
  }

  if (redirect) return <Redirect to='/' />
  return (
    <Content height='100vh' alignItems='center' display='flex'>
      <Container fluid>
        <Row>
          <LeftCol md={6}>
            <LeftColContent>
              <StyledLogo />
              <p>
                <span>Trade as a pro, </span>
                <em>
                  just for fun.
                </em>
              </p>
            </LeftColContent>
          </LeftCol>
          <RightCol md={6}>
            <p>
              <GoogleLogin
                clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}
                buttonText='Login with Google'
                onSuccess={handleSubmit}
                onFailure={responseError}
                cookiePolicy='single_host_origin'
                render={(renderProps) => (
                  <LoginButton onClick={renderProps.onClick}>
                    <StyledFaIcon
                      icon={faGoogle}
                      color='var(--color-primary)'
                    />{' '}
                    <span>Login with Google</span>
                  </LoginButton>
                )}
              />
              <FacebookLogin
                appId={process.env.REACT_APP_FACEBOOK_APP_ID}
                disableMobileRedirect
                fields='name,email,picture'
                callback={handleSubmit}
                render={(renderProps) => (
                  <LoginButton onClick={renderProps.onClick}>
                    <StyledFaIcon
                      icon={faFacebook}
                      color='var(--color-primary)'
                    />{' '}
                    <span>Login with Facebook</span>
                  </LoginButton>
                )}
              />
            </p>
            <Link to='/privacy'>
              <SmallText color='var(--color-secondary)'>
                Have a look at our
                <strong> privacy policy </strong>before getting started.
              </SmallText>
            </Link>
          </RightCol>
        </Row>
      </Container>
    </Content>
  )
}
