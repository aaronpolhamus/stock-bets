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
        <p>
          Furthermore, stockbets.io is proceeding with appropriate regard for any
          potentially applicable SEC regulation (see below). We do not
          believe that real stakes games on stockbets.io run afoul of regulations
          passed to protect retail investors in the wake of the Dodd-Frank Wall
          Street Reform and Consumer protection act, or any other applicable SEC
          law. Notwithstanding, we will not be directly facilitating real
          payments between participants or taking commissions from games until
          we conducted further due diligence and, likely, directly engaged with
          SEC regulators. Accordingly, if you participate in a real-stakes game
          among friends on stockbets.io, you acknowledge that this game is <i>honor system only</i>,
          and release Stockbets, Inc. from all responsibility associated with
          the settling of claims among participants.
        </p>
        <h2>Terms</h2>
        <h3>Game play and determining winners</h3>
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
        <h3>Regarding financial advice and investment in actual securities</h3>
        <p>
          stockbets.io does not seek to provide you with investment advice. No
          portfolio, trade, or performance result, or interaction with any other
          user either on or off the platform should be construed as investment
          advice from Stockbets, Inc. to you. Furthermore, you acknowledge that
          participating in the buying and selling of actual securities is an
          activity that involves the risk of loss, and release Stockbets, Inc.,
          from all potential claims related to investments in actual securities.
        </p>
        <h3>Regarding the standing of stockbets.io vis-a-vis SEC regulation of security-based swaps</h3>
        <p>
          The SEC has undertaken multiple cease and desist actions against
          companies that have run fantasy-style betting competitions related to
          the value of securities, arguing that these violate regulations of
          retail investor participation in <i>security-based swaps</i>.
          See {' '}
          <a href='https://www.sec.gov/litigation/admin/2015/33-9809.pdf'>
            Sand Hill Exchange
          </a>
          {' '} and {' '}
          <a href='https://www.sec.gov/litigation/admin/2016/33-10232.pdf'>
            Forcerank LLC
          </a> for examples. We do not believe that winnings on stockbets.io constitute
          security-based swaps according to the logic laid out in these cases.
          The reason for this is that the principal determinant stockbets.io
          payouts is based on the <i>relative skill</i> of each investor in a
          game, rather than on the movement of a specific security, basked of
          securities, or index. For example, in the case of Forecerank LLC, the
          SEC found that
          <i>
            "Forcerank LLC’s agreements with players were security-
            based swaps because they provided for a payment that was dependent on
            the occurrence, or the extent of the occurrence, of an event or
            contingency that was “associated with” a potential financial,
            economic, or commercial consequence <b>and</b> because they were “based on”
            the value of individual securities."
          </i> (emphasis added by Stockbets, Inc)
          We believe that the emphasis on valuing individual securities, in both
          of the cases mentioned above, distinguishes competitions of investment
          skill on stockbets.io from the sort of targeted valuation of securities
          that the SEC found to be in violation of security-based swap regulations.
        </p>
        <p>
          We hope that the SEC takes the same view. In the meantime, we will not
          be facilitating cash transfers between participants while we conduct
          further due diligence. Good citizenship and proper regard for applicable laws
          is as important to us as it is to you. If/when stockbets.io does begin
          to facilitate real stakes games we will update these terms to provide
          full transparency into the state of our engagement with the SEC and any
          updates on our/the SEC's view of whether these games constitute securities-based
          swaps.
        </p>
        <p>
          For now the platform is yours to enjoy either as a medium for facilitating
          strictly "honor system" games of real stakes between you and your friends,
          for research purposes, or just for fun :)
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
