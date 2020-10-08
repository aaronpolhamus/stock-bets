import React from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { Check } from 'react-feather'

const AvatarIcon = styled.i`
  width: ${props => `${props.$size}px`};
  height: ${props => `${props.$size}px`};
  background-color: ${props => props.$color || 'var(--color-success-darken)'};
  display: block;
  position: absolute;
  bottom: -1px;
  right: -4px;
  border-radius: 50%;
  svg{
    position: absolute;
    top: 21%;
    left: 18%;
  }
`

const AvatarFriendBadge = ({ friendStatus, size = 16 }) => {
  switch (friendStatus) {
    case 'friend':
      return (
        <AvatarIcon title={friendStatus} $size={size}>
          <Check size={size * 0.7} color='#fff' strokeWidth='4px' />
        </AvatarIcon>
      )
    case 'you_invited':
      return (
        <AvatarIcon $color='var(--color-auxiliar-purple)' title={friendStatus} $size={size}>
          <Check size={size * 0.7} color='#fff' strokeWidth='4px' />
        </AvatarIcon>
      )
    case 'they_invited':
      return (
        <AvatarIcon $color='var(--color-primary-darken)' title={friendStatus} $size={size}>
          <Check size={size * 0.7} color='#fff' strokeWidth='4px' />
        </AvatarIcon>
      )
    default:
      return (
        null
      )
  }
}

AvatarFriendBadge.propTypes = {
  friendStatus: PropTypes.string,
  size: PropTypes.number
}

export { AvatarFriendBadge }
