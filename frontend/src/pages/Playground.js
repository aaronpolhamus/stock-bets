import React from 'react'
import { CompoundChart } from 'components/charts/CompoundChart'

import { Container } from 'react-bootstrap'
import { FormattableTable } from 'components/tables/FormattableTable'

const symbolFormat = (value) => {
  return (
    <strong>
      {value}
    </strong>
  )
}

const recentChangeFormat = (value) => {
  return (
    <strong>
      {value.toFixed(3)}
    </strong>
  )
}

const Playground = () => {
  return (
    <Container>
      <h1>
        Playground
      </h1>
      <CompoundChart
        gameId='3'
        chartDataEndpoint='get_balances_chart'
        tableId='balances-table'
      >
        {
          ({ handleSelect }) => (
            <FormattableTable
              endpoint='get_current_balances_table'
              name='balances-table'
              gameId='3'
              onRowSelect={handleSelect}
              tableCellCheckbox={0}
              tableCellFormat={{
                Symbol: symbolFormat,
                'Recent change': recentChangeFormat
              }}
            />
          )
        }
      </CompoundChart>
    </Container>
  )
}

export { Playground }
