import PropTypes from 'prop-types'
import React, { useEffect, useState, useContext } from 'react'
import styled from 'styled-components'
import { fetchGameData } from 'components/functions/api'
import { Header } from 'components/layout/Layout'
import { Link } from 'react-router-dom'
import { numberToOrdinal } from 'components/functions/formattingHelpers'
import { PlayCircle, Eye } from 'react-feather'
import { SmallCaps } from 'components/textComponents/Text'
import { UserContext } from 'Contexts'

const CardMainColumn = styled.div`
  flex-grow: 1;
  padding: var(--space-200);
`

const GameCardWrapper = styled(Link)`
  border-radius: 10px;
  box-shadow: 0px 5px 11px rgba(53, 52, 120, 0.15), 0px 1px 4px rgba(31, 47, 102, 0.15);
  color: inherit;
  display: flex;
  line-height: 1;
  margin-bottom: var(--space-400);
  overflow: hidden;
  position: relative;
  top: 0;
  transition: all .2s;

  h3 {
    margin: 0
  }

  p {
    margin: 0
  }
  
  &:hover{
    color: inherit;
    text-decoration: none;
    top: -5px;
  }
`

const GameCardActiveInfo = styled.div`
  display: flex;
  align-items: center;
  text-align: right;
  color: var(--color-text-gray);
  font-weight: bold;
  p {
    margin-right: var(--space-200);
  }
  small {
    font-weight: regular;
    margin-top: var(--space-50);
    display: block;
  }
`

const GameCard = ({ gameId }) => {
  const { user } = useContext(UserContext)
  const currentUserLeaderboardPosition = (leaderboard) => {
    const position = leaderboard.findIndex(
      (playerStats, index) => {
        return playerStats.username === user.username
      }
    )
    return numberToOrdinal(parseInt(position) + 1)
  }

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
    ${currentUserLeaderboardPosition(gameInfo.leaderboard)}
    place
  `
  const currentLeader = gameInfo.leaderboard[0].username

  return (
    <GameCardWrapper to={`/play/${gameId}`}>
      <CardMainColumn>
        <Header alignItems='center'>
          <div>
            <h3>
              {gameInfo.title}
            </h3>
            <SmallCaps
              color='var(--color-text-gray)'
            >
              {gameInfo.benchmark_formatted}
            </SmallCaps>
          </div>
          <GameCardActiveInfo>
            <p>
              {leaderboardPosition}
              <small>
                1st: {currentLeader}
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
    <GameCardWrapper to={`/join/${gameData.game_id}`}>
      <CardMainColumn>
        <Header alignItems='center'>
          <div>
            <h3>
              {gameData.title}
            </h3>
            <small
              color='var(--color-text-gray)'
            >
              {`Created by: ${gameData.creator_username}`}
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
  gameId: PropTypes.string,
  currentUser: PropTypes.string
}

GameCardPending.propTypes = {
  gameData: PropTypes.object
}

export { GameCard, GameCardPending }
