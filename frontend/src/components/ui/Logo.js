import React from 'react'
import { ReactComponent as SvgLogo } from 'assets/logo-bright.svg'
import styled from 'styled-components'

const LogoWrapper = styled.a`
  text-transform: uppercase;
  font-weight: bold;
  color: var(--color-lightest);
  display: block;
  margin-bottom: 0;
  &:hover {
    color: inherit;
    text-decoration: none;
  }
`

const Logo = () => {
  return (
    <LogoWrapper href='/' title='Stockbets'>
      <SvgLogo />
    </LogoWrapper>
  )
}

export { Logo }
