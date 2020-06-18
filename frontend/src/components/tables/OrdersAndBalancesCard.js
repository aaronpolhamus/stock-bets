import React, { useEffect, useState } from "react";
import { Tab, Tabs, Card } from "react-bootstrap";
import { fetchGameData } from "components/functions/api";

import { BalancesTable } from "components/tables/BalancesTable";
import { OpenOrdersTable } from "components/tables/OpenOrdersTable";
import { PayoutsTable } from "components/tables/PayoutsTable";

const OrdersAndBalancesCard = ({ gameId }) => {
  const [cashData, setCashData] = useState({});

  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, "get_cash_balances");
      setCashData(data);
    };
    getGameData();
  }, [gameId]);

  console.log(cashData);
  return (
    <>
      <br></br>
      <div>
        Cash balance: {cashData.cash_balance} | Buying power{" "}
        {cashData.buying_power}
      </div>
      <br></br>
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
