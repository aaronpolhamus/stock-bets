import React from "react";
import styled from "styled-components";
import { UserAvatar } from "components/users/UserAvatar";

const infoBuilder = (info) => {
  return info.map((part, index) => {
    return <span key={index}>{part}</span>;
  });
};

const MiniCard = styled.div`
  display: flex;
  align-items: center;
  p {
    margin-bottom: 0;
    line-height: 1;
  }
`;
const UserData = styled.p`
  text-transform: uppercase;
  font-size: ${(props) => props.fontSize || "var(--font-size-min)"};
  color: ${(props) => props.color || "var(--color-text-gray)"};
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

const UserName = styled.p`
  color: ${(props) => props.color || "var(--color-text-gray)"};
  font-size: ${(props) => props.fontSize || "var(--font-size-normal)"};
`;

const UserInfo = styled.div`
  margin-left: var(--space-100);
`;

const UserMiniCard = ({
  name,
  username,
  avatarSrc,
  avatarSize,
  nameColor,
  nameFontSize,
  dataColor,
  dataFontSize,
  email,
  info,
}) => {
  return (
    <MiniCard title={email}>
      <UserAvatar src={avatarSrc} size={avatarSize} />
      <UserInfo>
        <UserName color={nameColor} fontSize={nameFontSize}>
          {username}
        </UserName>
        <UserData color={dataColor} fontSize={dataFontSize}>
          {info && infoBuilder(info)}
        </UserData>
      </UserInfo>
    </MiniCard>
  );
};

export { UserMiniCard };
