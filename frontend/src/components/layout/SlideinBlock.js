import React, { useState } from 'react'
import PropTypes from 'prop-types'
import { breakpoints } from 'design-tokens'
import styled from 'styled-components'

const Icon = styled.div`
  @media screen and (min-width: ${props => props.$breakpoint}){
    display: none;
  }
`
const Content = styled.div`
  position: relative;
  @media screen and (max-width: ${props => props.$breakpoint}){
    position: fixed;
    box-shadow: ${props => props.$show ? '-50px 0px 50px rgba(17, 7, 60, 0.5)' : '0'};
    background-color: ${props => props.$backgroundColor || '#fff'};
    top: 0;
    right: ${props => props.$show ? 0 : '-90vw'};
    height: 100vh;
    transition: right .2s ease-out;
    width: 90vw;
    z-index: 1;
    padding: var(--space-500) var(--space-300);
  }
`
const CloseButton = styled.button`
  appearance: none;
  border: none;
  background-color: transparent;
  position: absolute;
  top: var(--space-300);
  right: var(--space-100);
  @media screen and (min-width: ${props => props.$breakpoint}){
    display: none;
  }
`

const SlideinBlock = ({ children, icon, context, className, backgroundColor, iconClose }) => {
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
        </Icon>}
      <Content
        $breakpoint={breakpoint}
        $backgroundColor={backgroundColor}
        $show={showBlock}
      >
        <CloseButton
          $breakpoint={breakpoint}
          onClick={toggleShowBlock}
        >
          {iconClose || 'x'}
        </CloseButton>
        {children}

      </Content>
    </div>
  )
}

SlideinBlock.propTypes = {
  icon: PropTypes.node,
  iconClose: PropTypes.node,
  // In which screen size it behaves like a sliding block
  context: PropTypes.string,
  backgroundColor: PropTypes.string,
  children: PropTypes.node,
  className: PropTypes.string
}

export { SlideinBlock }
