import React, {useRef} from 'react'
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
      {value}
    </strong>
  )
}

const Playground = () => {
  const tableRef = useRef()
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
              ref={tableRef}
              endpoint='get_current_balances_table'
              name='balances-table'
              gameId='3'
              onRowSelect={handleSelect}
              tableCellCheckbox={0}
              tableCellFormat={{
                Symbol: symbolFormat,
                'Change since last close': recentChangeFormat
              }}
            />
          )
        }
      </CompoundChart>
    </Container>
  )
}

export { Playground }
