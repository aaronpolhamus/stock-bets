// A workbench for testing new components. We'll card-code in props and data connections, and coordinate with
// miguel to properly integrate into the play game flow
import React from "react";

import { BalancesChart } from "components/charts/BalancesChart";
import { FieldChart } from "components/charts/FieldChart";
import { PlaceOrder } from "components/forms/PlaceOrder";
import { MakeGame } from "components/forms/MakeGame";
import { OrdersAndBalancesCard } from "components/tables/OrdersAndBalancesCard";
import { PlayGameStats } from "components/lists/PlayGameStats";
import { GameCard } from "pages/game/GameCard";

const Workbench = () => {
  return (
    <>
      <BalancesChart gameId={3} />
      <OrdersAndBalancesCard gameId={3} />
      <GameCard gameId={3} />
      <FieldChart gameId={3} />
      <PlaceOrder gameId={3} />
      <PlayGameStats gameId={3} />
      <MakeGame />
    </>
  );
};

export { Workbench };
