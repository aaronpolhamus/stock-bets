import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchGameData, apiPost } from "components/functions/api";
import {
  Layout,
  Sidebar,
  Content,
  Header,
  PageSection,
  Breadcrumb,
} from "components/layout/Layout";
import { GameSettings } from "pages/game/GameSettings";
import { PendingGameParticipants } from "pages/game/PendingGameParticipants";

import { Button } from "react-bootstrap";

const JoinGame = (props) => {
  const { gameId } = useParams();

  const [gameInfo, setGameInfo] = useState([]);
  const [gameParticipants, setGameParticipants] = useState([]);

  const [invite, setInvite] = useState("");

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

  const handleRespondInvite = async (decision) => {
    await apiPost("respond_to_game_invite", {
      game_id: gameId,
      decision: decision,
    });

    setInvite(decision);
  };

  return (
    <Layout>
      <Sidebar>
        <GameSettings gameInfo={gameInfo} />
      </Sidebar>
      <Content>
        <PageSection>
          <Breadcrumb>
            <a href="/">&lt; Dashboard</a>
          </Breadcrumb>
          <Header>
            <h1>{gameInfo.title}</h1>
            <div>
              <Button
                variant="outline-secondary"
                disabled={invite === "" ? false : true}
                onClick={() => {
                  handleRespondInvite("declined");
                }}
              >
                {invite === "declined" ? "Declined" : "Decline"}
              </Button>
              <Button
                variant="success"
                disabled={invite === "" ? false : true}
                onClick={() => {
                  handleRespondInvite("joined");
                }}
              >
                {invite === "joined" ? "Accepted" : "Accept Invite"}
              </Button>
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
