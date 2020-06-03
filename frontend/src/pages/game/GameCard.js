import React, { useEffect, useState } from "react";
import styled from "styled-components";
import { fetchGameData } from "components/functions/api";
import { Button } from "react-bootstrap";
import { PlayGameStats } from "components/lists/PlayGameStats";
import { Header } from "components/layout/Layout";

const CardLeftColumn = styled.div`
  width: 300px;
  box-sizing: border-box;
  background-color: var(--color-light-gray);
  padding: var(--space-300);
`;

const CardMainColumn = styled.div`
  padding: var(--space-300);
  flex-grow: 1;
`;

const GameCardWrapper = styled.div`
  display: flex;
  border-radius: 10px;
  overrflow: hidden;
  box-shadow: 0px 5px 11px rgba(53, 52, 120, 0.15),
    0px 1px 4px rgba(31, 47, 102, 0.15);
`;

const GameCard = ({ gameId }) => {
  const [gameInfo, setGameInfo] = useState([]);

  useEffect(async () => {
    const data = await fetchGameData(gameId, "game_info");
    setGameInfo(data);
  }, []);

  return (
    <GameCardWrapper>
      <CardLeftColumn>
        <PlayGameStats gameId={gameId} />
      </CardLeftColumn>
      <CardMainColumn>
        <Header>
          <h2>{gameInfo.title}</h2>
          <Button href={`/play/${gameId}`}>Play</Button>
        </Header>
      </CardMainColumn>
    </GameCardWrapper>
  );
};

export { GameCard };
