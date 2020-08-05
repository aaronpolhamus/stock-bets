import React from 'react'
import { CompoundChart } from 'components/charts/CompoundChart'

import { Container } from 'react-bootstrap'

const Playground = () => {
  return (
    <Container>
      <h1>
        Playground
      </h1>
      <CompoundChart
        gameId={3}
        chartDataEndpoint='get_balances_chart'
        tableDataEndpoint='get_current_balances_table'
        tableOptions={''}
        tableId='balances-table'
      />
    </Container>
  )
}

export { Playground }
