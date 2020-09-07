import React from 'react'
import styled from 'styled-components'

const Icon = styled.span`
  display: inline-block;
  margin-right: var(--space-100);
  svg{
    width: 16px;
    height: 16px;
    stroke-width: 2px;
  }
`

const IconTabs = ({ children }) => {
  return (
    <Icon>
      {children}
    </Icon>
  )
}

export { IconTabs }
