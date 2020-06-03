import React, { useEffect, useState } from "react";
import { Card, Row, Col } from "react-bootstrap";
import { fetchGameData } from "components/functions/api";
import styled from "styled-components";
import { UserAvatar } from "components/users/UserAvatar";

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
        <UserAvatar src={row.profile_pic} size="small" />

        {row.username}
        <Row>
          <Col>
            <Card.Text>{row.stocks_held.join(", ")} </Card.Text>
          </Col>
          <Col>
            <Row>
              <Card.Text>{row.portfolio_value} (portfolio value) </Card.Text>
            </Row>
            <Row>
              <Card.Text>
                {row.total_return} (total return) | {row.sharpe_ratio} (sharpe
                ratio){" "}
              </Card.Text>
            </Row>
          </Col>
        </Row>
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
