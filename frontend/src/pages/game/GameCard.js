import React, { useEffect, useState } from 'react'
import styled from 'styled-components'
import { fetchGameData } from 'components/functions/api'
import { Button } from 'react-bootstrap'
import { PlayGameStats } from 'components/lists/PlayGameStats'
import { Header } from 'components/layout/Layout'
import { FieldChart } from 'components/charts/FieldChart'

import { PlayCircle } from 'react-feather'
import { SmallCaps } from 'components/textComponents/Text'

const CardLeftColumn = styled.div`
  width: 300px;
  box-sizing: border-box;
  background-color: var(--color-light-gray);
  padding: var(--space-300);
`

const CardMainColumn = styled.div`
  padding: var(--space-300);
  flex-grow: 1;
`

const GameCardWrapper = styled.div`
  display: flex;
  border-radius: 10px;
  overrflow: hidden;
  margin-bottom: var(--space-400);
  box-shadow: 0px 5px 11px rgba(53, 52, 120, 0.15),
    0px 1px 4px rgba(31, 47, 102, 0.15);
`

const GameCard = ({ gameId }) => {
  const [gameInfo, setGameInfo] = useState([])

  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, 'game_info')
      setGameInfo(data)
    }

    getGameData()
  }, [gameId])
  console.log(gameInfo)
  return (
    <GameCardWrapper>
      <CardMainColumn>
        <Header alignItems='flex-start'>
          <div>
            <h3>{gameInfo.title}</h3>
            <SmallCaps
              color='var(--color-text-gray)'
            >
              {gameInfo.mode}
            </SmallCaps>
          </div>
          <Button href={`/play/${gameId}`} size='sm' variant='light'>
            <PlayCircle
              color='var(--color-primary-darken)'
              size={14}
              style={{ marginTop: '-3px', marginRight: '4px' }}
            />
          </Button>
        </Header>
      </CardMainColumn>
    </GameCardWrapper>
  )
}

export { GameCard }
