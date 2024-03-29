import React, { useState } from 'react'
import { Link, Redirect } from 'react-router-dom'
import GoogleLogin from 'react-google-login'
import FacebookLogin from 'react-facebook-login/dist/facebook-login-render-props'
import api from 'services/api'

import { Container, Row, Col, Form, Button } from 'react-bootstrap'
import { Content } from 'components/layout/Layout'
import { ReactComponent as Logo } from 'assets/logo.svg'
import { Subtext, SmallText, AlignText } from 'components/textComponents/Text'
import styled from 'styled-components'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faGoogle, faFacebook } from '@fortawesome/free-brands-svg-icons'
import { breakpoints } from 'design-tokens'
import { TabbedRadioButtons } from 'components/forms/Inputs'

const RightCol = styled(Col)`
  padding: 0vw 8vw 8vw;
  min-height: 50vh;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  text-align: center;

  &::before {
    background: var(--color-secondary);
    border-radius: 50% 50% 0 60%/ 50% 50% 0 50%;
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
    top: 35vh;
    left: -25vw;
    width: 100vh;
    z-index: -1;
  }

  @media screen and (min-width: ${breakpoints.md}){
    text-align: left;
    padding: 0 8vw;
    justify-content: flex-start;

    br{
      display: none;
    }
    &::before {
      position: fixed;
      width: 100vw;
      height: 200vh;
      bottom: 20vh;
      top: auto;
      left: 50vw;
    }
    &::after {
      position: fixed;
      width: 100vw;
      height: 100vh;
      left: 60vw;
      top: 40vh;
      z-index: -2;
    }
  }
  @media screen and (max-width: ${breakpoints.md}){
    height: auto;
    padding: 0;
  }
`

const LeftCol = styled(Col)`
  display: flex;
  min-height: 0vh;
  flex-wrap: wrap;
  align-items: center;
  @media screen and (max-width: ${breakpoints.md}){
    height: 18vh;
  }
`

const LoginButton = styled.button`
  background-color: transparent;
  font-family: "proxima-nova", Avenir, sans-serif !important;
  color: var(--color-text-primary) !important;
  text-transform: uppercase;
  font-size: var(--font-size-normal);
  font-weight: bold;
  border: none;
  padding: 0 var(--space-100) var(--space-100) 0;
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
  @media screen and (max-width: ${breakpoints.md}){
    width: 70vw;
    max-width: 300px;
  }
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

const FooterLinks = styled.div`
  width: 100%;
  margin-top: 2rem;
  line-height: 1.2;
  position: static;
  text-align: center;
  a{
    color: inherit;
    font-weight: bold;
  }
  @media screen and (min-width: ${breakpoints.md}){
    width: 80%;
    bottom: 1.5vh;
    text-align: right;
    position: absolute;
    right: 2vw;
    br{
      display: none;
    }
  }
`

const LoginDialog = styled.div`
  background-color: rgba(255, 255, 255, 1);
  width: 100vw;
  max-width: 350px;
  border-radius: var(--space-100);
  box-shadow: var(--shadow-area);
  form small {
    margin-top: var(--space-300);
    margin-bottom: var(--space-400);
  }
`
const LoginDialogContent = styled.div`
  padding: var(--space-400);
  padding-bottom: var(--space-500);
`
const LoginDialogHeader = styled.div`
  .form-check{
    text-align: left;
    label{
      height: var(--space-900);
    }
  }
