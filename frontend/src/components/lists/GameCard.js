import React, { useEffect, useState } from 'react'
import styled from 'styled-components'
import { fetchGameData } from 'components/functions/api'
import { Button } from 'react-bootstrap'
import { Header } from 'components/layout/Layout'
import { PlayCircle, Eye } from 'react-feather'
import { SmallCaps } from 'components/textComponents/Text'
import PropTypes from 'prop-types'
import { numberToOrdinal } from 'components/functions/formattingHelpers'

const CardMainColumn = styled.div`
  padding: var(--space-200);
  flex-grow: 1;
`

const GameCardWrapper = styled.a`
  display: flex;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: var(--space-400);
  box-shadow: 0px 5px 11px rgba(53, 52, 120, 0.15),
    0px 1px 4px rgba(31, 47, 102, 0.15);
  color: inherit;
  position: relative;
  top: 0;
  transition: all .2s;
  line-height: 1;
  h3 {
    margin: 0
  }
  p {
    margin: 0
  }
  &:hover{
    top: -5px;
    color: inherit;
    text-decoration: none;
  }
`

const GameCardActiveInfo = styled.div`
  display: flex;
  align-items: center;
  text-align: right;
  color: var(--color-text-gray);
  font-weight: bold;
  p {
    margin-right: var(--space-200)
  }
  small {
    font-weight: regular;
    margin-top: var(--space-50);
    display: block;
  }
`

const currentUserLeaderboardPosition = (leaderboard, currentUser) => {
  const position = leaderboard.findIndex(
    (playerStats, index) => {
      return playerStats.username === currentUser
    }
  )
  return numberToOrdinal(parseInt(position) + 1)
}

const GameCard = ({ gameId, currentUser}) => {
  const [gameInfo, setGameInfo] = useState({})

  const getGameData = async () => {
    const data = await fetchGameData(gameId, 'game_info')
    setGameInfo(data)
  }

  useEffect(() => {
    getGameData()
  }, [])

  if (Object.keys(gameInfo).length === 0) return null

  const leaderboardPosition = `
    ${currentUserLeaderboardPosition(gameInfo.leaderboard, currentUser)}
    place
  `
  const currentLeader = gameInfo.leaderboard[0].username

  return (
    <GameCardWrapper href={`/play/${gameId}`}>
      <CardMainColumn>
        <Header alignItems='center'>
          <div>
            <h3>
              { gameInfo.title }
            </h3>
            <SmallCaps
              color='var(--color-text-gray)'
            >
              { gameInfo.mode }
            </SmallCaps>
          </div>
          <GameCardActiveInfo>
            <p>
              { leaderboardPosition }
              <small>
                1st: { currentLeader }
              </small>
            </p>
            <PlayCircle
              color='var(--color-success)'
              size={24}
              style={{ marginTop: '-3px', marginRight: '4px' }}
            />
          </GameCardActiveInfo>
        </Header>
      </CardMainColumn>
    </GameCardWrapper>
  )
}

const GameCardPending = ({ gameData }) => {
  return (
    <GameCardWrapper href={`/join/${gameData.game_id}`}>
      <CardMainColumn>
        <Header alignItems='center'>
          <div>
            <h3>
              { gameData.title }
            </h3>
            <small
              color='var(--color-text-gray)'
            >
              { `Created by: ${gameData.creator_username}` }
            </small>
          </div>
          <Eye
            color='var(--color-primary-darken)'
            size={24}
            style={{ marginTop: '-3px', marginRight: '4px' }}
          />
        </Header>
      </CardMainColumn>
    </GameCardWrapper>
  )
}

GameCard.propTypes = {
  gameId: PropTypes.number,
  currentUser: PropTypes.string
}

GameCardPending.propTypes = {
  gameData: PropTypes.object
}

export { GameCard, GameCardPending }
