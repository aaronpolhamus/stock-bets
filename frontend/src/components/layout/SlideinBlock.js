import React from 'react'
import PropTypes from 'prop-types'
import { breakpoints } from 'components/layout/Breakpoints'
import styled from 'styled-components'

const Icon = styled.div`
  @media screen and (min-width: ${breakpoints.md}){
    display: none;
  }
`

const SlideinBlock = ({ children, icon, context, className }) => {
  return (
    <div>
      {icon &&
        <Icon $context={context}>
          {icon}
        </Icon>
      }

      {children}
    </div>
  )
}

SlideinBlock.propTypes = {
  icon: PropTypes.node,
  context: PropTypes.string,
  children: PropTypes.node,
  className: PropTypes.string
}

export { SlideinBlock }
