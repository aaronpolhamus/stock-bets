import React from 'react'
import styled from 'styled-components'

const handleSize = (size) => {
  switch (size) {
    case 'xsmall':
      return '1rem'
    case 'small':
      return '1.5rem'
    default:
      if (size === undefined) return '3rem'
      return size
  }
}

const Avatar = styled.div`
  border-radius: 50%;
  width: ${({ size }) => handleSize(size)};
  height: ${({ size }) => handleSize(size)};
  flex: 0 0 ${({ size }) => handleSize(size)};
  display: block;
  background-color: var(--color-light-gray);
  overflow: hidden;
  img {
    display: block;
    object-fit: cover;
    width: 100%;
    height: 100%;
  }
`

const UserAvatar = ({ src, size }) => {
  if (src) {
    return (
      <Avatar size={size}>
        <img src={src} alt='Avatar' />
      </Avatar>
    )
  }
  return <Avatar size={size} />
}

export { UserAvatar }
