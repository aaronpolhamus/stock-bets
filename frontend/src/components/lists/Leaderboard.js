import React from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { UserAvatar } from 'components/users/UserAvatar'
import { Info } from 'react-feather'

const UserRow = styled.label`
  display: flex;
  cursor: pointer;
  input {
    display: none;
  }
  span{
    display: flex;
  }
  
  input:checked + span{
    font-weight: bold;
  }
`
const UserCard = styled.div`
  display: none;
`

const leaderboardBuilder = (data, onSelect) => {
  return data.map((player, index) => {
    return (
      <li key={index}>
        <UserRow onClick={() => {
          onSelect(player)
        }}>
          <input type='checkbox' />
          <span>
            <UserAvatar src={player.profile_pic} size='small'/>
            {player.username}
          </span>
          <Info size={18} color="var(--color-cool-gray)"/>
        </UserRow>
        <UserCard>
          <header>
            <UserAvatar src={player.profile_pic} size='var(--space-700)' />
            <h2>
              {player.username}
              <small>
                ${player.portfolio_value.toLocaleString()}
              </small>
            </h2>
          </header>
          <ul>
            <li>
              { 'Simple Return ' }
              <strong>
                {player.return_ratio.toFixed(2)}%
              </strong>
            </li>
            <li>
              { 'Sharpe Ratio ' }
              <strong>
                {player.sharpe_ratio.toFixed(4)}
              </strong>
            </li>
          </ul>
          <span>{ player.stocks_held.join(', ')}</span>
        </UserCard>
      </li>
    )
  })
}

const Leaderboard = ({ data, onSelect }) => {
  if (data === undefined) return null
  return (
    <ol>
      {leaderboardBuilder(data, onSelect)}
    </ol>
  )
}

Leaderboard.propTypes = {
  data: PropTypes.object
}

export { Leaderboard }
