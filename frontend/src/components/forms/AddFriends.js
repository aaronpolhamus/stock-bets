import React, { useState } from 'react'
import { Button, Modal, Accordion, Form } from 'react-bootstrap'
import {
  TextButton,
  AuxiliarText,
  FlexRow
} from 'components/textComponents/Text'
import { AsyncTypeahead } from 'react-bootstrap-typeahead'
import { UserPlus } from 'react-feather'
import { apiPost } from 'components/functions/api'
import { UserMiniCard } from 'components/users/UserMiniCard'
import { RadioButtons } from 'components/forms/Inputs'
import { ReactMultiEmail, isEmail } from 'react-multi-email';
import 'react-multi-email/style.css';

const AddFriends = () => {
  const [isLoading, setIsLoading] = useState(false)
  const [friendSuggestions, setFriendSuggestions] = useState([])
  const [friendInvitee, setFriendInvitee] = useState('')

  const [emails, setEmails] = useState([])

  const [show, setShow] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [inviteType, setInviteType] = useState('invite')

  const handleClose = () => setShow(false)
  const handleCloseForm = () => setShowForm(false)

  const handleFriendAdd = async (e) => {
    e.preventDefault()
    await apiPost('send_friend_request', {
      friend_invitee: friendInvitee
    })
    setShow(true)
    setShowForm(false)
  }

  const handleFriendInvite = async (e) => {
    e.preventDefault()
    await apiPost('invite_users_by_email', {
      friend_emails: emails
    })
    setShowForm(false)
    setShow(true)
  }

  const handleChange = (invitee) => {
    if (invitee[0] === undefined) return
    setFriendInvitee(invitee[0].username)
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
    <>
      <Button
        onClick={() => {
          setShowForm(true)
        }}
      >
        Invite or add friends
        <UserPlus />
      </Button>
      <Modal
        show={showForm}
        onHide={handleCloseForm}
        centered
      >
        <Modal.Header>
          <Modal.Title>
            Invite or add friends
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <RadioButtons
            options={{
              invite: 'Invite friends by mail',
              add: 'Add a friend by username'
            }}
            name='invite_type'
            defaultChecked={inviteType}
            onClick={(e) => {
              setInviteType(e.target.value)
            }}
          />
          { inviteType === 'invite'
            ? (
              <Form onSubmit={handleFriendInvite}>
                <ReactMultiEmail
                  autocomplete='off' 
                  autocorrect='off' 
                  autocapitalize='off' 
                  placeholder='After entering an email, add another one with the tab or comma keys'
                  emails={emails}
                  onChange={(_emails)=>{
                    setEmails(_emails)
                  }}
                  validateEmail={email => {
                    return isEmail(email); 
                  }}
                  getLabel={(
                    email: string,
                    index: number,
                    removeEmail: (index: number) => void,
                  ) => {
                    return (
                      <div data-tag key={index}>
                        {email}
                        <span data-tag-handle onClick={() => removeEmail(index)}>
                          ×
                        </span>
                      </div>
                    );
                  }}
                />
                <Form.Text className='text-muted'>
                  We&apos;ll never share your friend&apos;s email, and we won&apos;t spam them or put them on a mailing list.
                </Form.Text>
                <Button type='submit'>
                  Send invitation
                </Button>
              </Form>
            )
            : (
              <Form onSubmit={handleFriendAdd}>
                <Form.Group>
                  <AsyncTypeahead
                    id='typeahead-particpants'
                    name='invitees'
                    labelKey='username'
                    isLoading={isLoading}
                    options={friendSuggestions}
                    placeholder='Type your friend&apos;s username'
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
                </Form.Group>
                <Button type='submit'>
                  Add friend
                </Button>
              </Form>
            )
          }

        </Modal.Body>
      </Modal>
      <Modal show={show} onHide={handleClose}>
        <Modal.Body>
          {inviteType === 'invite'
            ? (
              <div className='text-center'>
                          You&apos;ve invited
                <strong> {emails.join(', ')} </strong>
                <div>to join stockbets.</div>
                <div>
                  <small>We&apos;ll let them know! If they accept they&apos;ll have your friend invitation waiting for them.</small>
                </div>
              </div>)
            : (<div className='text-center'>
                        You&apos;ve invited
              <strong> {friendInvitee} </strong>
              <div>to be friends with you.</div>
              <div>
                <small>We&apos;ll let them know!</small>
              </div>
            </div>)
          }
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

export { AddFriends }
