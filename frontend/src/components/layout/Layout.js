import React from "react";
import styled from "styled-components";

//Global Layout Component
const Layout = styled.div`
  display: ${(props) => props.type || "flex"};
`;

//Sidebar Component
const SidebarWrapper = styled.div`
  background-color: var(--color-secondary);
  color: var(--color-lightest);
  padding: 2rem;
  width: 320px;
  flex-shrink: 0;
  box-sizing: border-box;
  min-height: 100vh;
  border-radius: 0 1rem 0 0;
`;

const SmallColumnWrapper = styled.div`
  background-color: var(--color-light-gray);
  padding: var(--space-400);
  width: 280px;
  flex-shrink: 0;
  box-sizing: border-box;
  min-height: 100vh;
  border-radius: 0 1rem 0 0;
`;

const Logo = styled.a`
  text-transform: uppercase;
  font-weight: bold;
  color: var(--color-lightest);
  display: block;
  margin-bottom: 2.5rem;
  &:hover {
    color: inherit;
    text-decoration: none;
  }
`;

const Content = styled.div`
  padding: var(--space-400);
  flex-grow: 1;
  display: ${(props) => props.display || "block"};
  height: ${(props) => props.height || "auto"};
  align-items: ${(props) => props.alignItems || "flex-start"};
  justify-content: ${(props) => props.justifyContent || "flex-start"};
`;

const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Breadcrumb = styled.div`
  display: flex;
  margin-bottom: var(--space-200);
  font-size: var(--font-size-small);
  color: var(--color-text-gray);
  justify-content: ${(props) => props.justifyContent || "flex-start"};
  a {
    color: inherit;
  }
`;

const Sidebar = ({ children }) => (
  <SidebarWrapper>
    <Logo href="/">Stockbets</Logo>

    {children}
  </SidebarWrapper>
);

const SmallColumn = ({ children }) => (
  <SmallColumnWrapper>{children}</SmallColumnWrapper>
);

//Section Component
const PageSection = styled.section`
  margin-bottom: 4rem;
`;

export {
  Layout,
  Sidebar,
  PageSection,
  Content,
  SmallColumn,
  Header,
  Breadcrumb,
};
