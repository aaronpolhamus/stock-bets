import React from 'react'
import styled from 'styled-components'
import { Container, Col, Row } from 'react-bootstrap'
import { breakpoints } from 'components/layout/Breakpoints'
// Global Layout Component
const StyledContainer = styled(Container)`
  padding: 0;
`

// Sidebar Component
const SidebarWrapper = styled(Col)`
  background-color: var(--color-secondary);
  color: var(--color-lightest);
  box-sizing: border-box;
  box-shadow: 4px 0px 10px rgba(17, 7, 60, 0.3),
    2px 2px 3px rgba(61, 50, 106, 0.3);

  @media screen and (min-width: ${breakpoints.md}){
    border-radius: 0 1rem 0 0;
    min-height: 100vh;
    position: sticky;
    top: 0;
    align-self: flex-start;
  }
`

const SmallColumnWrapper = styled(Col)`
  background-color: var(--color-light-gray);
  min-height: 100vh;
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

const Content = styled.div`
  padding: ${(props) => props.padding || 'var(--space-400)'};
  display: ${(props) => props.display || 'block'};
  height: ${(props) => props.height || 'auto'};
  align-items: ${(props) => props.alignItems || 'flex-start'};
  justify-content: ${(props) => props.justifyContent || 'flex-start'};
`

const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: ${(props) => props.alignItems || 'center'};
  margin-bottom: ${(props) => props.marginBottom || 0};
  h2{
    flex-shrink: 0;
    margin-right: var(--space-200)
  }
`

const Breadcrumb = styled.div`
  display: flex;
  margin-bottom: var(--space-200);
  font-size: var(--font-size-small);
  color: var(--color-text-gray);
  justify-content: ${(props) => props.justifyContent || 'flex-start'};
  a {
    color: inherit;
  }
`

const SidebarSection = styled.div`
  margin-bottom: var(--space-500);
`

// Section Component
const PageSection = styled.section`
  margin-bottom: var(--space-600);
`

const ColContent = styled.div`
  padding: var(--space-200);
  @media screen and (min-width: ${breakpoints.md}){
    padding: var(--space-400);
  }
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
    <ColContent>
      <Logo href='/'>Stockbets</Logo>

      {children}
    </ColContent>
  </SidebarWrapper>
)

const SmallColumn = ({ children, ...props }) => (
  <SmallColumnWrapper {...props}>
    <ColContent>
      {children}
    </ColContent>
  </SmallColumnWrapper>
)

const Layout = ({ children }) => (
  <StyledContainer fluid>
    <Row noGutters>{children}</Row>
  </StyledContainer>
)

export {
  Breadcrumb,
  Column,
  Content,
  Header,
  Layout,
  PageSection,
  Sidebar,
  SidebarSection,
  SmallColumn
}
