import React, { useEffect, useState } from 'react'
import { Redirect, useParams } from 'react-router-dom'
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
import { Button, Modal } from 'react-bootstrap'
import * as Icon from 'react-feather'
import { PayPalButton } from 'react-paypal-button-v2'
import api from 'services/api'
import { InviteMoreFriends } from 'components/forms/InviteMoreFriends'

const JoinGame = () => {
  const { gameId } = useParams()
  const [gameInfo, setGameInfo] = useState([])
  const [gameParticipants, setGameParticipants] = useState([])
  const [showPaypalModal, setShowPaypalModal] = useState(false)
  const [showConfirmationModal, setShowConfirmationModal] = useState(false)
  const [redirect, setRedirect] = useState(false)
  const [decision, setDecision] = useState(null)

  const getGameData = async () => {
    const gameData = await fetchGameData(gameId, 'game_info')
    setGameInfo(gameData)

    const gameParticipantsData = await fetchGameData(
      gameId,
      'get_pending_game_info'
    )
    setGameParticipants(gameParticipantsData.platform_invites)
  }

  useEffect(() => {
    getGameData()
  }, [])

  const handleRespondInvite = async (choice) => {
    setDecision(choice)
    if (gameInfo.stakes === 'real' && choice === 'joined') {
      setShowPaypalModal(true)
    } else {
      await apiPost('respond_to_game_invite', {
        game_id: gameId,
        decision: choice
      })
      setShowConfirmationModal(true)
    }
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
  if (redirect) return <Redirect to='/' />
  return (
    <>
      <Layout>
        <Sidebar md={2} size='sm' />
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
              <div>
                {gameInfo.is_host &&
                  <InviteMoreFriends
                    gameId={gameId}
                  />
                }
                {renderButtons(gameInfo.user_status)}
              </div>
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
      <Modal show={showConfirmationModal}>
        <Modal.Body>
          {decision === 'joined' &&
            <div className='text-center'>
            You're in!
              <div>
                <small>
                The game will start once the (a) the invite windows expires or (b) everyone has either joined or
                declined
                </small>
              </div>
            </div>}
          {decision === 'declined' &&
            <div className='text-center'>
            Looks like you're sitting this round out
              <div>
                <small>
                Hope to see you in another game sometime soon!
                </small>
              </div>
            </div>}
        </Modal.Body>
        <Modal.Footer className='centered'>
          <Button
            variant='primary' onClick={() => {
              setShowConfirmationModal(false)
              setRedirect(true)
            }}
          >
            Got it
          </Button>
        </Modal.Footer>
      </Modal>
      <Modal show={showPaypalModal} onHide={() => {}} centered>
        <Modal.Body>
          <div className='text-center'>
        Fund the buy-in to join a real stakes game.
            <div>
              <small>
            We'll send you a full refund if the game doesn't kick off for any reason, including if you change your mind before the game starts 👍
              </small>
            </div>
          </div>
          <PayPalButton
            shippingPreference='NO_SHIPPING'
            createOrder={(data, actions) => {
              return actions.order.create({
                purchase_units: [{
                  amount: {
                    currency_code: 'USD',
                    value: gameInfo.buy_in
                  }
                }]
              })
            }}
            onApprove={(data, actions) => {
              return actions.order.capture().then(function (details) {
                setShowPaypalModal(false)
                setShowConfirmationModal(true)
                const joinGame = async () => {
                  await api
                    .post('/api/respond_to_game_invite', {
                      game_id: gameId,
                      decision: 'joined'
                    })
                    .then((r) => {
                      apiPost('process_payment', {
                        game_id: gameInfo.id,
                        processor: 'paypal',
                        type: 'join',
                        payer_email: details.payer.email_address,
                        uuid: details.payer.payer_id,
                        amount: details.purchase_units[0].amount.value,
                        currency: details.purchase_units[0].amount.currency_code
                      })
                    })
                    .catch((e) => console.log(e))
                }
                joinGame()
              })
            }}
            onError={(err) => {
              console.log(err)
            }}
            options={{
              clientId: process.env.REACT_APP_PAYPAL_CLIENT_ID,
              currency: 'USD'
            }}
          />
          <Button
            variant='secondary' onClick={() => {
              setShowPaypalModal(false)
            }}
          >
        Actually, take me back
          </Button>
        </Modal.Body>
      </Modal>
    </>
  )
}

export { JoinGame }
