import React, { useEffect, useState } from 'react'
import styled from 'styled-components'
import { fetchGameData } from 'components/functions/api'
import PropTypes from 'prop-types'
import { daysLeft } from 'components/functions/formattingHelpers'
import { TextDivider } from 'components/textComponents/Text'
import { Header } from 'components/layout/Layout'
import { CashInfo } from 'components/lists/CashInfo'

const GameDetails = styled.small`
  display: block;
  font-size: var(--font-size-min);
  letter-spacing: var(--letter-spacing-smallcaps);
  text-transform: uppercase;
  color: var(--color-text-gray);
  margin-top: var(--space-100);
`

const GameName = styled.span`
  height: var(--space-400);
  display: inline-block;
`

const GameHeader = ({ gameId, cashData }) => {
  const [gameInfo, setGameInfo] = useState([])

  const getGameData = async () => {
    const data = await fetchGameData(gameId, 'game_info')
    setGameInfo(data)
  }

  useEffect(() => {
    getGameData()
  }, [])

  return (
    <Header>
      <h1>
        <GameName>{gameInfo.title}</GameName>
        <GameDetails>
          {gameInfo.benchmark_formatted}
          <TextDivider> | </TextDivider>
          Sidebet: {gameInfo.side_bets_perc}% {gameInfo.side_bets_period}
          {gameInfo.end_time &&
            (
              <>
                <TextDivider> | </TextDivider>
                {daysLeft(gameInfo.end_time)}
              </>
            )}
        </GameDetails>
      </h1>
      <CashInfo cashData={cashData} buyingPower={false} />
    </Header>
  )
}

GameHeader.propTypes = {
  gameId: PropTypes.string, 
  cashData: PropTypes.object
}

export { GameHeader }
