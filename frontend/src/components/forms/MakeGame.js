import React, { useState, useEffect } from 'react'
import { Redirect } from 'react-router-dom'
import api from 'services/api'
import { Form, Button, Modal, Row, Col } from 'react-bootstrap'
import { Typeahead } from 'react-bootstrap-typeahead'
import { optionBuilder } from 'components/functions/forms'
import { RadioButtons } from 'components/forms/Inputs'
import { Tooltip } from 'components/forms/Tooltips'
import styled from 'styled-components'

const StyledTypeahead = styled(Typeahead)`
  .rbt-input-wrapper {
    display: flex;
    flex-direction: row-reverse;
    flex-wrap: wrap-reverse;
  }
  .rbt-input-wrapper div {
    flex: 1 0 100% !important;
  }
  .rbt-input-wrapper [option] {
    margin-top: var(--space-300);
  }
`

const MakeGame = () => {
  const [defaults, setDefaults] = useState({})
  const [sidePotPct, setSidePotPct] = useState(0)
  const [formValues, setFormValues] = useState({})
  const [redirect, setRedirect] = useState(false)
  const [showModal, setShowModal] = useState(false)

  const fetchData = async () => {
    const response = await api.post('/api/game_defaults')
    if (response.status === 200) {
      setDefaults(response.data)
      setFormValues(response.data) // this syncs our form value submission state with the incoming defaults
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    await api
      .post('/api/create_game', formValues)
      .then()
      .catch((e) => {})
    setShowModal(true)
  }

  const handleClose = () => {
    setShowModal(false)
    setRedirect(true)
  }

  const handleChange = (e) => {
    const formValuesCopy = { ...formValues }
    formValuesCopy[e.target.name] = e.target.value
    setFormValues(formValuesCopy)
  }

  const handleRadio = (e) => {
    const formValuesCopy = { ...formValues }
    // formValuesCopy['mode'] =
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

  if (redirect) return <Redirect to='/' />
  return (
    <>
      <Form onSubmit={handleSubmit}>
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
            <Form.Group>
              <Form.Label>
                Game mode
                <Tooltip message='In a "consolation prize" game second place gets their money back. In a return weighted game, the pot is divided up proportionally based on game scores.' />
              </Form.Label>
              <RadioButtons
                options={defaults.game_modes}
                name='mode'
                onChange={handleChange}
                defaultValue={formValues.mode}
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
            <Row>
              <Col xs={6}>
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
              </Col>
            </Row>
            <Form.Group>
              <Form.Label>
                Benchmark
                <Tooltip message="If you're not sure what a Sharpe ratio is, go with simple return, which simply  divides the money you have at the end by the amount you started with." />
              </Form.Label>

              <RadioButtons
                options={defaults.benchmarks}
                name='benchmark'
                onChange={handleChange}
                defaultValue={formValues.benchmark}
              />
            </Form.Group>
          </Col>
          <Col lg={4}>
            <Form.Group>
              <Form.Label>
                Add Participant
                <Tooltip message="Which of your friends do you want to invite to this game? If you haven't added friends, yet, do this first." />
              </Form.Label>
              <StyledTypeahead
                id='typeahead-particpants'
                name='invitees'
                labelKey='name'
                multiple
                options={
                  defaults.available_invitees &&
                  Object.values(defaults.available_invitees)
                }
                placeholder="Who's playing?"
                onChange={handleInviteesChange}
              />
            </Form.Group>
          </Col>
          <Col lg={4}>
            <Form.Group>
              <Form.Label>
                Sidebet % of pot
                <Tooltip message='In addition to an end-of-game payout, if you choose to have sidebets your game will have either weekly or monthly winners based on the game metric. Key point: sidebets are always winner-takes-all, regardless of the game mode you picked.' />
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
                  <Tooltip message='The sidebet % that you just picked will be paid out evenly over either weekly or monthly intervals. ' />
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
          </Col>
        </Row>
        <div className='text-right'>
          <Button variant='primary' type='submit'>
            Create New Game
          </Button>
        </div>
      </Form>
      <Modal show={showModal} onHide={handleClose}>
        <Modal.Body>
          <div className='text-center'>
            You've sent a game invite! We'll let your friends know.
            <div>
              <small>
                You can check who's accepted your game from your dashboard
              </small>
            </div>
          </div>
        </Modal.Body>
        <Modal.Footer className='centered'>
          <Button variant='primary' onClick={handleClose}>
            Awesome!
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  )
}

export { MakeGame }
