import React, { useEffect, useState } from 'react'
import { Table } from 'react-bootstrap'
import { fetchGameData } from 'components/functions/api'
import { ArrowDownLeft, ArrowUpRight } from 'react-feather'
import { Subtext, SectionTitle } from 'components/textComponents/Text'
import {
  RowStyled,
  CellStyled
} from 'components/tables/TableStyledComponents'

import { makeCustomHeader } from 'components/functions/tables'

import PropTypes from 'prop-types'

const OrderTypeIcon = ({ type, ...props }) => {
  switch (type) {
    case 'buy':
      return <ArrowDownLeft color='var(--color-text-light-gray)' {...props} />
    case 'sell':
      return <ArrowUpRight color='#5ac763' {...props} />
  }
}

const tableHeaders = {
  fulfilled: [
    {
      value: 'Type'
    },
    {
      value: 'Symbol'
    },
    {
      value: 'Qty.',
      align: 'right'
    },
    {
      value: 'Price',
      align: 'right'
    },
    {
      value: 'Date Placed',
      align: 'right'
    }
  ]
}

const renderFulfilledRows = (rows) => {
  return rows.map((row, index) => {
    return (
      <RowStyled title={`${row['Buy/Sell']} order`} key={index}>
        <td>
          <OrderTypeIcon size={18} type={row['Buy/Sell']} />
        </td>
        <td>
          <strong>{row.Symbol}</strong>
        </td>
        <CellStyled>
          <strong>{row.Quantity}</strong>
        </CellStyled>
        <CellStyled>
          <strong>{row['Clear price']}</strong>
          <Subtext>{row['Hypothetical % return']}</Subtext>
        </CellStyled>
        <CellStyled>{row['Placed on']}</CellStyled>
      </RowStyled>
    )
  })
}

const OpenOrdersTable = ({ gameId }) => {
  const [tableData, setTableData] = useState({})
  const getGameData = async () => {
    const data = await fetchGameData(gameId, 'get_order_details_table')
    setTableData(data)
  }

  useEffect(() => {
    getGameData()
  }, [])

  // Methods and settings for modal component

  if (tableData.orders) {
    return (
      <>
        <SectionTitle>Fulfilled orders</SectionTitle>
        <Table hover>
          <thead>
            <tr>{makeCustomHeader(tableHeaders.fulfilled)}</tr>
          </thead>
          <tbody>
            {renderFulfilledRows(tableData.orders.fulfilled.slice(0).reverse())}
          </tbody>
        </Table>
      </>
    )
  }
  return null
}

OrderTypeIcon.propTypes = {
  type: PropTypes.string
}

OpenOrdersTable.propTypes = {
  gameId: PropTypes.number
}
export { OpenOrdersTable }
