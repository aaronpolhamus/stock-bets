import React, { useContext, useState } from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { UserContext } from 'Contexts'
import { PlayerCardLegacy } from 'components/lists/PlayerCardLegacy'
import { Info } from 'react-feather'

const LeaderboardList = styled.ol`
  font-size: var(--font-size-small);
  padding-left: 0;
  position: relative;
  z-index: 1;
  list-style-type: none;
  counter-reset: leaderboard;
`

const PlayerRow = styled.div`
  cursor: pointer;
  position: relative;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  transform: translate3d(0, 0, 0);
  user-select: none;
  counter-increment: leaderboard;
  label{
    cursor: pointer;
    flex-basis: 70%;
    width: 70%;
    white-space: nowrap;
    justify-content: flex-start;
  }
  input {
    display: none;
  }

  label p{
    display: flex;
    margin-bottom: 0;
    &::before{
      content: counter(leaderboard)".";
      display: inline-block;
      width: 1.5rem;
      text-align: right;
    }
  }

  label p span{
    color: var(--color-text-gray);
    display: inline-block;
    width: 100%;
    text-overflow: ellipsis;
    overflow: hidden;
    &::before {
      background-color: var(--player-color);
      border-radius: 50%;
      content: '';
      display: inline-block;
      height: 0;
      margin-right: 0;
      position: relative;
      top: 0;
      transition: all .2s;
      width: 0;
      margin: 0 var(--space-50);
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
        <PlayerCardLegacy
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
