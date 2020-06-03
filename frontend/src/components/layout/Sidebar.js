import React from "react";
import styled from "styled-components";

const SidebarWrapper = styled.div`
  background-color: var(--color-secondary);
  color: var(--color-lightest);
  padding: 2rem;
  min-width: 340px;
  min-height: 100vh;
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

export { Sidebar };
