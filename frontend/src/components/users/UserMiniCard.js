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
const Stats = styled.p`
  text-transform: uppercase;
  font-size: var(--font-size-min);
  color: var(--color-text-light-gray);
  span {
    display: inline-block;
    margin: 0 0.4rem 0 0.25rem;
    color: var(--color-primary-darken);
    font-weight: bold;
  }
`;

const UserMiniCard = ({ name, pictureSrc, email, stats }) => {
  return (
    <MiniCard title={email}>
      <UserAvatar src={pictureSrc} size="normal" />
      <div>
        <p>{name}</p>
        <Stats>
          Return: <strong>{stats.absoluteReturn} </strong>
          <span>|</span>
          Sharpe: <strong>{stats.sharpeRatio}</strong>
        </Stats>
      </div>
    </MiniCard>
  );
};

export { UserMiniCard };
