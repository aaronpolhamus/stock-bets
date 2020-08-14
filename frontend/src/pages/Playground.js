import React from 'react'
import { CompoundChart } from 'components/charts/CompoundChart'

import { Container } from 'react-bootstrap'
import { FormattableTable } from 'components/tables/FormattableTable'

const Playground = () => {
  return (
    <Container>
      <h1>
        Playground
      </h1>
      <CompoundChart
        gameId='3'
        chartDataEndpoint='get_order_performance_chart'
        legends={false}
      >
        {
          ({ handleSelectedLines }) => (
            <FormattableTable
              hover
              endpoint='get_fulfilled_orders_table'
              name='orders_table'
              gameId='3'
              onRowSelect={(output) => {
                handleSelectedLines(output)
              }}
              tableCellCheckbox={0}
              tableRowOutput={{
                label: 'Symbol',
                color: 'color || #000000'
              }}
              tableCellFormat={{
                Symbol: function renderSymbol (value, row) {
                  return (
                    <strong>
                      {value}
                    </strong>
                  )
                },
                'Hypothetical % return': function formatForNetChange (value) {
                  let color = 'var(--color-text-gray)'
                  if (parseFloat(value) < 0) {
                    color = 'var(--color-danger)'
                  } else if (parseFloat(value) > 0) {
                    color = 'var(--color-success)'
                  }

                  return (
                    <strong
                      style={{
                        color: color
                      }}
                    >
                      {value}
                    </strong>
                  )
                }
              }}
              exclude={[
                'Status',
                'as of',
                'Buy/Sell',
                'Order type',
                'Time in force',
                'Market price',
                'Placed on',
                'Order price'
              ]}
              sortBy='Hypothetical % return'
              showColumns={{
              }}
            />
          )
        }
      </CompoundChart>
    </Container>
  )
}

export { Playground }
