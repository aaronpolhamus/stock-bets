import React, { useEffect, useState } from "react";
import { Container, Tabs, Tab } from "react-bootstrap";
import Autosuggest from "react-autosuggest";
import { optionBuilder } from "components/functions/forms";
import { useParams } from "react-router-dom";
import { PlaceOrder } from "components/forms/PlaceOrder";
import { Layout, Sidebar, PageSection } from "components/layout/Layout";
import { FieldChart } from "components/charts/FieldChart";
import { BalancesChart } from "components/charts/BalancesChart";
import { OrdersAndBalancesCard } from "components/tables/OrdersAndBalancesCard";
import { fetchGameData } from "components/functions/api";

const PlayGame = (props) => {
  const { gameId } = useParams();
  const [gameInfo, setGameInfo] = useState([]);

  useEffect(async () => {
    const data = await fetchGameData(gameId, "game_info");
    setGameInfo(data);
  }, []);

  console.log(gameInfo);
  return (
    <Layout>
      <Sidebar>
        <PlaceOrder gameId={gameId} />
      </Sidebar>
      <Container>
        <PageSection>
          <p>
            <a href="/">Dashboard</a>
          </p>
          <h1>
            {gameInfo.title}
            <small>
              {gameInfo.mode}
              <span> | </span>
              Sidebet: {gameInfo.side_bets_perc}% {gameInfo.side_bets_period}
            </small>
          </h1>
        </PageSection>
        <PageSection>
          <Tabs>
            <Tab eventKey="field-chart" title="Field">
              <FieldChart gameId={gameId} />
            </Tab>
            <Tab eventKey="balances-chart" title="Balances">
              <BalancesChart gameId={gameId} />
            </Tab>
          </Tabs>
        </PageSection>
        <PageSection>
          <OrdersAndBalancesCard gameId={gameId} />
        </PageSection>
      </Container>
    </Layout>
  );
};

export { PlayGame };
