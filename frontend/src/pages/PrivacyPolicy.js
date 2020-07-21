import React, { useState } from 'react'
import { Redirect, useHistory } from 'react-router-dom'
import { Button, Container } from 'react-bootstrap'
import { ReactComponent as Logo } from 'assets/logo.svg'
import { Content } from 'components/layout/Layout'
import styled from 'styled-components'

const StyledLogo = styled(Logo)`
  max-width: 300px;
  width: 90%;
  margin-bottom: 2rem;
`

const PrivacyPolicy = () => {
  const [redirect, setRedirect] = useState(false)
  const history = useHistory()

  if (redirect) return <Redirect to='/' />
  return (
    <Content className='text-page' padding='var(--space-lg-200)'>
      <Container>
        <StyledLogo />
        <h1>stockbets.io privacy policy</h1>
        <p>
          This policy explains what information we collect when you use
          stockbets.io It also has information about how we store, use,
          transfer, and delete that information. We don't just want to comply
          with minimum legal privacy requirements, but to earn your trust.
        </p>
        <h2>What is stockbets.io?</h2>
        <p>
          A fully-featured virtual trading experience that allows people who are
          fascinated by markets to play fantasy-style stock trading competitions
          with each other. We hope that you love it. stockbets.io is currently
          an exploratory project beta produced and owned by{' '}
          <i>Pisces Ventures LLC</i>, a Delaware company in good standing with
          its registered agent as{' '}
          <i>
            Northwest Registered Agent Service, Inc., 8 The Green, Ste B, Dover,
            DE 19901
          </i>
          . For all inquiries, please contact{' '}
          <a href='mailto: contact@stockbets.io'>
            contact [at] stockbets [dot] io
          </a>
          . If/when we formalize the project further, we will register the
          stockbets as a separate legal entity and update this policy
          accordingly.
        </p>

        <h2>What information does stockbets.io collect and store?</h2>
        <p>
          One of the main reasons that stockbets.io strictly uses logins from
          major online platforms--as opposed to more standard usernames and
          passwords--is that we value your privacy and security, and want to
          make sure that you are in complete control of your account access and
          data. When you login we only request basic profile information from
          your authentication provider (Google, Facebook, or Twitter). This lets
          us know that you are who you say are, and that you do indeed control
          the account that you're using to login. When you create your account,
          we save the following information about you:
          <ul>
            <li>Your name</li>
            <li>Your email address</li>
            <li>Your profile picture</li>
            <li>Your unique resource ID </li>
          </ul>
          That's it. We don't gain ongoing access to your account, and have no
          ability to produce or distribute content on your behalf, or gain any
          other form of control or access to your account of personal data.
        </p>

        <h2>What we do with your personal data once we have it?</h2>
        <p>
          We use your data for account authentication, and, in the case of your
          profile picture, to create an avatar for you that identifies you to
          friends / to the community when you create or receive friend
          invitations. We will also, occasionally, use your email for critical
          communications related to changes on the platform, including:
          <ul>
            <li>Updates to this agreement</li>
            <li>Updated to stockbets.io as a legal entity</li>
            <li>
              Any other relevant privacy or terms-of-use related changes that
              you should know about
            </li>
          </ul>
          Here's a list of things that we will never do with your personal data:
          <ul>
            <li>
              Share it with any third party for any purpose whatsoever without
              your explicit and informed consent
            </li>
            <li>Spam you with annoying content that clutters your inbox</li>
            <li>
              Share it with other users on the platform without your consent and
              approval. Specifically, unless someone is your friend, the only
              thing they can know about you is your username and avatar.{' '}
            </li>
          </ul>
        </p>

        <h2>
          What we do with the information that you generate on the platform?
        </h2>
        <p>
          stockbets.io's goal is to provide a fun, low-stakes, virtual platform
          for playing competitive stock trading games with your friends. As you
          do this, you'll create data about virtual orders, balances, and
          portfolio performance. When you're in a game, your fellow game
          participants will be able to see your game-specific perfomance,
          balances, and portfolio statistics. Everyone that you are friends with
          will see your "overall" statistics, but won't be able to see the games
          that you are in unless they're also playing that game with you. We
          apply the same privacy policy to this virtual trading and performance
          data that we apply to handling your personal information.
        </p>

        <h2>
          I created an account, and now I want to delete it along with my
          personal data and virtual trading data. How do I do that?
        </h2>
        <p>
          We'll deliver an account removal feature as we grow the platform. For
          now we'll help you out with that by hand. Please email{' '}
          <a href='mailto: contact@stockbets.io'>
            contact [at] stockbets [dot] io
          </a>{' '}
          for assistance.
        </p>

        <h2>Data storage</h2>
        <p>
          stockbets.io uses Amazon Web Services (AWS) for all third-party data
          storage and hosting. We maintain two types of logs: server logs and
          event logs. By using the site you authorize us to transfer, store, and
          use your information for the purposes elaborated here in the United
          States and any other country where we operate.
        </p>

        <h2>Tracking, cookies, and data security</h2>
        <p>
          When you login we set an HTTP-only web token that encrypts the basic
          profile information that we describe above. That's the only browser
          session information that we store. This information is not available
          to javascript applications running on your browser, and even if it
          was, would be un-readable without our server-side secret encryption
          key. We are PCI-compliant and implement a CORS policy that validates
          that origin of all requests sent to the stockbets API, protecting you
          from cross-site third party attacks. We have your personal data and
          session access on lock.
        </p>
        <hr />
        <p className='text-right'>
          <Button variant='outline-secondary' onClick={() => history.go(-2)}>
            Thanks but no, thanks.
          </Button>
          <Button variant='primary' onClick={() => setRedirect(true)}>
            Sounds great, let's go!
          </Button>
        </p>
      </Container>
    </Content>
  )
}

export { PrivacyPolicy }
