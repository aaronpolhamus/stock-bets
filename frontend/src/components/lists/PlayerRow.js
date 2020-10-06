import React from 'react'
import styled from 'styled-components'
import { UserAvatar } from 'components/users/UserAvatar'
import { SmallCaps } from 'components/textComponents/Text'
import PropTypes from 'prop-types'
import { Check } from 'react-feather'

const infoBuilder = (info) => {
  return info.map((part, index) => {
    return <span key={index}>{part}</span>
  })
}

const PlayerRowWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  p {
    margin-bottom: 0;
    line-height: 1;
  }
`
const PlayerData = styled.p`
  text-transform: uppercase;
  font-size: ${(props) => props.fontSize || 'var(--font-size-min)'};
  color: ${(props) => props.color || 'var(--color-text-light-gray)'};
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
  color: ${(props) => props.color || 'var(--color-text-gray)'};
  font-size: ${(props) => props.fontSize || 'var(--font-size-normal)'};
  margin-left: var(--space-100);
  small{
    transform: translateY(2px);
    display: inline-block;
    border: 1px solid ${(props) => props.color || 'var(--color-text-gray)'};
    padding: 2px var(--space-100);
    border-radius: var(--space-50);
  }
`

const PlayerInfo = styled.div`
  display: flex;
`

const AvatarWrapper = styled.div`
  position: relative;
  i{
    width: 16px;
    height: 16px;
    background-color: var(--color-success-darken);
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
  } 
`

const PlayerRow = ({
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
  isFriend,
  info
}) => {
  return (
    <PlayerRowWrapper title={email} className={className}>
      <PlayerInfo>
        <AvatarWrapper>
          <UserAvatar src={avatarSrc} size={avatarSize} />
          {isFriend
            ? (
              <i>
                <Check size={11} color='#fff' strokeWidth='4px'/>
              </i>
            )
            : null
          }
        </AvatarWrapper>
        <PlayerName color={nameColor} fontSize={nameFontSize}>
          {isMarketIndex ? (<SmallCaps>{username}</SmallCaps>) : username}
        </PlayerName>
      </PlayerInfo>
      <PlayerData color={dataColor} fontSize={dataFontSize}>
        {info && infoBuilder(info)}
      </PlayerData>
    </PlayerRowWrapper>
  )
}

PlayerRow.propTypes = {
  className: PropTypes.string,
  name: PropTypes.string,
  username: PropTypes.string,
  avatarSrc: PropTypes.string,
  avatarSize: PropTypes.string,
  isMarketIndex: PropTypes.bool,
  isFriend: PropTypes.bool,
  nameColor: PropTypes.string,
  nameFontSize: PropTypes.string,
  dataColor: PropTypes.string,
  dataFontSize: PropTypes.string,
  email: PropTypes.string,
  info: PropTypes.array
}

export { PlayerRow }
