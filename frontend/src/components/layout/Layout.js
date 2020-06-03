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
  min-width: 340px;
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

const Sidebar = ({ children }) => (
  <SidebarWrapper>
    <Logo href="/">Stockbets</Logo>

    {children}
  </SidebarWrapper>
);

//Section Component
const PageSection = styled.section`
  margin-bottom: 4rem;
`;

export { Layout, Sidebar, PageSection };
