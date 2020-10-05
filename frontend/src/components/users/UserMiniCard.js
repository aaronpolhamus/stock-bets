import React from 'react'
import styled from 'styled-components'
import { UserAvatar } from 'components/users/UserAvatar'
import PropTypes from 'prop-types'

const infoBuilder = (info) => {
  return info.map((part, index) => {
    return <span key={index}>{part}</span>
  })
}

const MiniCard = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  p {
    margin-bottom: 0;
    line-height: 1;
  }
`
const UserData = styled.p`
  text-transform: uppercase;
  font-size: ${(props) => props.fontSize || 'var(--font-size-min)'};
  color: ${(props) => props.color || 'var(--color-text-light-gray)'};
  margin-top: var(--space-50);
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

const UserName = styled.p`
  color: ${(props) => props.color || 'var(--color-text-gray)'};
  font-size: ${(props) => props.fontSize || 'var(--font-size-normal)'};
  margin-left: var(--space-100);
`

const UserInfo = styled.div`
  display: flex;
`

const UserMiniCard = ({
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
  info
}) => {
  return (
    <MiniCard title={email} className={className}>
      <UserInfo>
        <UserAvatar src={avatarSrc} size={avatarSize} />
        <UserName color={nameColor} fontSize={nameFontSize}>
          {username}
        </UserName>
      </UserInfo>
      <UserData color={dataColor} fontSize={dataFontSize}>
        {info && infoBuilder(info)}
      </UserData>
    </MiniCard>
  )
}

UserMiniCard.propTypes = {
  className: PropTypes.string,
  name: PropTypes.string,
  username: PropTypes.string,
  avatarSrc: PropTypes.string,
  avatarSize: PropTypes.string,
  nameColor: PropTypes.string,
  nameFontSize: PropTypes.string,
  dataColor: PropTypes.string,
  dataFontSize: PropTypes.string,
  email: PropTypes.string,
  info: PropTypes.array
}

export { UserMiniCard }
