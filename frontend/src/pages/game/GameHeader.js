import React, { useEffect, useState } from 'react'
import styled from 'styled-components'
import { fetchGameData } from 'components/functions/api'
import { Tooltip } from 'components/forms/Tooltips'
import PropTypes from 'prop-types'

const GameDetails = styled.small`
  display: block;
  font-size: var(--font-size-min);
  letter-spacing: var(--letter-spacing-smallcaps);
  text-transform: uppercase;
  color: var(--color-text-gray);
  margin-top: var(--space-100);
`

const TextDivider = styled.span`
  font-weight: bold;
  color: var(--color-primary-darken);
`

const CashInfoWrapper = styled.div`
  text-align: right;
  color: var(--color-text-gray);
  p {
    margin: 0;
  }
  strong {
    text-transform: uppercase;
    font-size: var(--font-size-min);
  }
  small {
    color: var(--color-text-light-gray);
  }
`
const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
  h1 {
    margin-top: 0;
    line-height: 1;
  }
`

const GameName = styled.span`
  height: var(--space-400);
  display: inline-block;
`

const GameHeader = ({ gameId }) => {
  const [gameInfo, setGameInfo] = useState([])
  const [cashData, setCashData] = useState({})

  const getGameData = async () => {
    const data = await fetchGameData(gameId, 'game_info')
    const cashInfo = await fetchGameData(gameId, 'get_cash_balances')

    setCashData(cashInfo)
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
          {gameInfo.mode}
          <TextDivider> | </TextDivider>
          Sidebet: {gameInfo.side_bets_perc}% {gameInfo.side_bets_period}
          <TextDivider> | </TextDivider>
          {gameInfo.days_left && gameInfo.days_left} days left
        </GameDetails>
      </h1>
      <CashInfoWrapper>
        <Tooltip message='Your buying power is the amount of cash that you have on hand, minus the estimated value of any outstanding buy orders. If this is negative, check your open orders information and consider cancelling a few.' />
        <p>
          <strong>Cash Balance: </strong>
          {cashData.cash_balance && cashData.cash_balance}
        </p>
        <p>
          <small>
            <strong>Buying power: </strong>
            {cashData.buying_power && cashData.buying_power}
          </small>
        </p>
      </CashInfoWrapper>

    </Header>
  )
}

GameHeader.propTypes = {
  gameId: PropTypes.string
}

export { GameHeader }
