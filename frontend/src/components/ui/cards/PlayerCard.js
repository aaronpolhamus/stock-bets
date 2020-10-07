import React, { useState } from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { UserAvatar } from 'components/users/UserAvatar'
import {
  Button
} from 'react-bootstrap'
import { Check } from 'react-feather'
import { apiPost } from 'components/functions/api'

const PlayerCardWrapper = styled.div`
  width: 100%;
  cursor: default;
  user-select: text;
  header {
    display: flex;
    align-items: center;
  }
  h2{
    color: var(--color-text-primary);
    font-weight: bold;
    font-size: var(--font-size-normal);
    margin-bottom: 0;
    margin-left: var(--space-100);
    small {
      display: block;
      color: var(--color-success);
    }
  }
  header{
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  width: 14rem;
  z-index: 2;
`
const PlayerInfo = styled.ul`
  list-style-type: none;
  padding: var(--space-200) 0;
  margin: 0 0 var(--space-200) 0;
  color: var(--color-text-gray);
  border-bottom: 1px solid var(--color-light-gray);
  li {
    display: flex;
    justify-content: space-between;
  }
  strong {
    color: var(--color-text-primary)
  }
`

const AvatarWrapper = styled.div`
  position: relative;
`
const AvatarIcon = styled.i`
  width: 16px;
  height: 16px;
  background-color: ${props => props.$color || 'var(--color-success-darken)'};
  display: block;
  position: absolute;
  bottom: -1px;
  right: -4px;
  border-radius: 50%;
  svg{
    position: absolute;
    top: 4px;
    left: 3px;
  }
`

const PlayerCard = ({ children, username, profilePic, leaderboardPosition, isFriend, playerStats }) => {
  const [friendStatus, setFriendStatus] = useState(isFriend)

  const handleFriendAdd = async (invitee) => {
    await apiPost('send_friend_request', {
      friend_invitee: invitee
    }).then((response) => {
      setFriendStatus('invited')
    })
  }
  const playerStatsList = (playerStats) => {
    return playerStats.map((row, index) => {
      return (
        <li key={index}>
          {row.type}
          <strong>{row.value}</strong>
        </li>
      )
    })
  }

  const renderFriendActions = (friendStatus) => {
    switch (friendStatus) {
      case true:
        return (<p>You&apos;re friends!</p>)
      case false:
        return (
          <Button
            size='sm'
            onClick={() => {
              handleFriendAdd(username)
            }}
          >
            Add friend
          </Button>
        )
      default:
        return (<p>Invitation Sent!</p>)
    }
  }

  const renderFriendBadge = (friendStatus) => {
    switch (friendStatus) {
      case true:
        return (
          <AvatarIcon>
            <Check size={11} color='#fff' strokeWidth='4px' />
          </AvatarIcon>
        )
      case false:
        return (
          null
        )
      default:
        return (
          <AvatarIcon $color='var(--color-auxiliar-purple)'>
            <Check size={11} color='#fff' strokeWidth='4px' />
          </AvatarIcon>
        )
    }
  }

  return (
    <PlayerCardWrapper>
      <header>
        <AvatarWrapper>
          <UserAvatar src={profilePic} size='big' />
          {renderFriendBadge(friendStatus)}
        </AvatarWrapper>
        {renderFriendActions(friendStatus)}
      </header>
      <h2>
        <span>
          {leaderboardPosition} {username}
        </span>
      </h2>
      {playerStats !== undefined &&
        (
          <PlayerInfo>
            {playerStatsList(playerStats)}
          </PlayerInfo>
        )
      }
      {children}
    </PlayerCardWrapper>
  )
}

PlayerCard.propTypes = {
  username: PropTypes.string,
  profilePic: PropTypes.string,
  leaderboardPosition: PropTypes.number,
  isFriend: PropTypes.bool,
  playerStats: PropTypes.array,
  children: PropTypes.oneOfType([
    PropTypes.func,
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ])
}

export { PlayerCard }
