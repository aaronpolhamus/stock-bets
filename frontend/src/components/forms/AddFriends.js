import React, { useState } from 'react'
import { Button, Modal, Accordion, Form } from 'react-bootstrap'
import {
  TextButton,
  AuxiliarText,
  FlexRow
} from 'components/textComponents/Text'
import { AsyncTypeahead } from 'react-bootstrap-typeahead'
import * as Icon from 'react-feather'
import { apiPost } from 'components/functions/api'
import { UserMiniCard } from 'components/users/UserMiniCard'

const AddFriends = ({ inviteType }) => {
  const [isLoading, setIsLoading] = useState(false)
  const [friendSuggestions, setFriendSuggestions] = useState([])
  const [friendInvitee, setFriendInvitee] = useState('')
  const [emailInvitee, setEmailInvitee] = useState('')
  const [show, setShow] = useState(false)

  const handleClose = () => setShow(false)

  const handleFriendInvite = async (e) => {
    e.preventDefault()

    if (friendInvitee !== '' && inviteType === 'internal') {
      await apiPost('send_friend_request', {
        friend_invitee: friendInvitee
      })
      setShow(true)
    }
    if (emailInvitee && inviteType === 'external') {
      await apiPost('invite_user_by_email', {
        friend_email: emailInvitee
      })
      setShow(true)
    }
  }

  const handleChange = (invitee) => {
    if (invitee[0] === undefined) return
    setFriendInvitee(invitee[0].username)
  }

  const handleEmailChange = (e) => {
    setEmailInvitee(e.target.value)
  }

  const handleSuggestions = async (query) => {
    setIsLoading(true)
    apiPost('suggest_friend_invites', { text: query })
      .then((friends) => {
        setFriendSuggestions(friends)
        setIsLoading(false)
      })
  }

  const friendLabel = (label) => {
    switch (label) {
      case 'you_invited':
        return <AuxiliarText>Invite sent</AuxiliarText>
      case 'invited_you':
        return <AuxiliarText>Invited you</AuxiliarText>
    }
  }

  return (
    <Accordion defaultActiveKey='0' className='text-right'>
      <Accordion.Toggle
        as={TextButton}
        eventKey='1'
        color='var(--color-light-gray)'
      >
        {inviteType === 'internal' ? <span>Add a friend on the platform    </span> : <span>Email a friend an invite    </span>}
        <Icon.PlusCircle color='var(--color-primary)' size='16' />
      </Accordion.Toggle>
      <Accordion.Collapse eventKey='1'>
        <Form onSubmit={handleFriendInvite}>
          <Form.Group>
            {inviteType === 'internal'
              ? <AsyncTypeahead
                id='typeahead-particpants'
                name='invitees'
                labelKey='username'
                isLoading={isLoading}
                options={friendSuggestions}
                placeholder="Type your friend's username"
                onSearch={handleSuggestions}
                onChange={handleChange}
                renderMenuItemChildren={(option, props) => (
                  <FlexRow justify='space-between'>
                    <UserMiniCard
                      avatarSrc={option.profile_pic}
                      avatarSize='small'
                      username={option.username}
                    />
                    {friendLabel(option.label)}
                  </FlexRow>
                )}
                />
              : <>
                <Form.Control type='email' placeholder="Enter your friend's email here" onChange={handleEmailChange} />
                <Form.Text className='text-muted'>
                We'll never share your friend's email, and we won't spam them or put them on a mailing list.
                </Form.Text>
                </>}
          </Form.Group>
          <Accordion.Toggle as={Button} size='sm' variant='outline-primary'>
            Cancel
          </Accordion.Toggle>
          {inviteType === 'internal'
            ? <Button type='submit' size='sm'>
            Add friend
              </Button>
            : <Button type='submit' size='sm'>
              Send invitation
              </Button>}
        </Form>
      </Accordion.Collapse>
      <Modal show={show} onHide={handleClose}>
        <Modal.Body>
          {inviteType === 'internal'
            ? <div className='text-center'>
            You've invited
              <strong> {friendInvitee} </strong>
              <div>to be friends with you.</div>
              <div>
                <small>We'll let them know!</small>
              </div>
              </div>
            : <div className='text-center'>
              You've invited
              <strong> {emailInvitee} </strong>
              <div>to join stockbets.</div>
              <div>
                <small>We'll let them know! If they accept they'll have your friend invitation waiting for them.</small>
              </div>
              </div>}
        </Modal.Body>
        <Modal.Footer className='centered'>
          <Button variant='primary' onClick={handleClose}>
            Awesome!
          </Button>
        </Modal.Footer>
      </Modal>
    </Accordion>
  )
}

export { AddFriends }
