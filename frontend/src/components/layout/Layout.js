import React from "react";
import styled from "styled-components";

//Global Layout Component
const typeHandler = (type) => {
  switch (type) {
    default:
  }
};
const LayoutWrapper = styled.div`
  display: flex;
`;

const Layout = ({ type, children }) => {
  return <LayoutWrapper>{children}</LayoutWrapper>;
};

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
`;

const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
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

export { Layout, Sidebar, PageSection, Content, SmallColumn, Header };
