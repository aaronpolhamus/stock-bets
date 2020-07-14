import React, { useContext } from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { UserAvatar } from 'components/users/UserAvatar'
import { Info } from 'react-feather'
import { UserContext } from 'Contexts'

const LeaderboardList = styled.ol`
  font-size: var(--font-size-small);
  padding-left: 2em;
  position: relative;
  z-index: 1;
`

const PlayerLi = styled.li`
`

const PlayerRow = styled.label`
  cursor: pointer;
  display: flex;
  position: relative;
  transform: translate3d(0, 0, 0);
  user-select: none;

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

  &:hover p span{
    color: var(--color-text-primary);
    &::before{
      width: 8px;
      height: 8px;
    }
  }
`

const PlayerStocks = styled.div`
  color: var(--color-text-gray);
  span {
    color: var(--color-text-primary);
    font-size: var(--font-size-small)
  }
`

const PlayerReturn = styled.ul`
  list-style-type: none;
  padding: var(--space-200) 0;
  margin: 0 0 var(--space-200) 0;
  color: var(--color-text-gray);
  border-bottom: 1px solid var(--color-light-gray);
  li {
    display: flex;
    justify-content: space-between;
  }
  strong {
    color: var(--color-text-primary)
  }
`

const PlayerCard = ({ player, className }) => {
  return (
    <div className={className}>
      <header>
        <UserAvatar src={player.profile_pic} size='var(--space-700)' />
        <h2>
          {player.username}
          <small>
          ${player.portfolio_value.toLocaleString()}
          </small>
        </h2>
      </header>
      <PlayerReturn>
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
      </PlayerReturn>
      <PlayerStocks>
        <p>
          Stocks held:
        </p>
        <span>{ player.stocks_held.join(', ')}</span>
      </PlayerStocks>
    </div>
  )
}

const PlayerCardStyled = styled(PlayerCard)`
  position: absolute;
  background-color: white;
  box-shadow: 0px 15px 27px rgba(17, 7, 60, 0.15);
  width: 14rem;
  padding: var(--space-200);
  border-radius: 6px;
  top: -999px;
  left: 200%;
  opacity: 0;
  z-index: 2;
  transition: top 0s .5s, left .3s .1s, opacity .3s .1s;
  transform: translateY(-20%);
  header {
    display: flex;
    align-items: center;
  }
  h2{
    color: var(--color-text-primary);
    font-weight: bold;
    font-size: var(--font-size-normal);
    margin-bottom: 0;
    margin-left: var(--space-100);
    small {
      display: block;
      color: var(--color-success);
    }
  }
  div:hover > & {
    top: 0;
    left: 100%;
    opacity: 1;
    transition: left .3s .1s, opacity .3s .1s;
  }
`

const PlayerTooltip = styled.div`
  position: relative;
  small {
    margin-right: var(--space-50);
  }
  svg{
    margin-top: -3px;
  }
`

const Leaderboard = ({ data, onSelect }) => {
  const { user } = useContext(UserContext)

  if (data === undefined) return null
  const leaderboardBuilder = () => {
    return data.map((player, index) => {
      const isCurrentUser = player.username === user.username
      return (
        <PlayerLi key={index}>
          <PlayerRow
            onClick={() => {
              onSelect(player)
            }}
            style={{ '--player-color': player.color }}
          >
            <input
              type='checkbox'
              value={player.username}
              color={player.color}
              defaultChecked={isCurrentUser}
            />
            <p>
              <span>
                {player.username}
              </span>
            </p>
            <PlayerTooltip>
              <small>{player.return_ratio.toFixed(2)}%</small>
              <Info 
                size={14}
                color="var(--color-text-gray)"
              />
              <PlayerCardStyled player={player}/>
            </PlayerTooltip>
          </PlayerRow>
        </PlayerLi>
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

export { Leaderboard }
