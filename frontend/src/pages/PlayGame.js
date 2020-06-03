import React, { useEffect, useState } from "react";
import axios from "axios";
import { Container, Tabs, Tab } from "react-bootstrap";
import Autosuggest from "react-autosuggest";
import { optionBuilder } from "components/functions/forms";
import { useParams } from "react-router-dom";
import { PlaceOrder } from "components/forms/PlaceOrder";
import { Layout, Sidebar, PageSection } from "components/layout/Layout";
import { FieldChart } from "components/charts/FieldChart";
import { BalancesChart } from "components/charts/BalancesChart";
import { OrdersAndBalancesCard } from "components/tables/OrdersAndBalancesCard";

const PlayGame = (props) => {
  const { gameId } = useParams();
  return (
    <Layout>
      <Sidebar>
        <PlaceOrder gameId={gameId} />
      </Sidebar>
      <Container>
        <PageSection>
          <p>
            <a>Dashboard</a>
          </p>
          <h1>
            Game Name
            <small>Return Weighted | Sidebet: 50% weekly</small>
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
