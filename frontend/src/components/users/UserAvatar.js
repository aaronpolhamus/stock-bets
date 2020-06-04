import React from "react";
import styled from "styled-components";

const handleSize = (size) => {
  switch (size) {
    case "small":
      return "1.5rem";
    default:
      return "3rem";
  }
};

const Avatar = styled.img`
  border-radius: 50%;
  width: ${({ size }) => handleSize(size)};
  height: ${({ size }) => handleSize(size)};
  display: block;
  background-color: var(--color-lightest);
`;

const UserAvatar = ({ src, size }) => {
  return <Avatar src={src} alt="user avatar" size={size} />;
};

export { UserAvatar };
