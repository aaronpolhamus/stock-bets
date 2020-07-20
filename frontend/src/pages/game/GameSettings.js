import React from 'react'
import { SidebarSection } from 'components/layout/Layout'
import { SectionTitle, Label } from 'components/textComponents/Text'
import { UserMiniCard } from 'components/users/UserMiniCard'
import styled from 'styled-components'

const StyledDd = styled.dd`
  margin-bottom: var(--space-300);
  margin-top: 0;
`

const GameSettings = ({ gameInfo }) => {
  return (
    <div>
      <SidebarSection>
        <SectionTitle color='var(--color-primary)'>Game Host</SectionTitle>
        <UserMiniCard
          username={gameInfo.creator_username}
          nameColor='var(--color-lighter)'
        />
      </SidebarSection>
      <SidebarSection>
        <SectionTitle color='var(--color-primary)'>Game Settings</SectionTitle>
        <dl>
          <dt>
            <Label>Buy In</Label>
          </dt>
          <StyledDd>{gameInfo.buy_in}</StyledDd>
          <dt>
            <Label>Game Duration</Label>
          </dt>
          <StyledDd>{gameInfo.duration} days</StyledDd>
          <dt>
            <Label>Benchmark</Label>
          </dt>
          <StyledDd>{gameInfo.benchmark_formatted}</StyledDd>
          <dt>
            <Label>Sidebet</Label>
          </dt>
          <StyledDd>
            {gameInfo.side_bets_perc}% {gameInfo.side_bets_period}
          </StyledDd>
        </dl>
      </SidebarSection>
    </div>
  )
}

export { GameSettings }
