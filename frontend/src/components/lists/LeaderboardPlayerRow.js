import React, { useState } from 'react'
import styled from 'styled-components'
import { UserAvatar } from 'components/users/UserAvatar'
import { SmallCaps } from 'components/textComponents/Text'
import PropTypes from 'prop-types'
import { apiPost } from 'components/functions/api'
import { AvatarFriendBadge } from 'components/ui/badges/AvatarFriendBadge'
import { ElementTooltip } from 'components/ui/ElementTooltip'
import { PlayerCard } from 'components/ui/cards/PlayerCard'

const infoBuilder = (info) => {
  return info.map((part, index) => {
    return <span key={index}>{part}</span>
  })
}

const PlayerRowWrapper = styled.div`
  display: flex;
  padding: calc(var(--space-100) + var(--space-50)) 0;
  align-items: center;
  justify-content: space-between;
  p {
    margin-bottom: 0;
    line-height: 1;
  }
`
const PlayerData = styled.p`
  text-transform: uppercase;
  font-size: ${(props) => props.$fontSize || 'var(--font-size-min)'};
  color: ${(props) => props.$color || 'var(--color-text-light-gray)'};
  margin-top: 0;
  font-weight: 500;
  text-align: right;
  span {
    &::before {
      content: "|";
      display: inline-block;
      font-weight: bold;
      color: var(--color-primary-darken);
      margin: 0 0.5em;
    }
    &:first-child::before {
      display: none;
    }
  }
`

const PlayerName = styled.p`
  color: ${(props) => props.$color || 'var(--color-text-gray)'};
  font-size: ${(props) => props.$fontSize || 'var(--font-size-normal)'};
  margin-left: var(--space-100);
  font-weight: ${props => props.$isCurrentPlayer ? 'bold' : 'normal'};
  small{
    transform: translateY(2px);
    display: inline-block;
    border: 1px solid ${(props) => props.$color || 'var(--color-text-gray)'};
    padding: 2px var(--space-100);
    border-radius: var(--space-50);
  }
`

const PlayerInfo = styled.div`
  display: flex;
`

const AvatarWrapper = styled.div`
  position: relative;
  div{
    border-radius: 50%;
    box-sizing: border-box;
    border: ${props => props.$isCurrentPlayer ? '3px solid var(--color-primary)' : ''}
  }
`

const LeaderboardPlayerRow = ({
  className,
  name,
  username,
  avatarSrc,
  avatarSize,
  nameColor,
  nameFontSize,
  dataColor,
  dataFontSize,
  email,
  isMarketIndex,
  friendStatus,
  playerCardInfo,
  leaderboardPosition,
  info
}) => {
  const isCurrentPlayer = friendStatus === 'is_you'
  const [localFriendStatus, setLocalFriendStatus] = useState(null)

  const handleFriendAdd = async (invitee) => {
    await apiPost('send_friend_request', {
      friend_invitee: invitee
    }).then((response) => {
      console.log(invitee, 'invited')
      setLocalFriendStatus('you_invited')
    })
  }
  const handleRespondFriend = async (requesterUsername, decision) => {
    await apiPost('respond_to_friend_request', {
      requester_username: requesterUsername,
      decision: decision
    }).then((response) => {
      setLocalFriendStatus(decision === 'accepted' ? 'friend' : '')
    })
  }

  return (
    <PlayerRowWrapper title={email} className={className}>
      <PlayerInfo>
        <AvatarWrapper $isCurrentPlayer={isCurrentPlayer}>
          <UserAvatar src={avatarSrc} size={avatarSize} />
          <AvatarFriendBadge
            friendStatus={localFriendStatus || friendStatus}
          />
        </AvatarWrapper>
        <ElementTooltip
          placement='left'
          message={(
            <PlayerCard
              profilePic={avatarSrc}
              username={username}
              leaderboardPosition={leaderboardPosition}
              friendStatus={localFriendStatus || friendStatus}
              playerStats={playerCardInfo}
              onFriendAdd={() => {
                handleFriendAdd(username)
              }}
              onInvitationDecline={() => {
                handleRespondFriend(username, 'declined')
              }}
              onInvitationAccept={() => {
                handleRespondFriend(username, 'accepted')
              }}
            />
          )}
        >
          <PlayerName $color={nameColor} $fontSize={nameFontSize} $isCurrentPlayer={isCurrentPlayer}>
            {isMarketIndex ? (<SmallCaps>{username}</SmallCaps>) : username}
          </PlayerName>
        </ElementTooltip>
      </PlayerInfo>
      <PlayerData $color={dataColor} $fontSize={dataFontSize}>
        {info && infoBuilder(info)}
      </PlayerData>
    </PlayerRowWrapper>
  )
}

LeaderboardPlayerRow.propTypes = {
  avatarSize: PropTypes.string,
  avatarSrc: PropTypes.string,
  dataColor: PropTypes.string,
  dataFontSize: PropTypes.string,
  email: PropTypes.string,
  friendStatus: PropTypes.string,
  info: PropTypes.array,
  isMarketIndex: PropTypes.bool,
  name: PropTypes.string,
  nameColor: PropTypes.string,
  nameFontSize: PropTypes.string,
  username: PropTypes.string,
  playerCardInfo: PropTypes.array,
  leaderboardPosition: PropTypes.string,
  className: PropTypes.string
}

export { LeaderboardPlayerRow }
