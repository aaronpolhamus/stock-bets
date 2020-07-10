import React from 'react'
import { GameCard, GameCardPending } from 'components/lists/GameCard'
import PropTypes from 'prop-types'

const gameListBuilder = (props) => {
  return props.games.map((entry, index) => {
    switch (props.cardType){
      case 'pending':
        return <GameCardPending gameData={entry}/>
      default:
        return <GameCard
          gameId={entry.game_id}
          currentUser={props.currentUser}
          key={index}
        />
    }
  })
}

const GameList = (props) => {
  return (
    <div>
      {gameListBuilder(props)}
    </div>
  )
}

GameList.propTypes = {
  games: PropTypes.array,
  currentUser: PropTypes.string
}

export { GameList }
