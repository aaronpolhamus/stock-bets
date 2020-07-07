import React, { useState } from 'react'
import { Link, Redirect } from 'react-router-dom'
import GoogleLogin from 'react-google-login'
import FacebookLogin from 'react-facebook-login/dist/facebook-login-render-props'
import api from 'services/api'

import { Container, Row } from 'react-bootstrap'
import { Content } from 'components/layout/Layout'
import { ReactComponent as Logo } from 'assets/logo.svg'
import { SmallText } from 'components/textComponents/Text'
import styled from 'styled-components'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faGoogle, faFacebook } from '@fortawesome/free-brands-svg-icons'

const RightCol = styled.div`
  padding: 8vw;
  &::before {
    content: "";
    display: block;
    width: 150vh;
    height: 120vh;
    background: var(--color-secondary);
    position: fixed;
    bottom: 6vh;
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
  a {
    position: fixed;
    bottom: 2vh;
    right: 2vw;
  }
`

const LeftCol = styled.div`
  display: flex;
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
  width: 90%;
`

const StyledFaIcon = styled(FontAwesomeIcon)`
  position: relative;
  top: 1px;
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
        <Row noGutters sm={2}>
          <LeftCol>
            <StyledLogo />
          </LeftCol>
          <RightCol>
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
            </p>
            <p>
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
