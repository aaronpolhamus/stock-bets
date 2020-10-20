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
  padding: 0 var(--space-300) var(--space-300);
  position: relative;
  @media screen and (min-width: ${breakpoints.md}){
    padding: 0 var(--space-400) var(--space-400);
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

  @media screen and (min-width: ${breakpoints.md}){
    & > * {
      margin-bottom: 0;
    }
  }
`

const PageSection = styled.section`
  padding-top: ${props => props.$marginBottomMd || 'var(--space-200)'};
  padding-bottom: ${props => props.$paddingBottom || 'var(--space-400)'};
  @media screen and (min-width: ${breakpoints.md}){
    padding-top: ${props => props.$marginBottomMd || 'var(--space-200)'};
    padding-bottom: ${props => props.$paddingBottomMd || 'var(--space-400)'};
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

  & + [class*="col-"] {
    padding-bottom: var(--space-lg-200)
  }

  @media screen and (min-width: ${breakpoints.md}){
    box-shadow: 4px 0px 10px rgba(17, 7, 60, 0.3),
    2px 2px 3px rgba(61, 50, 106, 0.3);
    background-color: var(--color-secondary-dark);
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
  padding: 0 var(--space-300);
  display: flex;
  width: 87vw;
  justify-content: space-between;
  @media screen and (min-width: ${breakpoints.md}){
    display: block;
    width: 100%;
    padding: 0 var(--space-400) 0;
  }
`

const SidebarSection = styled.div`
  background-color: ${props => props.$backgroundColor || 'transparent'};
  margin: 0 calc(var(--space-400) * -1);
  padding: 0 var(--space-400) var(--space-300);
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
    padding-top: 0;
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

const Column = ({ children, className, ...props }) => (
  <Col className={className} {...props}>
    <ColContent>
      {children}
    </ColContent>
  </Col>
)

const Sidebar = ({ children, className, ...props }) => (
  <SidebarWrapper className={className} {...props}>
    <SidebarContent>
      {children}
    </SidebarContent>
  </SidebarWrapper>
)

const GameContent = styled(Column)`
  padding-top: 0;
  @media screen and (min-width: ${breakpoints.md}){
    width: 100%;
    flex-basis: 100%;
    max-width: calc(100% - var(--sidebar-size));
  }
`

const GameSidebar = styled(Sidebar)`
  @media screen and (min-width: ${breakpoints.md}){
    flex-basis: var(--sidebar-size);
    max-width: none;
    order: 2;
  }
`
const HomeSidebar = styled(Sidebar)`
  @media screen and (min-width: ${breakpoints.md}){
    padding-bottom: var(--space-700);
    max-height: 100vh;
    overflow-y: auto;
    flex-basis: var(--sidebar-size);
    max-width: none;
    order: 2;
  }
`

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
  GameContent,
  GameSidebar,
  HomeSidebar,
  Header,
  Layout,
  ModalOverflowControls,
  PageSection,
  PageFooter,
  Sidebar,
  SidebarSection,
  SmallColumn
}
