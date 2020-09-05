import React from 'react'
import { CompoundChart } from 'components/charts/CompoundChart'
import { UserDropDownChart } from 'components/charts/BaseCharts'
import { CustomSelect } from 'components/ui/inputs/CustomSelect'

import { Container } from 'react-bootstrap'
import { FormattableTable } from 'components/tables/FormattableTable'

const players = ['player1', 'player3', 'player3']
const Playground = () => {
  const gameId = 3
  return (
    <Container>
      <h1>
        Playground
      </h1>
      <CompoundChart
        gameId={gameId}
        chartDataEndpoint='get_order_performance_chart'
        legends={false}
      >
        {
          ({ handleSelectedLines }) => (
            <FormattableTable
              hover
              endpoint='get_fulfilled_orders_table'
              name='orders_table'
              gameId={gameId}
              onRowSelect={(output) => {
                handleSelectedLines(output)
              }}
              tableCellCheckbox={0}
              formatOutput={(output) => {
                const label = `${output.Symbol}/${output.Quantity} @ ${output['Clear price']}/${output['Cleared on']}`
                return {
                  label: label,
                  color: output.color
                }
              }}
              formatCells={{
                Symbol: function renderSymbol (value, row) {
                  return (
                    <strong>
                      {value}
                    </strong>
                  )
                },
                'Hypothetical return': function netChangeFormat (value) {
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
                },
                'Clear price': function clearPriceFormat (value, row) {
                  const qty = row.Quantity
                  const price = value.replace(/\$|,/g, '')
                  const totalPrice = (qty * price).toLocaleString()
                  return (
                    <>
                      <strong>
                        {value}
                      </strong>
                      <br />
                      <span
                        style={{
                          color: 'var(--color-text-gray)'
                        }}
                      >
                        {`($${totalPrice})`}
                      </span>
                    </>
                  )
                }
              }}
              excludeRows={(row) => {
                return row['Buy/Sell'] === 'sell'
              }}
              exclude={[
                'as of',
                'Buy/Sell',
                'Order type',
                'Time in force',
                'Market price',
                'Placed on',
                'Order price'
              ]}
              sortBy='Hypothetical return'
              sortOrder='DESC'
              showColumns={{
                md: [
                  'Symbol',
                  'Quantity',
                  'Clear price',
                  'Hypothetical return'
                ]
              }}
            />
          )
        }
      </CompoundChart>
    </Container>
  )
}

export { Playground }
