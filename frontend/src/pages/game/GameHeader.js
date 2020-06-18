import React, { useEffect, useState } from "react";
import styled from "styled-components";
import { fetchGameData } from "components/functions/api";
import { dollarizer } from "components/functions/formats";

const GameDetails = styled.small`
  display: block;
  font-size: var(--font-size-min);
  letter-spacing: var(--letter-spacing-smallcaps);
  text-transform: uppercase;
  color: var(--color-text-gray);
  margin-top: var(--space-200);
`;

const TextDivider = styled.span`
  font-weight: bold;
  color: var(--color-primary-darken);
`;

const CashInfoWrapper = styled.div`
  text-align: right;
  color: var(--color-text-gray);
  p {
    margin: 0;
  }
  strong {
    text-transform: uppercase;
    font-size: var(--font-size-min);
  }
  small {
    color: var(--color-text-light-gray);
  }
`;
const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
  h1 {
    margin-top: 0;
    line-height: 1;
  }
`;

const GameHeader = ({ gameId }) => {
  const [gameInfo, setGameInfo] = useState([]);
  const [cashData, setCashData] = useState({});

  const getGameData = async () => {
    const data = await fetchGameData(gameId, "game_info");
    const cashInfo = await fetchGameData(gameId, "get_cash_balances");

    setCashData(cashInfo);
    setGameInfo(data);
  };

  useEffect(() => {
    getGameData();
  }, []);

  console.log("playgamejs", cashData);
  return (
    <Header>
      <h1>
        {gameInfo.title}
        <GameDetails>
          {gameInfo.mode}
          <TextDivider> | </TextDivider>
          Sidebet: {gameInfo.side_bets_perc}% {gameInfo.side_bets_period}
        </GameDetails>
      </h1>
      <CashInfoWrapper>
        <p>
          <strong>Cash Balance: </strong>
          {cashData.cash_balance && dollarizer.format(cashData.cash_balance)}
        </p>
        <p>
          <small>
            <strong>Buying power: </strong>
            {cashData.buying_power && dollarizer.format(cashData.buying_power)}
          </small>
        </p>
      </CashInfoWrapper>
    </Header>
  );
};

export { GameHeader };
