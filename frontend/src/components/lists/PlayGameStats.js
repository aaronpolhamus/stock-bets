import React, { useEffect, useState } from "react";
import { Card, Row, Col } from "react-bootstrap";
import { fetchGameData } from "components/functions/api";
import styled from "styled-components";
import { UserMiniCard } from "components/users/UserMiniCard";

const SectionTitle = styled.h2`
  text-transform: uppercase;
  font-size: var(--font-size-small);
  font-weight: bold;
  letter-spacing: var(--letter-spacing-smallcaps);
`;

const entryBuilder = (data) => {
  return data.map((row, index) => {
    return (
      <div>
        <UserMiniCard
          avatarSrc={row.profile_pic}
          avatarSize="small"
          username={row.username}
          nameFontSize="var(--font-size-small)"
          info={[`${row.stocks_held.join(", ")}`]}
        />
        <p title="Portfolio Value">${Math.round(row.portfolio_value, 10)}</p>
        <p>
          <span>
            {row.total_return && `${parseFloat(row.total_return).toFixed(3)}%`}
          </span>
          <span>
            {row.sharpe_ratio && `${parseFloat(row.sharpe_ratio).toFixed(3)}`}
          </span>
        </p>
      </div>
    );
  });
};

const PlayGameStats = ({ gameId }) => {
  const [statData, setStatData] = useState({});

  useEffect(async () => {
    const data = await fetchGameData(gameId, "get_sidebar_stats");
    setStatData(data);
  }, []);

  return (
    <div>
      <SectionTitle>The Field</SectionTitle>|{" "}
      {statData.days_left && Math.abs(statData.days_left)} days left
      {statData.records && entryBuilder(statData.records)}
    </div>
  );
};

export { PlayGameStats };
