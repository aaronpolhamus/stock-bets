import React, { useEffect, useState } from 'react'
import { Button, Form, Modal } from 'react-bootstrap'
import { MultiInvite } from 'components/forms/AddFriends'
import { AlignText } from 'components/textComponents/Text'
import api from 'services/api'
import { UserPlus } from 'react-feather'
import PropTypes from 'prop-types'

const InviteMoreFriends = ({ gameId, onInvite }) => {
  const [availableInvitees, setAvailableInvitees] = useState([])
  const [newInvitations, setNewInvitations] = useState({})
  const [showInviteConfirmation, setShowInviteConfirmation] = useState(false)
  const [showInviteForm, setShowInviteForm] = useState(false)

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
    newInvitationsCopy.game_id = gameId
    await api
      .post('/api/invite_users_to_pending_game', newInvitationsCopy)
      .then(() => {
        setShowInviteConfirmation(true)
      })
      .catch((e) => {})
  }

  const handleConfirmationClose = () => {
    setShowInviteConfirmation(false)
  }

  useEffect(() => {
    const fetchData = async () => {
      const response = await api.post('/api/game_defaults', { game_mode: 'multi_player' })
      if (response.status === 200) {
        setAvailableInvitees(response.data.available_invitees)
      }
    }
    fetchData()
  }, [])

  return (
    <>
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
    </>
  )
}

InviteMoreFriends.propTypes = {
  gameId: PropTypes.string,
  onInvite: PropTypes.func
}

export { InviteMoreFriends }
