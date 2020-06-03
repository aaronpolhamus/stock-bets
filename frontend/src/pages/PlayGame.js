import React, { useEffect, useState } from "react";
import { Container, Tabs, Tab } from "react-bootstrap";
import Autosuggest from "react-autosuggest";
import { optionBuilder } from "components/functions/forms";
import { useParams } from "react-router-dom";
import { PlaceOrder } from "components/forms/PlaceOrder";
import {
  Layout,
  Sidebar,
  PageSection,
  Content,
  SmallColumn,
} from "components/layout/Layout";
import { FieldChart } from "components/charts/FieldChart";
import { BalancesChart } from "components/charts/BalancesChart";
import { OrdersAndBalancesCard } from "components/tables/OrdersAndBalancesCard";
import { GameHeader } from "pages/game/GameHeader";
import { PlayGameStats } from "components/lists/PlayGameStats";

const PlayGame = (props) => {
  const { gameId } = useParams();

  return (
    <Layout>
      <Sidebar>
        <PlaceOrder gameId={gameId} />
      </Sidebar>
      <SmallColumn>
        <PlayGameStats gameId={gameId} />
      </SmallColumn>
      <Content>
        <PageSection>
          <p>
            <a href="/">&lt; Dashboard</a>
          </p>
          <GameHeader gameId={gameId} />
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
      </Content>
    </Layout>
  );
};

export { PlayGame };
