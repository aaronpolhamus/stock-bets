import React, { useEffect, useState } from "react";
import { isEmpty, fetchGameData } from "components/functions/api";
import {
  SimplifiedCurrency,
  AuxiliarText,
} from "components/textComponents/Text";
import styled from "styled-components";
import { UserMiniCard } from "components/users/UserMiniCard";

const SectionTitle = styled.h2`
  text-transform: uppercase;
  font-size: var(--font-size-small);
  font-weight: bold;
  letter-spacing: var(--letter-spacing-smallcaps);
`;

const UserRow = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-400);
`;
const UserStatsInfo = styled.div`
  text-align: right;
  font-weight: medium;
  color: var(--color-text-primary);
  font-size: var(--font-size-small);
  p {
    margin: var(--space-50) 0 0 0;
    line-height: 1;
  }
`;

const FieldHeader = styled.div`
  display: flex;
  justify-content: space-between;
`;

const FieldParticipants = styled.div`
  margin-top: var(--space-400);
`;

const entryBuilder = (data) => {
  return data.map((row, index) => {
    return (
      <UserRow key={index}>
        <UserMiniCard
          avatarSrc={row.profile_pic}
          avatarSize="small"
          username={row.username}
          nameFontSize="var(--font-size-small)"
          info={[`${row.stocks_held.join(", ")}`]}
        />
        <UserStatsInfo>
          <p>
            <SimplifiedCurrency value={row.portfolio_value} />
          </p>
          <p>
            <AuxiliarText>
              {row.total_return &&
                `${parseFloat(row.total_return).toFixed(3)}%`}
              <span> | </span>
              {row.sharpe_ratio && `${parseFloat(row.sharpe_ratio).toFixed(3)}`}
            </AuxiliarText>
          </p>
        </UserStatsInfo>
      </UserRow>
    );
  });
};

const PlayGameStats = ({ gameId }) => {
  const [statData, setStatData] = useState({});

  const getGameData = async () => {
    const data = await fetchGameData(gameId, "get_sidebar_stats");
    setStatData(data);
  };

  useEffect(() => {
    getGameData();
  }, [gameId]);

  console.log(statData);
  return (
    <div>
      <FieldHeader>
        <SectionTitle>The Field</SectionTitle>
        <AuxiliarText>
          {statData.days_left && statData.days_left} days left
        </AuxiliarText>
      </FieldHeader>
      <FieldParticipants>
        {statData.records && entryBuilder(statData.records)}
      </FieldParticipants>
    </div>
  );
};

export { PlayGameStats };
