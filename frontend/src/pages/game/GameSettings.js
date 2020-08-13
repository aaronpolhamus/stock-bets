import React from 'react'
import { Row, Col } from 'react-bootstrap'
import { SectionTitle, Label, Flex } from 'components/textComponents/Text'
import { UserMiniCard } from 'components/users/UserMiniCard'
import styled from 'styled-components'
import { breakpoints } from 'design-tokens'
import PropTypes from 'prop-types'

const StyledDd = styled.dd`
  margin-bottom: var(--space-300);
  margin-top: 0;
`

const TopPaddingColumn = styled(Col)`
  @media screen and (max-width: ${breakpoints.md}){
    padding-top: var(--space-300); 
  }
`

const GameSettings = ({ gameInfo }) => {
  return (
    <>
      <Row>
        <Col md={3}>
          <SectionTitle>Game Host</SectionTitle>
          <UserMiniCard
            username={gameInfo.creator_username}
            avatarSrc={gameInfo.creator_profile_pic}
            nameColor='var(--color-lighter)'
          />
        </Col>
        <TopPaddingColumn md={9}>
          <SectionTitle>Game Settings</SectionTitle>
          <Flex as='dl'>
            <div>
              <dt>
                <Label>Buy In</Label>
              </dt>
              <StyledDd>{gameInfo.stakes_formatted}</StyledDd>
            </div>
            <div>
              <dt>
                <Label>Game Duration</Label>
              </dt>
              <StyledDd>{gameInfo.duration} days</StyledDd>
            </div>
            <div>
              <dt>
                <Label>Benchmark</Label>
              </dt>
              <StyledDd>{gameInfo.benchmark_formatted}</StyledDd>
            </div>
            <div>
              <dt>
                <Label>Sidebet</Label>
              </dt>
              <StyledDd>
                {gameInfo.side_bets_perc}% {gameInfo.side_bets_period}
              </StyledDd>
            </div>
          </Flex>
        </TopPaddingColumn>
      </Row>
    </>
  )
}

GameSettings.propTypes = {
  gameInfo: PropTypes.object
}

export { GameSettings }
