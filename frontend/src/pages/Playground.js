import React from 'react'
import { CompoundChart } from 'components/charts/CompoundChart'
import { UserDropDownChart } from 'components/charts/BaseCharts'


import { Container } from 'react-bootstrap'
import { FormattableTable } from 'components/tables/FormattableTable'

const Playground = () => {
  return (
    <Container>
      <h1>
        Playground
      </h1>
      <FormattableTable
        hover
        update={''}
        endpoint='get_fulfilled_orders_table'
        name='fulfilled-orders'
        gameId={3}
        formatCells={{
          Symbol: function formatSymbol (value, row) {
            return (
              <>

                <strong>
                  {value}
                </strong>
              </>
            )
          }
        }}
        exclude={[
          'Hypothetical return',
          'Cleared on',
          'Order price',
          'as of',
          'Buy/Sell',
          'Order Type',
          'Time in force',
          'Market price',
          'Order type'
        ]}
        sortBy='Placed on'
        order='DESC'
        showColumns={{
        }}
        formatHeaders={{
          Quantity: 'Qty.'
        }}
      />

    </Container>
  )
}

export { Playground }
