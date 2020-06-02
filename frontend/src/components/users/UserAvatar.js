import React from "react";
import styled from "styled-components";

const handleSize = (size) => {
  switch (size) {
    default:
      return "3rem";
  }
};

const Avatar = styled.img`
  border-radius: 50%;
  width: ${({ size }) => handleSize(size)};
  height: auto;
  display: block;
  background-color: var(--color-lightest);
`;

const UserAvatar = ({ src, size }) => {
  return <Avatar src={src} alt="user avatar" />;
};

export { UserAvatar };
