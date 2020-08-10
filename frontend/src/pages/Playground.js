import React from 'react'
import { CompoundChart } from 'components/charts/CompoundChart'

import { Container } from 'react-bootstrap'
import { FormattableTable } from 'components/tables/FormattableTable'
import styled from 'styled-components'

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
        legends={false}
      >
        {
          ({ handleSelect }) => (
            <FormattableTable
              hover
              endpoint='get_current_balances_table'
              name='balances-table'
              gameId='3'
              onRowSelect={(output) => {
                console.log(output)
              }}
              tableCellCheckbox={0}
              tableRowOutput={{
                name: 'Symbol',
                color: 'color'
              }}
              tableCellFormat={{
                Symbol: function renderSymbol (value, row) {
                  return (
                    <strong>
                      {value}
                    </strong>
                  )
                },
                'Change since last close': function formatForNetChange (value) {
                  return (
                    <strong>
                      {value}
                    </strong>
                  )
                }
              }}
            />
          )
        }
      </CompoundChart>
    </Container>
  )
}

export { Playground }
