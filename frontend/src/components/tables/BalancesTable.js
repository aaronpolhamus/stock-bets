import React, { useEffect, useState } from 'react'
import { AutoTable } from 'components/functions/tables'
import { fetchGameData } from 'components/functions/api'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { breakpoints } from 'design-tokens'

const StyledBalancesTable = styled(AutoTable)`
  @media screen and (max-width: ${breakpoints.md}){
    th#balances-last-order-price,
    td[headers='balances-last-order-price'], 
    th#balances-market-price,
    td[headers='balances-market-price'], 
    th#balances-updated-at,
    td[headers='balances-updated-at']{
      display: none;
    }
  }
`

const BalancesTable = ({ gameId }) => {
  const [tableData, setTableData] = useState({})
  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, 'get_current_balances_table')
      setTableData(data)
    }
    getGameData()
  }, [gameId])
  return (
    <StyledBalancesTable
      className
      classhover
      tabledata={tableData}
      name='balances'
    />
  )
}

BalancesTable.propTypes = {
  gameId: PropTypes.number
}

export { BalancesTable }
