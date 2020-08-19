import React from 'react'
import styled from 'styled-components'
import { Container, Col, Row } from 'react-bootstrap'
import { breakpoints } from 'design-tokens'
// Global Layout Component
const Breadcrumb = styled.div`
  display: flex;
  font-size: var(--font-size-small);
  position: relative;
  button, a {
    color: var(--color-primary-darken);
    position: absolute;
    top: -5.6rem;
    right: 0;
  }
  justify-content: ${(props) => props.justifyContent || 'flex-start'};
  span {
    display: none; 
  }
  svg {
    stroke: currentColor;
    width: 24px;
    height: 24px;
  }
  @media screen and (min-width: ${breakpoints.md}){
    margin-bottom: var(--space-200);
    button, a{
      position: static;
      color: var(--color-text-gray);
    }
    span {
      display: inline;
    }
    svg {
      width: inherit;
      height: inherit;
    }
  }
`

const ColContent = styled.div`
  padding: var(--space-300);
  position: relative;
  @media screen and (min-width: ${breakpoints.md}){
    padding: var(--space-400);
  }
`

const Content = styled.div`
  padding: ${(props) => props.padding || 'var(--space-400)'};
  position: relative;
  display: ${(props) => props.display || 'block'};
  height: ${(props) => props.height || 'auto'};
  min-height: ${(props) => props.minHeight || 0};
  flex-wrap: wrap;
  align-items: ${(props) => props.alignItems || 'flex-start'};
  justify-content: ${(props) => props.justifyContent || 'flex-start'};
  overflow: hidden;
  @media screen and (max-width: ${breakpoints.md}){
    padding: var(--space-200);
  }
`

const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: ${(props) => props.alignItems || 'center'};
  flex-wrap: wrap;
  margin-bottom: ${(props) => props.marginBottom || 0};
  h2{
    flex-shrink: 0;
    margin-right: var(--space-200)
  }
`

const Logo = styled.a`
  text-transform: uppercase;
  font-weight: bold;
  color: var(--color-lightest);
  display: block;
  margin-bottom: 1.2rem;
  &:hover {
    color: inherit;
    text-decoration: none;
  }
`
const PageSection = styled.section`
  margin-bottom: ${props => props.$marginBottom || 'var(--space-600)'};
  &:last-of-type{
    margin-bottom: 0;
  }
  @media screen and (min-width: ${breakpoints.md}){
    margin-bottom: ${props => props.$marginBottomMd || 'var(--space-800)'};
  }
`

const PageFooter = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-200);
`

const SidebarWrapper = styled(Col)`
  color: var(--color-lightest);
  box-sizing: border-box;
  &::before {
    content: '';
    display: block;
    position: absolute;
    width: 50%;
    height: 100%;
    border-radius: 0 0 100%;
    background-color: var(--color-secondary);
    z-index: -1;
  }

  & + [class*="col-"] {
    padding-bottom: var(--space-lg-200)
  }

  @media screen and (min-width: ${breakpoints.md}){
    box-shadow: 4px 0px 10px rgba(17, 7, 60, 0.3),
    2px 2px 3px rgba(61, 50, 106, 0.3);
    background-color: var(--color-secondary);
    border-radius: 0 var(--space-200) 0 0;
    min-height: 100vh;
    position: sticky;
    top: 0;
    align-self: flex-start;
    & + [class*="col-"] {
      padding-bottom: var(--space-lg-400)
    }
  }
`

const SidebarContent = styled.div`
  padding: var(--space-300);
  display: flex;
  width: 87vw;
  justify-content: space-between;
  @media screen and (min-width: ${breakpoints.md}){
    display: block;
    width: 100%;
    padding: var(--space-400);
  }
`

const SidebarSection = styled.div`
  margin-bottom: var(--space-500);
`

const SmallColumnWrapper = styled(Col)`
  background-color: var(--color-light-gray);
  min-height: 100vh;
`
const StyledContainer = styled(Container)`
  padding: 0;
  min-height: 100vh;
  @media screen and (max-width: ${breakpoints.md}){
    overflow: hidden;
    padding-bottom: 10vh;
  }
`

const ModalOverflowControls = styled.div`
  text-align: center;
  padding: var(--space-300);
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  transform: translateY(100%);
`

const Column = ({ children, ...props }) => (
  <Col {...props}>
    <ColContent>
      {children}
    </ColContent>
  </Col>
)

const Sidebar = ({ children, size, ...props }) => (
  <SidebarWrapper size={size} {...props}>
    <SidebarContent>
      <Logo href='/'>Stockbets</Logo>

      {children}
    </SidebarContent>
  </SidebarWrapper>
)

const SmallColumn = ({ children, ...props }) => (
  <SmallColumnWrapper {...props}>
    <ColContent>
      {children}
    </ColContent>
  </SmallColumnWrapper>
)

const Layout = ({ children, className }) => (
  <StyledContainer fluid className={className}>
    <Row noGutters>{children}</Row>
  </StyledContainer>
)

export {
  Breadcrumb,
  Column,
  Content,
  Header,
  Layout,
  ModalOverflowControls,
  PageSection,
  PageFooter,
  Sidebar,
  SidebarSection,
  SmallColumn
}
