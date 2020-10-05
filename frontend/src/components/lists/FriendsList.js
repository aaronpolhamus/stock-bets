import React, { useEffect, useState } from 'react'
import { apiPost } from 'components/functions/api'
import { UserMiniCard } from 'components/users/UserMiniCard'
import { Button, Modal } from 'react-bootstrap'
import styled from 'styled-components'
import { UserCheck } from 'react-feather'

const FriendsListWrapper = styled.div`
`

const FriendsListList = styled.ul`
  list-style-type: none;
  padding: 0;
`

const FriendsListItem = styled.li`
  padding: var(--space-100) 0;
`

const FriendRequest = styled.p`
  font-size: var(--font-size-small);
  display: flex;
  cursor: pointer;
  align-items: center;
  justify-content: space-between;
`

const FriendsList = ({ onLoadFriends }) => {
  const [friendsData, setFriendsData] = useState({})
  const [friendRequestsData, setFriendRequestsData] = useState({})

  const [show, setShow] = useState(false)
  const [requester, setRequester] = useState('')
  const [requestRespondMessage, setRequestRespondMessage] = useState('')

  useEffect(() => {
    const getFriendsLists = async () => {
      const friends = await apiPost('get_list_of_friends')
      setFriendsData(friends)

      setFriendRequestsData(getFriendInvites)
    }

    getFriendsLists()
  }, [requestRespondMessage])

  const getFriendInvites = async () => {
    const friendRequests = await apiPost('get_list_of_friend_invites')

    onLoadFriends(friendRequests)
    setFriendRequestsData(friendRequests)
  }

  const handleRespondFriend = async (requesterUsername, decision) => {
    const respondInvite = await apiPost('respond_to_friend_request', {
      requester_username: requesterUsername,
      decision: decision
    })

    setRequestRespondMessage(respondInvite)
    setFriendRequestsData(getFriendInvites)
  }

  const handleClose = () => setShow(false)
  const handleShow = (requester) => {
    setRequestRespondMessage('')
    setRequester(requester)
    setShow(true)
  }

  const friendsListBuilder = (data) => {
    return data.map((friend, index) => {
      return (
        <FriendsListItem key={index}>
          <UserMiniCard
            avatarSrc={friend.profile_pic}
            avatarSize='small'
            username={friend.username}
            nameFontSize='var(--font-size-small)'
            nameColor='var(--color-light-gray)'
          />
        </FriendsListItem>
      )
    })
  }

  const friendRequestsBuilder = (data) => {
    return data.map((friend, index) => {
      return (
        <FriendRequest
          key={index}
          onClick={() => handleShow(friend)}
        >
          <span>
            <UserCheck
              color='var(--color-primary)'
              size={16}
              style={{
                marginRight: 'var(--space-100)',
                marginTop: '-4px'
              }}
            />
            New request from <strong>{friend}</strong>
          </span>
        </FriendRequest>
      )
    })
  }

  return (
    <FriendsListWrapper>
      {friendRequestsData.length > 0 &&
        friendRequestsBuilder(friendRequestsData)}
      <FriendsListList>
        {friendsData.length > 0 && friendsListBuilder(friendsData)}
      </FriendsListList>

      <Modal show={show} onHide={handleClose} centered>
        <Modal.Header>
          <Modal.Title>
            New friend invite from
            <strong> {requester}</strong>!
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {requestRespondMessage === ''
            ? `${requester} wants to be your friend`
            : requestRespondMessage}
        </Modal.Body>
        <Modal.Footer>
          {requestRespondMessage === '' ? (
            <>
              <Button
                variant='outline-secondary'
                onClick={() => {
                  handleRespondFriend(requester, 'declined')
                }}
              >
                Decline
              </Button>
              <Button
                variant='success'
                onClick={() => {
                  handleRespondFriend(requester, 'accepted')
                }}
              >
                Accept invite
              </Button>
            </>
          ) : (
            <Button variant='primary' onClick={handleClose}>
              Awesome!
            </Button>
          )}
        </Modal.Footer>
      </Modal>
    </FriendsListWrapper>
  )
}

export { FriendsList }
