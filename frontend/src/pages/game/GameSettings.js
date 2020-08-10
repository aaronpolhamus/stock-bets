import React, { useEffect, useState } from 'react'
import { Button, Row, Col, Form, Modal } from 'react-bootstrap'
import { SectionTitle, Label, Flex, AlignText } from 'components/textComponents/Text'
import { UserMiniCard } from 'components/users/UserMiniCard'
import styled from 'styled-components'
import { breakpoints } from 'design-tokens'
import { MultiInvite } from 'components/forms/AddFriends'
import api from 'services/api'
import { UserPlus } from 'react-feather'

const StyledDd = styled.dd`
  margin-bottom: var(--space-300);
  margin-top: 0;
`

const TopPaddingColumn = styled(Col)`
  @media screen and (max-width: ${breakpoints.md}){
    padding-top: var(--space-300); 
  }
`

const GameSettings = ({ gameInfo }) => {
  const [availableInvitees, setAvailableInvitees] = useState([])
  const [newInvitations, setNewInvitations] = useState({})
  const [showInviteConfirmation, setShowInviteConfirmation] = useState(false)
  const [showInviteForm, setShowInviteForm] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      const response = await api.post('/api/game_defaults', { game_mode: 'multi_player' })
      if (response.status === 200) {
        setAvailableInvitees(response.data.available_invitees)
      }
    }
    fetchData()
  }, [])

  const handleInviteesChange = (inviteesInput) => {
    const newInvitationsCopy = { ...newInvitations }
    newInvitationsCopy.invitees = inviteesInput
    setNewInvitations(newInvitationsCopy)
  }

  const handleEmailInviteesChange = (_emails) => {
    const newInvitationsCopy = { ...newInvitations }
    newInvitationsCopy.email_invitees = _emails
    setNewInvitations(newInvitationsCopy)
  }

  const handleInvitationsSubmit = async (e) => {
    e.preventDefault()
    setShowInviteForm(false)
    const newInvitationsCopy = { ...newInvitations }
    newInvitationsCopy.game_id = gameInfo.id
    await api
      .post('/api/invite_users_to_pending_game', newInvitationsCopy)
      .then()
      .catch((e) => {})
    setShowInviteConfirmation(true)
  }

  const handleConfirmationClose = () => {
    setShowInviteConfirmation(false)
  }
  return (
    <>
      <Modal show={showInviteConfirmation} onHide={handleConfirmationClose}>
        <Modal.Body>
          <div className='text-center'>
          Great, we'll let your friends know about the game.
            <div>
              <small>
              Your friends who aren't on the platform yet will receive an invitation. Important note: the email needs to either be a gmail account or linked to your friend's Facebook account for them to get in.
              </small>
            </div>
          </div>
        </Modal.Body>
        <Modal.Footer className='centered'>
          <Button variant='primary' onClick={handleConfirmationClose}>
          Awesome!
          </Button>
        </Modal.Footer>
      </Modal>
      <Row>
        <Col md={3}>
          <SectionTitle>Game Host</SectionTitle>
          <UserMiniCard
            username={gameInfo.creator_username}
            avatarSrc={gameInfo.creator_profile_pic}
            nameColor='var(--color-lighter)'
          />
        </Col>
        <TopPaddingColumn md={9}>
          <SectionTitle>Game Settings</SectionTitle>
          <Flex as='dl'>
            <div>
              <dt>
                <Label>Buy In</Label>
              </dt>
              <StyledDd>{gameInfo.stakes_formatted}</StyledDd>
            </div>
            <div>
              <dt>
                <Label>Game Duration</Label>
              </dt>
              <StyledDd>{gameInfo.duration} days</StyledDd>
            </div>
            <div>
              <dt>
                <Label>Benchmark</Label>
              </dt>
              <StyledDd>{gameInfo.benchmark_formatted}</StyledDd>
            </div>
            <div>
              <dt>
                <Label>Sidebet</Label>
              </dt>
              <StyledDd>
                {gameInfo.side_bets_perc}% {gameInfo.side_bets_period}
              </StyledDd>
            </div>
          </Flex>
        </TopPaddingColumn>
        {gameInfo.is_host &&
          <>
            <AlignText
              align='right'
            >
              <Button
                onClick={() => {
                  setShowInviteForm(true)
                }}
              >
            Invite more friends to play
                <UserPlus
                  color='var(--color-secondary)'
                  size={18}
                  style={{
                    marginLeft: 'var(--space-100)'
                  }}
                />
              </Button>
            </AlignText>
            <Modal
              show={showInviteForm}
              onHide={() => {
                setShowInviteForm(false)
              }}
              centered
            >
              <Modal.Body>
                <Form onSubmit={handleInvitationsSubmit}>
                  <Form.Group>
                    <MultiInvite availableInvitees={availableInvitees} handleInviteesChange={handleInviteesChange} handleEmailsChange={handleEmailInviteesChange} />
                  </Form.Group>
                  <AlignText align='right'>
                    <Button variant='primary' type='submit'>
                      Invite additional players
                    </Button>

                  </AlignText>
                </Form>
              </Modal.Body>
            </Modal>
          </>}
      </Row>
    </>
  )
}

export { GameSettings }
