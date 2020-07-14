import React, { useContext } from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { UserAvatar } from 'components/users/UserAvatar'
import { Info } from 'react-feather'
import { UserContext } from 'Contexts'

const UserRow = styled.label`
  display: flex;
  cursor: pointer;
  user-select: none;
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

const Leaderboard = ({ data, onSelect }) => {
  const { user } = useContext(UserContext)

  if (data === undefined) return null
  const leaderboardBuilder = () => {
    return data.map((player, index) => {
      const isCurrentUser = player.username === user.username
      return (
        <li key={index}>
          <UserRow onClick={() => {
            onSelect(player)
          }}>
            <input
              type='checkbox'
              value={player.username}
              color={player.color}
              defaultChecked={isCurrentUser}
            />
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

  return (
    <ol id='leaderboard'>
      {leaderboardBuilder()}
    </ol>
  )
}

Leaderboard.propTypes = {
  data: PropTypes.array,
  onSelect: PropTypes.func
}

export { Leaderboard }
