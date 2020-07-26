import React, {useEffect, useState} from 'react'
import {Button, Form, Modal} from 'react-bootstrap'
import {AuxiliarText, FlexRow} from 'components/textComponents/Text'
import {AsyncTypeahead, Typeahead} from 'react-bootstrap-typeahead'
import {UserPlus} from 'react-feather'
import {apiPost} from 'components/functions/api'
import {UserMiniCard} from 'components/users/UserMiniCard'
import {RadioButtons} from 'components/forms/Inputs'
import {isEmail, ReactMultiEmail} from 'react-multi-email';
import 'react-multi-email/style.css';
import PropTypes from 'prop-types'
import styled from "styled-components";
import {breakpoints} from "../../design-tokens";
import {Tooltip} from "./Tooltips";

const AddFriends = ({variant}) => {
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
        variant={variant}
      >
        Invite or add friends
        <UserPlus 
          color='var(--color-secondary)' 
          size={18}
          style={{
            marginLeft: 'var(--space-100)'
          }}
        />
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
                  placeholder='Separate multiple emails with a comma or tab'
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

AddFriends.propTypes = {
  variant: PropTypes.string
}

const StyledTypeahead = styled(Typeahead)`
  
  .rbt-input-wrapper {
    display: flex;
  }
  .rbt-input-wrapper div {
    
  }
  .rbt-input-wrapper [option] {
    font-size: var(--font-size-small);
    background-color: var(--color-light-gray);
    padding: 0 var(--space-100);
    border-radius: var(--space-50);
    margin-right: var(--space-50);
    button{
      margin-right: var(--space-50);
    }
  }
`

const MultiInvite = ({availableInvitees, handleInviteesChange, handleEmailsChange}) => {
  return <>
    <Form.Group>
      <Form.Label>
        Add competitors with username
        <Tooltip
          message="Which of your friends do you want to invite to this game? If you haven't added friends, yet, do this first."
        />
      </Form.Label>
      <StyledTypeahead
        id='typeahead-particpants'
        name='invitees'
        labelKey='name'
        multiple
        options={
          availableInvitees &&
          Object.values(availableInvitees)
        }
        placeholder="Who's playing?"
        onChange={handleInviteesChange}
      />
    </Form.Group>
    <Form.Group>
      <Form.Label>
        Add competitors with email
        <Tooltip
          message="Email a friend a game invitation. If they're not on the platform already we'll walk them through onboarding, and they'll have your invitation waiting for them."
        />
      </Form.Label>

      <ReactMultiEmail
        autocomplete='off'
        autocorrect='off'
        autocapitalize='off'
        placeholder='Separate multiple emails with a comma or tab'
        onChange={handleEmailsChange}
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
    </Form.Group>
  </>;
}

export { AddFriends, MultiInvite }