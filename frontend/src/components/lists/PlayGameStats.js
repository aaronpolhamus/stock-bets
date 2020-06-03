import React, { useEffect, useState } from "react";
import { Card, Row, Col } from "react-bootstrap";
import { fetchGameData } from "components/functions/api";

const entryBuilder = (data) => {
  return data.map((row, index) => {
    return (
      <Card>
        <Card.Title>
          ({row.profile_pic}) {row.username}
        </Card.Title>
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
      </Card>
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
    <Card>
      <Card.Title>
        The Field | Days left: {statData.days_left && statData.days_left}
      </Card.Title>
      {statData.records && entryBuilder(statData.records)}
    </Card>
  );
};

export { PlayGameStats };