`

const LoginDialogAuths = styled.div``

function responseError (response) {
  return response
}

export default function Login () {
  const [redirect, setRedirect] = useState(false)
  const [loginEmail, setLoginEmail] = useState(null)
  const [loginPassword, setLoginPassword] = useState(null)
  const [loginSelection, setLoginSelection] = useState('logIn')

  const detectProvider = (response) => {
    if (Object.keys(response).includes('googleId')) return 'google'
    if (response.graphDomain === 'facebook') return 'facebook'
  }

  const handleLoginError = (error) => {
    if (error.response.status === 403) {
      window && window.alert(error.response.data)
    } else {
      window.alert("Something seems to have gone terribly wrong. We apologize for that! Please send us an email at contact@stockbets.io and we'll sort it out right away.")
    }
  }

  const handleOAuthSubmit = async (response) => {
    const provider = detectProvider(response)
    const responseCopy = { ...response }
    responseCopy.provider = provider
    responseCopy.is_sign_up = loginSelection === 'signUp'
    try {
      await api
        .post('/api/login', responseCopy)
        .then((r) => console.log({ r }) || setRedirect(true))
    } catch (error) {
      handleLoginError(error)
    }
  }

  const handleUserPasswordSubmit = async (e) => {
    e.preventDefault()
    try {
      await api
        .post('/api/login', { provider: 'stockbets', email: loginEmail, password: loginPassword, is_sign_up: loginSelection === 'signUp' })
        .then((r) => console.log({ r }) || setRedirect(true))
    } catch (error) {
      handleLoginError(error)
    }
  }

  if (redirect) return <Redirect to='/' />
  return (
    <Content minHeight='100vh' alignItems='center' display='flex'>
      <Container fluid style={{ maxWidth: '1400px' }}>
        <Row>
          <LeftCol md={6}>
            <LeftColContent>
              <StyledLogo />
            </LeftColContent>
          </LeftCol>
          <RightCol md={6}>
            <LoginDialog>
              <LoginDialogHeader>
                <TabbedRadioButtons
                  defaultChecked={loginSelection}
                  onClick={(e) => {
                    setLoginSelection(e.target.value)
                  }}
                  colorTab='var(--color-light-gray)'
                  optionsList={{
                    logIn: 'Log In',
                    signUp: 'Sign Up'
                  }}
                />
              </LoginDialogHeader>
              <LoginDialogContent>
                <LoginDialogAuths>
                  <GoogleLogin
                    clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}
                    buttonText='Login with Google'
                    onSuccess={handleOAuthSubmit}
                    onFailure={responseError}
                    cookiePolicy='single_host_origin'
                    render={(renderProps) => (
                      <LoginButton onClick={renderProps.onClick}>
                        <StyledFaIcon
                          icon={faGoogle}
                          color='var(--color-primary)'
                        />{' '}
                        <span>
                          {loginSelection === 'signUp'
                            ? 'Sign up with Google'
                            : 'Login with Google'}
                        </span>
                      </LoginButton>
                    )}
                  />
                  <FacebookLogin
                    appId={process.env.REACT_APP_FACEBOOK_APP_ID}
                    disableMobileRedirect
                    fields='name,email,picture'
                    callback={handleOAuthSubmit}
                    render={(renderProps) => (
                      <LoginButton onClick={renderProps.onClick}>
                        <StyledFaIcon
                          icon={faFacebook}
                          color='var(--color-primary)'
                        />{' '}
                        <span>
                          {loginSelection === 'signUp'
                            ? 'Sign up with Facebook'
                            : 'Login with Facebook'}
                        </span>
                      </LoginButton>
                    )}
                  />
                </LoginDialogAuths>
                <Form
                  onSubmit={handleUserPasswordSubmit}
                >
                  <Subtext>
                    {loginSelection === 'signUp'
                      ? 'Or create an account with an email an password'
                      : 'Or login with your email and password'}
                  </Subtext>
                  <Form.Group>
                    <Form.Label>
                      Email
                    </Form.Label>
                    <Form.Control
                      type='email'
                      placeholder='Your email'
                      onChange={(e) => setLoginEmail(e.target.value)}
                    />
                  </Form.Group>
                  <Form.Group>
                    <Form.Label>
                      Password
                    </Form.Label>
                    <Form.Control
                      type='password'
                      placeholder={loginSelection === 'signUp'
                        ? 'Pick a strong password ;)'
                        : 'Your password'}
                      onChange={(e) => setLoginPassword(e.target.value)}
                    />
                  </Form.Group>
                  <AlignText align='center'>
                    <Button type='submit'>
                      {loginSelection === 'signUp'
                        ? 'Create account'
                        : 'Enter stockbets'}
                    </Button>
                  </AlignText>
                </Form>
              </LoginDialogContent>
            </LoginDialog>
          </RightCol>
        </Row>
      </Container>
      <FooterLinks>
        <SmallText color='var(--color-secondary)'>
          Have a look at our
          <Link to='/terms' target='_blank'> terms and conditions </Link>
          <br />
          and <Link to='/privacy' target='_blank'> privacy policy </Link> before getting started.
        </SmallText>
      </FooterLinks>
    </Content>
  )
}
