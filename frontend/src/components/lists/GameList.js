import React from 'react'
import { GameCard, GameCardPending } from 'components/lists/GameCard'
import PropTypes from 'prop-types'
import styled from 'styled-components'

const StyledSummary = styled.summary`
  color: ${(props) => props.color || 'var(--color-text-primary)'};
  font-size: var(--font-size-normal);
  font-weight: bold;
  margin-bottom: var(--space-200);
`

const gameListBuilder = (props) => {
  return props.games.map((entry, index) => {
    switch (props.cardType) {
      case 'pending':
        return <GameCardPending gameData={entry} key={index} isPublic={props.isPublic}/>
      default:
        return <GameCard
          gameId={entry.game_id}
          key={index}
        />
    }
  })
}

const GameList = (props) => {
  if (props.games.length === 0) return null
  return (
    <>
      { props.hide
        ? <details>
          { props.title &&
          <StyledSummary>{props.title}</StyledSummary>
          }
          {gameListBuilder(props)}
        </details>
        : <div>
          { props.title &&
          <StyledSummary>{props.title}</StyledSummary>
          }
          {gameListBuilder(props)}
        </div>
      }
    </>
  )
}

GameList.propTypes = {
  games: PropTypes.array,
  title: PropTypes.string,
  hide: PropTypes.bool,
  isPublic: PropTypes.bool
}

export { GameList }
