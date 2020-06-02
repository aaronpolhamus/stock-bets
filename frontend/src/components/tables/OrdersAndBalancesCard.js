import React from "react";
import { Tab, Tabs } from "react-bootstrap";

import { BalancesTable } from "components/tables/BalancesTable";
import { OpenOrdersTable } from "components/tables/OpenOrdersTable";

const OrdersAndBalancesCard = (gameId) => {
  return (
    <Tabs>
      <Tab eventKey="balances" title="Balances">
        <BalancesTable gameId={3} />
      </Tab>
      <Tab eventKey="orders" title="Open orders">
        <OpenOrdersTable gameId={3} />
      </Tab>
    </Tabs>
  );
};

export { OrdersAndBalancesCard };
