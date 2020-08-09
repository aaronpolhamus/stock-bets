import React, { useEffect, useState } from 'react'
import { Redirect } from 'react-router-dom'
import api from 'services/api'
import { Button, Col, Form, Modal, Row } from 'react-bootstrap'
import { optionBuilder } from 'components/functions/forms'
import { RadioButtons } from 'components/forms/Inputs'
import { Tooltip } from 'components/forms/Tooltips'
import { MultiInvite } from 'components/forms/AddFriends'
import { PayPalButton } from 'react-paypal-button-v2'

const MakeGame = ({ gameMode }) => {
  // game settings
  const [defaults, setDefaults] = useState({})
  const [sidePotPct, setSidePotPct] = useState(0)
  const [formValues, setFormValues] = useState({})
  const [redirect, setRedirect] = useState(false)
  const [showConfirationModal, setShowConfirationModal] = useState(false)
  const [showPaypalModal, setShowPaypalModal] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      const response = await api.post('/api/game_defaults', { game_mode: gameMode })
      if (response.status === 200) {
        setDefaults(response.data)
        setFormValues(response.data) // this syncs our form value submission state with the incoming defaults
      }
    }
    fetchData()
  }, [])

  const createGame = () => {
    const formValuesCopy = { ...formValues }
    formValuesCopy.game_mode = gameMode
    api
      .post('/api/create_game', formValuesCopy)
      .then()
      .catch((e) => {
      })
    setShowConfirationModal(true)
  }

  const handleFormSubmit = async () => {
    if (gameMode === 'multi_player' && (!formValues.email_invitees && !formValues.invitees)) {
      window.alert('In multiplayer mode you need to invite at least one other user via username or email. Switch to "You vs. The Market" if you meant to select single player mode')
    } else if (gameMode === 'multi_player' && formValues.stakes === 'real') {
      setShowPaypalModal(true)
    } else {
      createGame()
    }
  }

  const handleChange = (e) => {
    const formValuesCopy = { ...formValues }
    formValuesCopy[e.target.name] = e.target.value
    setFormValues(formValuesCopy)
  }

  // necessary because this field has a special change action whereby the
  const handleSideBetChange = (e) => {
    setSidePotPct(e.target.value)
    const formValuesCopy = { ...formValues }
    formValuesCopy.side_bets_perc = e.target.value
    setFormValues(formValuesCopy)
  }

  // I'm not in love wit this separate implementation for typeahead fields. I couldn't figure out a good way to get them to play well
  // with standard bootstrap controlled forms, so this is what I went with
  const handleInviteesChange = (inviteesInput) => {
    const formValuesCopy = { ...formValues }
    formValuesCopy.invitees = inviteesInput
    setFormValues(formValuesCopy)
  }

  const handleEmailInviteesChange = (_emails) => {
    const formValuesCopy = { ...formValues }
    formValuesCopy.email_invitees = _emails
    setFormValues(formValuesCopy)
  }

  if (redirect) return <Redirect to='/' />
  return (
    <>
      <Form>
        {/* We should probably have this on the bottom of the form. It's just here for now because test_user can't write CSS */}
        <Row>
          <Col lg={4}>
            <Form.Group>
              <Form.Label>
                Title
                <Tooltip message='We randomly generate a nonsense title for you, but feel free to pick your own!' />
              </Form.Label>
              <Form.Control
                name='title'
                type='input'
                defaultValue={defaults.title}
                onChange={handleChange}
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
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
            </Row>
            {gameMode === 'multi_player' &&
              <Row>
                <Col xs={6}>
                  <Form.Group>
                    <Form.Label>Choose the game stakes</Form.Label>
                    <RadioButtons
                      options={defaults.stakes_options}
                      name='stakes'
                      onChange={handleChange}
                      defaultChecked={formValues.stakes}
                    />
                  </Form.Group>
                  {formValues.stakes === 'real' &&
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
                          onChange={handleChange}
                        />
                      </Form.Group>
                      <Form.Group>
                        <Form.Label>
                    Sidebet % of pot
                          <Tooltip
                            message='In addition to an end-of-game payout, if you choose to have sidebets your game will have either weekly or monthly winners based on the game metric. Key point: sidebets are always winner-takes-all, regardless of the game mode you picked.'
                          />
                        </Form.Label>
                        <Form.Control
                          name='side_bets_perc'
                          type='input'
                          defaultValue={defaults.side_bets_perc}
                          value={sidePotPct}
                          onChange={handleSideBetChange}
                        />
                      </Form.Group>
                      {sidePotPct > 0 && (
                        <Form.Group>
                          <Form.Label>
                    Sidebet period
                            <Tooltip
                              message='The sidebet % that you just picked will be paid out evenly over either weekly or monthly intervals. '
                            />
                          </Form.Label>
                          <Form.Control
                            name='side_bets_period'
                            as='select'
                            defaultValue={defaults.side_bets_period}
                            onChange={handleChange}
                          >
                            {defaults.sidebet_periods &&
                    optionBuilder(defaults.sidebet_periods)}
                          </Form.Control>
                        </Form.Group>
                      )}
                    </>}
                </Col>
              </Row>}
            {gameMode === 'multi_player' &&
              <Row>
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
                      onChange={handleChange}
                    />
                  </Form.Group>
                </Col>
              </Row>}
            <Form.Group>
              <Form.Label>
                Benchmark
                <Tooltip message="Simple return is your total portfolio value at the end of your game divided by what you started with. The Sharpe ratio is trickier, and it's important to understand it if you're going to use it as a benchmark. It's possible, for example, to have a positive Sharpe ratio even if your total return is negative. Check out this video for the details of how we calculate the Sharpe ratio: https://www.youtube.com/watch?v=s0bxoD_0fAU" />
              </Form.Label>

              <RadioButtons
                options={defaults.benchmarks}
                name='benchmark'
                onChange={handleChange}
                defaultChecked={formValues.benchmark}
              />
            </Form.Group>
          </Col>
          {gameMode === 'multi_player' &&
            <Col lg={4}>
              <MultiInvite availableInvitees={defaults.available_invitees} handleInviteesChange={handleInviteesChange} handleEmailsChange={handleEmailInviteesChange} />
            </Col>}
        </Row>
        <div className='text-right'>
          <Button variant='primary' onClick={handleFormSubmit}>
            Create game
          </Button>
        </div>
      </Form>
      <Modal show={showConfirationModal}>
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
        <Modal.Footer className='centered'>
          <Button
            variant='primary' onClick={() => {
              setShowConfirationModal(false)
              setRedirect(true)
            }}
          >
            Awesome!
          </Button>
        </Modal.Footer>
      </Modal>
      <Modal show={showPaypalModal} onHide={() => {}} centered>
        <Modal.Body>
          <div className='text-center'>
            Fund your buy-in to open a real-stakes game
            <div>
              <small>
                We'll send you a full refund if the game doesn't kick off for any reason 👍
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
                    value: formValues.buy_in
                  }
                }]
              })
            }}
            onApprove={(data, actions) => {
              // Capture the funds from the transaction
              return actions.order.capture().then(function (details) {
                setShowPaypalModal(false)
                setShowConfirationModal(true)
                createGame()
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

export { MakeGame }
