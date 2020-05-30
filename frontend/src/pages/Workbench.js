// A workbench for testing new components. We'll card-code in props and data connections, and coordinate with 
// miguel to properly integrate into the play game flow
import React from 'react';

import {BalancesChart} from "../components/charts/BalancesChart"
import {FieldChart} from "../components/charts/FieldChart"


const Workbench = () => {
  return (
    <>
      <BalancesChart gameId={3} />
      <FieldChart gameId={3} />
    </>
  )
}

export {Workbench};
