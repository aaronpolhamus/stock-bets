import React from 'react'
import { CompoundChart } from 'components/charts/CompoundChart'
import { UserDropDownChart } from 'components/charts/BaseCharts'
import { CustomSelect } from 'components/ui/inputs/CustomSelect'

import { Container } from 'react-bootstrap'
import { FormattableTable } from 'components/tables/FormattableTable'

const players = ['player1', 'player3', 'player3']
const Playground = () => {
  return (
    <Container>
      <h1>
        Playground
        <CustomSelect
          name='username'
          as='select'
          size='sm'

        >
          {players && players.map((element) => <option key={element} value={element}>{element}</option>)}
        </CustomSelect>
      </h1>
    </Container>
  )
}

export { Playground }
