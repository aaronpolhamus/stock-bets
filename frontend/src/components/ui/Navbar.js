import React from 'react'
import styled from 'styled-components'
import { Logo } from 'components/ui/Logo'
import PropTypes from 'prop-types'
import { HomeButton } from 'components/ui/buttons/HomeButton'
// Global Layout Component

const NavbarWrapper = styled.nav`
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: var(--space-800);
`
const NavbarLeft = styled.div`
  display: flex;
  align-items: center;
  .logo{
    margin-top: -2px;
  }
`
const NavbarRight = styled.div`
  display: flex;
  align-items: center;
`

const Navbar = ({ itemsRight, itemsLeft, homeButton = true }) => {
  return (
    <NavbarWrapper>
      <NavbarLeft>
        <Logo/>
        {homeButton &&
          <HomeButton/>
        }
        {itemsLeft}
      </NavbarLeft>
      {itemsRight !== undefined &&
        (<NavbarRight>
          {itemsRight}
        </NavbarRight>)
      }
    </NavbarWrapper>
  )
}

Navbar.propTypes = {
  homeButton: PropTypes.bool,
  itemsRight: PropTypes.oneOfType([
    PropTypes.func,
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ]),
  itemsLeft: PropTypes.oneOfType([
    PropTypes.func,
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ])
}

export { Navbar }
