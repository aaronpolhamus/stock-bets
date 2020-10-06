import React from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { UserAvatar } from 'components/users/UserAvatar'

import { breakpoints } from 'design-tokens'

const PlayerCardWrapper = styled.div`
  width: 100%;
  cursor: default;
  user-select: text;
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

  flex-basis: 100%;
  flex-grow: 1;


  @media screen and (min-width: ${breakpoints.md}){
    position: absolute;
    background-color: white;
    box-shadow: 0px 15px 27px rgba(17, 7, 60, 0.15);
    width: 14rem;
    padding: var(--space-200);
    border-radius: 6px;
    top: -999px;
    left: 100%;
    opacity: 0;
    z-index: 2;
    transition: top 0s .5s, transform .3s .1s, opacity .3s .1s;
    transform: translateY(-20%) translateX(10%) translate3d(0, 0, 0);
    div:hover + &,
    &:hover {
      top: 0;
      transform: translateY(-20%) translateX(0) translate3d(0, 0, 0);
      opacity: 1;
      transition: transform .3s .2s, opacity .3s .2s;
    }
  }

  @media screen and (max-width: ${breakpoints.md}){
    transition: all .3s ease-in-out;
    max-height: ${props => props.$show ? '100vh' : 0};
    margin-bottom: ${props => props.$show ? 'var(--space-300)' : 0};

    overflow: hidden;

    header{
      justify-content: space-between;
    }
    h2 span{
      display: none;
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

const PlayerCard = ({ player, type = 'game', show }) => {
  return (
    <PlayerCardWrapper $show={show}>
      <header>
        <UserAvatar src={player.profile_pic} size='var(--space-700)' />
        <h2>
          <span>
            {player.username}
          </span>
          {type === 'game'
            ? (
              <small>
                  ${player.portfolio_value.toLocaleString()}
              </small>
            )
            : null
          }
        </h2>
      </header>

      {type === 'game'
        ? (
          <>
            <PlayerReturn>
              <li>
                {'Simple Return '}
                <strong>
                  {player.return_ratio.toFixed(2)}%
                </strong>
              </li>
              <li>
                {'Sharpe Ratio '}
                <strong>
                  {player.sharpe_ratio.toFixed(4)}
                </strong>
              </li>
            </PlayerReturn>
            <PlayerStocks>
              <p>
                            Stocks held:
              </p>
              <span>{player.stocks_held.join(', ')}</span>
            </PlayerStocks>
          </>
        )
        : null
      }
    </PlayerCardWrapper>
  )
}

PlayerCard.propTypes = {
  type: PropTypes.string,
  player: PropTypes.object,
  show: PropTypes.bool
}

export { PlayerCard }
