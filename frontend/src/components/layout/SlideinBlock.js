import React, { useState } from 'react'
import PropTypes from 'prop-types'
import { breakpoints } from 'components/layout/Breakpoints'
import styled from 'styled-components'

const Icon = styled.div`
  @media screen and (min-width: ${props => props.$breakpoint}){
    display: none;
  }
`
const Content = styled.div`

  @media screen and (max-width: ${props => props.$breakpoint}){
    position: fixed;
    background-color: ${props => props.$backgroundColor || '#fff'};
    top: 0;
    right: ${props => props.$show ? 0 : '-80vw'};
    height: 100vh;
    transition: right .2s ease-out;
    width: 80vw;
    z-index: 1;
    padding: var(--space-500) var(--space-300);
  }
`

const SlideinBlock = ({ children, icon, context, className, backgroundColor }) => {
  const [showBlock, setShowBlock] = useState(false)

  const toggleShowBlock = () => {
    if (showBlock) {
      setShowBlock(false)
    } else {
      setShowBlock(true)
    }
  }

  const breakpoint = breakpoints[context] || 0

  return (
    <div>
      {icon &&
        <Icon
          $breakpoint={breakpoint}
          onClick={toggleShowBlock}
        >
          {icon}
        </Icon>
      }
      <Content
        $breakpoint={breakpoint}
        $backgroundColor={backgroundColor}
        $show={showBlock}>

        {children}

      </Content>
    </div>
  )
}

SlideinBlock.propTypes = {
  icon: PropTypes.node,
  // In which screen size it behaves like a sliding block
  context: PropTypes.string,
  backgroundColor: PropTypes.string,
  children: PropTypes.node,
  className: PropTypes.string
}

export { SlideinBlock }
