import React, { useEffect, useState } from "react";
import styled from "styled-components";
import { fetchGameData } from "components/functions/api";

const GameDetails = styled.small`
  display: block;
  font-size: var(--font-size-min);
  letter-spacing: var(--letter-spacing-smallcaps);
  text-transform: uppercase;
  color: var(--color-text-gray);
  margin-top: var(--space-100);
`;

const TextDivider = styled.span`
  font-weight: bold;
  color: var(--color-primary-darken);
`;

const GameHeader = ({ gameId }) => {
  const [gameInfo, setGameInfo] = useState([]);

  useEffect(async () => {
    const data = await fetchGameData(gameId, "game_info");
    setGameInfo(data);
  }, []);

  return (
    <h1>
      {gameInfo.title}
      <GameDetails>
        {gameInfo.mode}
        <TextDivider> | </TextDivider>
        Sidebet: {gameInfo.side_bets_perc}% {gameInfo.side_bets_period}
      </GameDetails>
    </h1>
  );
};

export { GameHeader };
