import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchGameData } from "components/functions/api";
import {
  Layout,
  Sidebar,
  Content,
  Header,
  PageSection,
} from "components/layout/Layout";
import { PlaceOrder } from "components/forms/PlaceOrder";
import { GameSettings } from "pages/game/GameSettings";
import { PendingGameParticipants } from "pages/game/PendingGameParticipants";

import { Button } from "react-bootstrap";

const JoinGame = (props) => {
  const { gameId } = useParams();

  const [gameInfo, setGameInfo] = useState([]);
  const [gameParticipants, setGameParticipants] = useState([]);

  useEffect(() => {
    const getGameData = async () => {
      const gameData = await fetchGameData(gameId, "game_info");
      setGameInfo(gameData);

      const gameParticipantsData = await fetchGameData(
        gameId,
        "get_pending_game_info"
      );
      setGameParticipants(gameParticipantsData);
    };

    getGameData();
  }, [gameId]);

  return (
    <Layout>
      <Sidebar>
        <GameSettings gameInfo={gameInfo} />
      </Sidebar>
      <Content>
        <PageSection>
          <Header>
            <h1>{gameInfo.title}</h1>
            <div>
              <Button variant="outline-secondary">Decline</Button>
              <Button variant="success">Accept Invitation</Button>
            </div>
          </Header>
        </PageSection>
        <PageSection>
          <PendingGameParticipants participants={gameParticipants} />
        </PageSection>
      </Content>
    </Layout>
  );
};

export { JoinGame };
