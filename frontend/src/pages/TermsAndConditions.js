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

const TermsAndConditions = () => {
  const [redirect, setRedirect] = useState(false)
  const history = useHistory()

  if (redirect) return <Redirect to='/' />
  return (
    <Content className='text-page' padding='var(--space-lg-200)'>
      <Container>
        <StyledLogo />
        <h1>stockbets.io Terms and Conditions</h1>
        <p>
          Thanks for your interest in stockbets! We're looking forward to having
          you on the platform. Whether you're just curious, are planning to test
          different investment strategies, or are looking to compete for real stakes, our goal
          is that your experience on stockbets is a win. Below you'll find the
          terms and conditions associated with using our platform. If you have
          any specific questions that are not answered here, please reach out to
          us at{' '}
          <a href='mailto: contact@stockbets.io'>
            contact [at] stockbets [dot] io
          </a>
        </p>
        <h2>What is stockbets.io?</h2>
        <p>
          A fully-featured virtual trading experience that allows people who are
          fascinated by markets to play fantasy-style stock trading competitions
          with each other. We also offer a single-player mode where you can test
          virtual strategies against major market indexes. If you're just here
          to learn/explore different investing strategies that's great:
          there is no requirement that users on the platform play for real
          stakes. stockbets.io is owned by {' '}
          <i>Stockbets, Inc.</i>, a Delaware C Corporation with it's registered
          agent <i>Legalinc Corporate Services </i> at {' '}
          <i>
            651 N Broad St, Suite 206, Middletown, DE 19709
          </i>
          . For all inquiries, please contact{' '}
          <a href='mailto: contact@stockbets.io'>
            contact [at] stockbets [dot] io
          </a>
          .
        </p>
        <h2>What is stockbets.io <i>not</i>?</h2>
        <p>
          <ul>
            <li>
              <b>We are not a brokerage.</b> The trades that you make on stockbets are
              virtual. We do not hold securities on your behalf and we are not
              licensed as a broker. While the trading dynamics on the platform
              are almost identical to real trading, you do not hold the
              underlying securities. Our goal is fun, social competition without
              the significant financial stakes inherent in actual investing.
            </li>
            <li>
              <b>We are not a gambling company.</b> The legal definition of gambling
              is a game that involves (1) consideration, (2) a prize, and (3)
              whose outcome is significantly determined by chance. While
              conditions (1) and (2) clearly apply to real-stakes wagers on
              stockbets, different states in the U.S.A. have developed different
              guidelines for the degree to which chance may be a determining
              factor in a game in order for it to be considered gambling. Games
              on stockbets mirror the business of professional investing and are
              therefore <i>skills-based</i>. There are 17 American states that
              allow for online sports betting based on the premise that picking
              good teams requires a significant level of sports knowledge and
              skill. Picking good investment securities requires at least the
              same degree of acumen. We operate according to sports betting law
              in seeking to comply with local regulatory requirements.
            </li>
          </ul>
        </p>
        <h2>Restrictions on real stakes betting</h2>
        <p>
          Proper regard for local regulation and adherence to good business
          ethics is a core part of who we are. If you intend to participate in
          real-stakes wagers on stockbets, you agree that you satisfy the
          following conditions:
          <ul>
            <li>You are at least 18 years of age</li>
            <li>
              If you are a resident of the U.S.A., you currently reside in one
              of the following 17 states where sports betting is legal:
              <ul>
                <li>Arkansas</li>
                <li>Colorado</li>
                <li>Delaware</li>
                <li>Delaware</li>
                <li>Illinois</li>
                <li>Iowa</li>
                <li>Nevada</li>
                <li>New Hampshire</li>
                <li>New Jersey</li>
                <li>New York</li>
                <li>Michigan</li>
                <li>Mississippi</li>
                <li>Montana</li>
                <li>Oregon</li>
                <li>Pennsylvania</li>
                <li>Rhode Island</li>
                <li>West Virginia</li>
              </ul>
            </li>
          </ul>
          <li>
            If you are not an American resident, online sports betting is legal
            in the jurisdiction where you live.
          </li>
          <li>
            You understand that stakes involving real money can be financially
            consequential. You will not engage with stockbets.io as a principal
            income source, or engage in betting that puts your financial well
            being at risk.
          </li>
        </p>
        <h2>Terms</h2>
        <p>
            Real-stakes games are non-refundable and you cannot cancel your
            participation in a real-stakes game once it has begun.
        </p>
        <p>
            stockbets.io is still in product beta, and we still occasionally
            find ways to improve how the platform calculates winners of games
            based on their portfolio performance. Our data feed is
            presently nearly--but not entirely--real-time, meaning that orders
            may clear at prices that do not identically match the market. The
            platform has logic to handle stock splits, reverse splits, and
            dividend payments, but it is possible that this logic will be
            imperfectly applied in a way that has a material impact on game
            outcomes. If you believe this has happened in your case please
            contact us at {' '}
          <a href='mailto: contact@stockbets.io'>
              contact [at] stockbets [dot] io
          </a> for resolution.
            Notwithstanding, if you participate in a real-stakes game
            you acknowledge that you are aware that these risks have the
            potential to influence game outcomes, and release Stockbets, Inc. from
            all related legal and financial claims.
        </p>
        <h2>Regarding financial advice and investment in actual securities</h2>
        <p>
          stockbets.io does not seek to provide you with investment advice. No
          portfolio, trade, or performance result, or interaction with any other
          user either on or off the platform should be construed as investment
          advice from Stockbets, Inc. to you. Furthermore, you acknowledge that
          participating in the buying and selling of actual securities is an
          activity that involves the risk of loss, and release Stockbets, Inc.,
          from all potential claims related to investments in actual securities.
        </p>
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

export { TermsAndConditions }
