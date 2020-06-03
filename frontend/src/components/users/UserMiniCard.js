import React from "react";
import styled from "styled-components";
import { UserAvatar } from "components/users/UserAvatar";

const MiniCard = styled.div`
  display: flex;
  align-items: center;
  p {
    margin-bottom: 0;
    line-height: 1;
  }
`;
const Info = styled.p`
  text-transform: uppercase;
  font-size: var(--font-size-min);
  color: var(--color-text-light-gray);
  margin-top: var(--space-50);
  span {
    &::before {
      content: "|";
      display: inline-block;
      font-weight: bold;
      color: var(--color-primary-darken);
      margin: 0 0.5em;
    }
    &:first-child::before {
      display: none;
    }
  }
`;

const UserInfo = styled.div`
  margin-left: var(--space-100);
`;

const infoBuilder = (info) => {
  return info.map((part, index) => {
    return <span>{part}</span>;
  });
};

const UserMiniCard = ({
  name,
  username,
  avatarSrc,
  avatarSize,
  email,
  info,
}) => {
  return (
    <MiniCard title={email}>
      <UserAvatar src={avatarSrc} size={avatarSize} />
      <UserInfo>
        <p>{username}</p>
        <Info>{info && infoBuilder(info)}</Info>
      </UserInfo>
    </MiniCard>
  );
};

export { UserMiniCard };
