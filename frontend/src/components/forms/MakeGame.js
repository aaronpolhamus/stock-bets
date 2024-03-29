import React, { useEffect, useState } from 'react'
import { Redirect } from 'react-router-dom'
import api from 'services/api'
import { Button, Col, Form, Modal, Row } from 'react-bootstrap'
import { RadioButtons } from 'components/forms/Inputs'
import { Tooltip } from 'components/forms/Tooltips'
import { MultiInvite } from 'components/forms/AddFriends'
import { PayPalButton } from 'react-paypal-button-v2'
import { apiPost } from 'components/functions/api'
import { Loader } from 'components/Loader'
import { ModalOverflowControls } from 'components/layout/Layout'

const MakeGame = ({ gameMode }) => {
  // game settings
  const [defaults, setDefaults] = useState({})
  const [title, setTitle] = useState(null)
  const [duration, setDuration] = useState(null)
  const [benchmark, setBenchmark] = useState(null)
  const [buyIn, setBuyIn] = useState(null)
  const [sideBetsPerc, setSideBetsPerc] = useState(0)
  const [sideBetsPeriod, setSideBetsPeriod] = useState(null)
  const [invitees, setInvitees] = useState([])
  const [emailInvitees, setEmailInvitees] = useState([])
  const [inviteWindow, setInviteWindow] = useState(null)
  const [stakes, setStakes] = useState(null)
  const [redirect, setRedirect] = useState(false)
  const [showConfirmationModal, setShowConfirmationModal] = useState(false)
  const [showPaypalModal, setShowPaypalModal] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      const response = await api.post('/api/game_defaults', { game_mode: gameMode })
      if (response.status === 200) {
        setDefaults(response.data)
        setTitle(response.data.title)
        setDuration(response.data.duration)
        setBenchmark(response.data.benchmark)
        setBuyIn(response.data.buy_in)
        setSideBetsPerc(response.data.side_bets_perc)
        setSideBetsPeriod(response.data.side_bets_period)
        setInviteWindow(response.data.invite_window)
        setStakes(response.data.stakes)
      }
    }
    fetchData()
  }, [])

  const handleFormSubmit = async () => {
    if (gameMode === 'multi_player' && (!emailInvitees && !invitees)) {
      window.alert('In multiplayer mode you need to invite at least one other user via username or email. Switch to "You vs. The Market" if you meant to select single player mode')
    // } else if (gameMode === 'multi_player' && stakes === 'real') {  // TODO: turn these lines back on once we are on a more solid legal footing to accept real payments.
    //   setShowPaypalModal(true)
    } else {
      apiPost('create_game', {
        title: title,
        duration: duration,
        benchmark: benchmark,
        buy_in: buyIn,
        side_bets_perc: sideBetsPerc,
        side_bets_period: sideBetsPeriod,
        invitees: invitees,
        email_invitees: emailInvitees,
        invite_window: inviteWindow,
        stakes: stakes,
        game_mode: gameMode
      })
      setShowConfirmationModal(true)
    }
  }

  if (redirect) return <Redirect to='/' />
  return (
    <>
      <Form>
        <Loader show={loading} />
        <Row>
          <Col lg={6}>
            <Form.Group>
              <Form.Label>
                Title
                <Tooltip message='We randomly generate a nonsense title for you, but feel free to pick your own!' />
              </Form.Label>
              <Form.Control
                name='title'
                type='input'
                defaultValue={defaults.title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </Form.Group>
            <Row>
              <Col xs={6}>
                <Form.Group>
                  <Form.Label>
                    Game duration (days)
                    <Tooltip message='How many days would you like your game to last for?' />
                  </Form.Label>
                  <Form.Control
                    name='duration'
                    type='input'
                    defaultValue={defaults.duration}
                    onChange={(e) => setDuration(e.target.value)}
                  />
                </Form.Group>
              </Col>
              {['multi_player', 'public'].includes(gameMode) &&
                <Col xs={6}>
                  <Form.Group>
                    <Form.Label>
                    Invite window (days)
                      <Tooltip message='For how many days would you like your game to be open for before kicking off automatically?' />
                    </Form.Label>
                    <Form.Control
                      name='invite_window'
                      type='input'
                      defaultValue={defaults.invite_window}
                      onChange={(e) => setInviteWindow(e.target.value)}
                    />
                  </Form.Group>
                </Col>}
            </Row>
            {gameMode === 'multi_player' &&
              <Row>
                <Col xs={12}>
                  <Form.Group>
                    <Form.Label>Choose the game stakes</Form.Label>
                    <RadioButtons
                      optionsList={defaults.stakes_options}
                      name='stakes'
                      onChange={(e) => setStakes(e.target.value)}
                      defaultChecked={stakes}
                    />
                  </Form.Group>
                  {stakes === 'real' &&
                    <>
                      <Form.Group>
                        <Form.Label>
                      Buy-in
                          <Tooltip message='How many dollars does each player need to put in to join the game?' />
                        </Form.Label>
                        <Form.Control
                          name='buy_in'
                          type='input'
                          defaultValue={defaults.buy_in}
                          onChange={(e) => setBuyIn(e.target.value)}
                        />
                      </Form.Group>
                    </>}
                </Col>
              </Row>}
          </Col>
          {gameMode === 'multi_player' &&
            <Col lg={6}>
              <MultiInvite availableInvitees={defaults.available_invitees} handleInviteesChange={(input) => setInvitees(input)} handleEmailsChange={(emails) => setEmailInvitees(emails)} />
            </Col>}
        </Row>
        <div className='text-right'>
          <Button variant='primary' onClick={handleFormSubmit}>
            Create game
          </Button>
        </div>
      </Form>
      <Modal
        centered
        show={showConfirmationModal}
        onHide={() => {
          setShowConfirmationModal(false)
        }}
      >
        {gameMode === 'multi_player' &&
          <Modal.Body>
            <div className='text-center'>
            You've sent a game invite! We'll let your friends know.
              <div>
                <small>
                You can check who's accepted your game from your dashboard
                </small>
              </div>
            </div>
          </Modal.Body>}
        {gameMode === 'single_player' &&
          <Modal.Body>
            <div className='text-center'>
            Your single player game is live!
              <div>
                <small>
                They say the market is tough to beat...
                </small>
              </div>
            </div>
          </Modal.Body>}
        {gameMode === 'public' &&
          <Modal.Body>
            <div className='text-center'>
            Your game is visible to everyone on stockbets 👍
              <div>
                <small>
                It will kick off after either 9 more people join or the invite window runs out
                </small>
              </div>
            </div>
          </Modal.Body>}
        <Modal.Footer className='centered'>
          <Button
            variant='primary' onClick={() => {
              setShowConfirmationModal(false)
              setRedirect(true)
            }}
          >
            Awesome!
          </Button>
        </Modal.Footer>
      </Modal>
      <Modal
        show={showPaypalModal}
        onHide={() => {
          setShowPaypalModal(false)
        }}
        centered
      >
        <Modal.Header>
          Fund your buy-in
          <br />
          to open a real-stakes game
        </Modal.Header>
        <Modal.Body>
          <div>
            We'll send you a full refund if the game doesn't kick off for any reason 👍
          </div>
          <PayPalButton
            shippingPreference='NO_SHIPPING'
            createOrder={(data, actions) => {
              return actions.order.create({
                purchase_units: [{
                  amount: {
                    currency_code: 'USD',
                    value: buyIn
                  }
                }]
              })
            }}
            onCancel={(data) => {
            }}
            onApprove={(data, actions) => {
              setLoading(true)
              return actions.order.capture().then(function (details) {
                setLoading(false)
                setShowPaypalModal(false)
                setShowConfirmationModal(true)
                const bookGame = async () => {
                  await api
                    .post('/api/create_game', {
                      title: title,
                      duration: duration,
                      benchmark: benchmark,
                      buy_in: buyIn,
                      side_bets_perc: sideBetsPerc,
                      side_bets_period: sideBetsPeriod,
                      invitees: invitees,
                      email_invitees: emailInvitees,
                      invite_window: inviteWindow,
                      stakes: stakes,
                      game_mode: gameMode
                    })
                    .then((r) => {
                      apiPost('process_payment', {
                        game_id: r.data.game_id,
                        processor: 'paypal',
                        type: 'start',
                        payer_email: details.payer.email_address,
                        uuid: details.payer.payer_id,
                        amount: details.purchase_units[0].amount.value,
                        currency: details.purchase_units[0].amount.currency_code
                      })
                    })
                    .catch((e) => console.log(e))
                }
                bookGame()
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
        </Modal.Body>
        <ModalOverflowControls>
          <Button
            variant='outline-info' onClick={() => {
              setShowPaypalModal(false)
            }}
          >
          Actually, take me back
          </Button>
        </ModalOverflowControls>
      </Modal>
    </>
  )
}

export { MakeGame }
