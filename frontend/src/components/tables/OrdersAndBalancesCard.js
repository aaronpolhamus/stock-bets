import React from "react";
import { Tab, Tabs, Card } from "react-bootstrap";

import { BalancesTable } from "components/tables/BalancesTable";
import { OpenOrdersTable } from "components/tables/OpenOrdersTable";
import { PayoutsTable } from "components/tables/PayoutsTable";

const OrdersAndBalancesCard = ({ gameId }) => {
  return (
    <>
      <Tabs>
        <Tab eventKey="balances" title="Balances">
          <BalancesTable gameId={gameId} />
        </Tab>
        <Tab eventKey="orders" title="Open orders">
          <OpenOrdersTable gameId={gameId} />
        </Tab>
        <Tab eventKey="payouts" title="Payouts">
          <PayoutsTable gameId={gameId} />
        </Tab>
      </Tabs>
    </>
  );
};

export { OrdersAndBalancesCard };
