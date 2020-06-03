import React from "react";
import styled from "styled-components";

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

export { Layout };
