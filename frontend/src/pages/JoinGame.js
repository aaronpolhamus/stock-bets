import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { fetchGameData, apiPost } from 'components/functions/api'
import {
  Layout,
  Sidebar,
  Column,
  Header,
  PageSection,
  Breadcrumb
} from 'components/layout/Layout'
import { GameSettings } from 'pages/game/GameSettings'
import { PendingGameParticipants } from 'pages/game/PendingGameParticipants'

import { Button } from 'react-bootstrap'
import * as Icon from 'react-feather'

const JoinGame = (props) => {
  const { gameId } = useParams()

  const [gameInfo, setGameInfo] = useState([])
  const [gameParticipants, setGameParticipants] = useState([])

  const getGameData = async () => {
    const gameData = await fetchGameData(gameId, 'game_info')
    setGameInfo(gameData)

    const gameParticipantsData = await fetchGameData(
      gameId,
      'get_pending_game_info'
    )
    setGameParticipants(gameParticipantsData)
  }

  useEffect(() => {
    getGameData()
  }, [])

  const handleRespondInvite = async (decision) => {
    await apiPost('respond_to_game_invite', {
      game_id: gameId,
      decision: decision
    })
    getGameData()
  }

  const renderButtons = (status) => {
    switch (status) {
      case 'invited':
        return (
          <div>
            <Button
              variant='outline-danger'
              onClick={() => {
                handleRespondInvite('declined')
              }}
            >
              Decline Invite
            </Button>
            <Button
              variant='success'
              onClick={() => {
                handleRespondInvite('joined')
              }}
            >
              Join Game
            </Button>
          </div>
        )
      case 'joined':
        return (
          <Button variant='success' disabled>
            Joined
          </Button>
        )
      case 'declined':
        return (
          <Button variant='danger' disabled>
            Declined
          </Button>
        )
    }
  }

  return (
    <Layout>
      <Sidebar md={2} size='sm'/>
      <Column md={10}>
        <PageSection>
          <Breadcrumb>
            <a href='/'>
              <Icon.ChevronLeft size={14} style={{ marginTop: '-3px' }} />
              Dashboard
            </a>
          </Breadcrumb>
          <Header>
            <h1>{gameInfo.title}</h1>
            {renderButtons(gameInfo.user_status)}
          </Header>
        </PageSection>
        <PageSection $marginBottomMd='var(--space-300)'>
          <GameSettings gameInfo={gameInfo} />
        </PageSection>
        <PageSection>
          <PendingGameParticipants participants={gameParticipants} />
        </PageSection>
      </Column>
    </Layout>
  )
}

export { JoinGame }
