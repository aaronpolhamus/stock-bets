import React from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { UserAvatar } from 'components/users/UserAvatar'
import {
  Button
} from 'react-bootstrap'
import { AvatarFriendBadge } from 'components/ui/badges/AvatarFriendBadge'
import { SmallCaps } from 'components/textComponents/Text'

const PlayerCardWrapper = styled.div`
  width: 100%;
  cursor: default;
  user-select: text;
  header {
    display: flex;
    align-items: center;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--color-light-gray);
    margin-bottom: var(--space-200);
  }
  h2{
    color: var(--color-text-primary);
    font-weight: bold;
    font-size: var(--font-size-normal);
    margin-bottom: 0;
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
  
  width: 15rem;
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
  margin-right: var(--space-200);
`

const CardStatus = styled.p`
  font-weight: bold;
  color: ${props => props.$color || 'initial'}
`
const CardMessage = styled.p`
  line-height: 1.2;
  margin-bottom: var(--space-100);
`

const PlayerPosition = styled.p`
  color: var(--color-text-gray);
`

const PlayerCard = ({
  children,
  username,
  profilePic,
  leaderboardPosition,
  friendStatus,
  playerStats,
  onFriendAdd,
  onInvitationAccept,
  onInvitationDecline
}) => {
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
      case 'friend':
        return (
          <CardStatus $color='var(--color-success-darken)'>
            You&apos;re friends!
          </CardStatus>
        )
      case 'you_invited':
        return (
          <CardStatus $color='var(--color-auxiliar-purple)'>
            Invitation Sent!
          </CardStatus>
        )
      case 'they_invited':
        return (
          <div>
            <CardMessage>{username} sent you a friend invitation:</CardMessage>
            <p>
              <Button
                size='sm'
                variant='outline-secondary'
                onClick={onInvitationDecline}
              >
                Decline
              </Button>
              <Button
                size='sm'
                variant='success'
                onClick={onInvitationAccept}
              >
                Accept
              </Button>
            </p>
          </div>
        )
      case 'is_you':
        return (null)
      default:
        return (
          <Button
            size='sm'
            onClick={onFriendAdd}
          >
            Send friend invitation
          </Button>
        )
    }
  }

  return (
    <PlayerCardWrapper>
      <header>
        <AvatarWrapper>
          <UserAvatar src={profilePic} size='big' />
          <AvatarFriendBadge
            size={24}
            friendStatus={friendStatus}
          />
        </AvatarWrapper>
        {renderFriendActions(friendStatus)}
      </header>
      <h2>
        <span>
          {username}
        </span>
      </h2>
      <PlayerPosition>
        <SmallCaps>
          {leaderboardPosition} place global
        </SmallCaps>
      </PlayerPosition>
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
  leaderboardPosition: PropTypes.string,
  friendStatus: PropTypes.string,
  playerStats: PropTypes.array,
  onFriendAdd: PropTypes.func,
  children: PropTypes.oneOfType([
    PropTypes.func,
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ])
}

export { PlayerCard }
