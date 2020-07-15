import React from 'react'
import { GameCard, GameCardPending } from 'components/lists/GameCard'
import PropTypes from 'prop-types'

const gameListBuilder = (props) => {
  return props.games.map((entry, index) => {
    switch (props.cardType) {
      case 'pending':
        return <GameCardPending gameData={entry} key={index}/>
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
    <div>
      <h2>{props.title}</h2>
      {gameListBuilder(props)}
    </div>
  )
}

GameList.propTypes = {
  games: PropTypes.array,
  title: PropTypes.string
}

export { GameList }
