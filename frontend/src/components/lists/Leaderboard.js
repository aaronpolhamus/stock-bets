import React, { useContext, useState } from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { UserContext } from 'Contexts'
import { PlayerCard } from 'components/lists/PlayerCard'
import { Info } from 'react-feather'

const LeaderboardList = styled.ol`
  font-size: var(--font-size-small);
  padding-left: 2em;
  position: relative;
  z-index: 1;
`

const PlayerRow = styled.div`
  cursor: pointer;
  position: relative;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  transform: translate3d(0, 0, 0);
  user-select: none;

  label{
    cursor: pointer;
    flex-basis: 50%;
  }
  input {
    display: none;
  }

  p{
    display: flex;
    margin-bottom: 0;
  }

  p span{
    color: var(--color-text-gray);
    display: inline-block;
    margin-left: var(--space-50);
    &::before {
      background-color: var(--player-color);
      border-radius: 50%;
      content: '';
      display: inline-block;
      height: 0;
      margin-right: var(--space-50);
      position: relative;
      top: 0;
      transition: width .2s;
      width: 0;
    }
  }
  
  input:checked + p{
    font-weight: bold;
  }

  input:checked + p span{
    color: var(--color-text-primary);
    &::before{
      top: 2px;
      width: 12px;
      height: 12px;
    }
  }

  &:hover {
    z-index: 2
  }

  label:hover span{
    color: var(--color-text-primary);
    &::before{
      width: 8px;
      height: 8px;
    }
  }
`

const PlayerDetails = styled.div`
  position: relative;
  small {
    margin-right: var(--space-50);
  }
  svg{
    margin-top: -3px;
  }
`

const PlayerLi = ({ player, checked, onSelect }) => {
  const [showCard, setShowCard] = useState(false)

  const handleShowCard = () => {
    if (showCard) {
      setShowCard(false)
    } else {
      setShowCard(true)
    }
  }
  // console.log(player)
  return (
    <li>
      <PlayerRow
        style={{ '--player-color': player.color }}
      >
        <label>
          <input
            type='checkbox'
            value={player.username}
            color={player.color}
            onInput={() => {
              onSelect(player)
            }}
            defaultChecked={checked}
          />
          <p>
            <span>
              {player.username}
            </span>
          </p>
        </label>
        <PlayerDetails
          onClick={handleShowCard}
        >
          <small>{player.return_ratio.toFixed(2)}%</small>
          <Info
            size={14}
            color='var(--color-text-gray)'
          />
        </PlayerDetails>
        <PlayerCard
          show={showCard}
          player={player}
        />
      </PlayerRow>
    </li>
  )
}

const Leaderboard = ({ data, onSelect }) => {
  const { user } = useContext(UserContext)

  if (data === undefined) return null

  const leaderboardBuilder = () => {
    return data.map((player, index) => {
      const isCurrentUser = player.username === user.username

      return (
        <PlayerLi
          key={index}
          player={player}
          checked={isCurrentUser}
          onSelect={onSelect}
        />
      )
    })
  }

  return (
    <LeaderboardList id='leaderboard'>
      {leaderboardBuilder()}
    </LeaderboardList>
  )
}

Leaderboard.propTypes = {
  data: PropTypes.array,
  onSelect: PropTypes.func
}

PlayerLi.propTypes = {
  player: PropTypes.object,
  checked: PropTypes.bool,
  onSelect: PropTypes.func
}

export { Leaderboard }
