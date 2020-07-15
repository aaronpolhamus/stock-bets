import React, { useEffect, useState } from 'react'
import { Table, Button, Modal } from 'react-bootstrap'
import { fetchGameData, apiPost } from 'components/functions/api'
import { ArrowDownLeft, ArrowUpRight } from 'react-feather'
import { SmallCaps, Subtext } from 'components/textComponents/Text'

import {
  RowStyled,
  CellStyled,
  CancelButton
} from 'components/tables/TableStyledComponents'

import { makeCustomHeader } from 'components/functions/tables'

const OrderTypeIcon = ({ type, ...props }) => {
  switch (type) {
    case 'buy':
      return <ArrowDownLeft color='var(--color-text-light-gray)' {...props} />
    case 'sell':
      return <ArrowUpRight color='#5ac763' {...props} />
  }
}

const tableHeaders = {
  pending: [
    {
      value: 'Type'
    },
    {
      value: 'Symbol'
    },
    {
      value: 'Quantity',
      align: 'right'
    },
    {
      value: 'Price',
      align: 'right'
    },
    {
      value: 'Time in force'
    },
    {
      value: 'Date Placed',
      align: 'right'
    }
  ],
  fulfilled: [
    {
      value: 'Type'
    },
    {
      value: 'Symbol'
    },
    {
      value: 'Quantity',
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

  const [cancelableOrder, setCancelableOrder] = useState(null)
  // Methods and settings for modal component
  const [show, setShow] = useState(false)
  const handleClose = () => setShow(false)
  const handleCancelOrder = async (gameId, orderId) => {
    await apiPost('cancel_order', {
      game_id: gameId,
      order_id: orderId
    })
    getGameData()
    setShow(false)
  }

  const renderRows = (rows) => {
    return rows.map((row, index) => {
      return (
        <RowStyled title={`${row['Buy/Sell']} order`} key={index}>
          <td>
            <OrderTypeIcon size={20} type={row['Buy/Sell']} />
            <SmallCaps color='var(--color-text-gray)'>
              {row['Order type']}
            </SmallCaps>
          </td>
          <td>
            <strong>{row.Symbol}</strong>
          </td>
          <CellStyled>
            <strong>{row.Quantity}</strong>
          </CellStyled>
          <CellStyled>
            <strong>{row['Order price']}</strong>
          </CellStyled>
          <td>
            <SmallCaps>{row['Time in force']}</SmallCaps>
          </td>
          <CellStyled>
            {row['Placed on']}
            <CancelButton
              onClick={() => {
                setCancelableOrder(row)
                setShow(true)
              }}
            />
          </CellStyled>
        </RowStyled>
      )
    })
  }

  if (tableData.orders) {
    return (
      <>
        <h2>
          <SmallCaps>Pending orders</SmallCaps>
        </h2>
        <Table hover>
          <thead>
            <tr>{makeCustomHeader(tableHeaders.pending)}</tr>
          </thead>
          <tbody>{renderRows(tableData.orders.pending, gameId)}</tbody>
        </Table>
        <h2>
          <SmallCaps>Fulfilled orders</SmallCaps>
        </h2>
        <Table hover>
          <thead>
            <tr>{makeCustomHeader(tableHeaders.fulfilled)}</tr>
          </thead>
          <tbody>
            {renderFulfilledRows(tableData.orders.fulfilled.slice(0).reverse())}
          </tbody>
        </Table>
        <Modal centered show={show} onHide={handleClose}>
          <Modal.Header>
            <Modal.Title className='text-center'>
              {cancelableOrder && `Cancel ${cancelableOrder['Buy/Sell']} order`}
            </Modal.Title>
          </Modal.Header>
          <Modal.Body className='text-center'>
            <p>
              {cancelableOrder &&
                `${cancelableOrder.Quantity} shares of ${cancelableOrder.Symbol} at ${cancelableOrder['Order price']}`}
            </p>
          </Modal.Body>
          <Modal.Footer className='centered'>
            <Button variant='info' onClick={handleClose}>
              I'll think about it
            </Button>
            <Button
              type='submit'
              variant='danger'
              onClick={() => {
                handleCancelOrder(gameId, cancelableOrder.order_id)
              }}
            >
              Cancel order
            </Button>
          </Modal.Footer>
        </Modal>
      </>
    )
  }
  return null
}

export { OpenOrdersTable }
