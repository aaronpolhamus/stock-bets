import React, { useState, useRef, useEffect } from 'react'
import { Table, Button, Modal } from 'react-bootstrap'
import { fetchGameData, apiPost } from 'components/functions/api'
import { ArrowDownLeft, ArrowUpRight } from 'react-feather'
import { SectionTitle, SmallCaps } from 'components/textComponents/Text'
import {
  RowStyled,
  CellStyled,
  CancelButton
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

const tableHeaders = [
  {
    value: 'Type',
    content: (<p>jsdfa</p>)
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
    value: 'Time in force',
    hideOnBreakpoint: 'md',
    align: 'right'
  },
  {
    value: 'Date Placed',
    align: 'right',
    hideOnBreakpoint: 'md'
  },
  {
    value: '',
    align: 'right'
  }
]

const PendingOrdersTable = ({ gameId, title, onCancelOrder, update }) => {
  const [cancelableOrder, setCancelableOrder] = useState(null)
  const [ordersData, setOrdersData] = useState({})
  const btnCancelRef = useRef()

  // Methods and settings for modal component
  const [show, setShow] = useState(false)
  const handleClose = () => setShow(false)

  const getOrdersData = async () => {
    const data = await fetchGameData(gameId, 'get_order_details_table')
    setOrdersData(data)
  }

  const handleCancelOrder = async (gameId, orderId) => {
    await apiPost('cancel_order', {
      order_id: orderId
    })
    getOrdersData()
    onCancelOrder()
    setShow(false)
  }

  useEffect(() => {
    getOrdersData()
  }, [update])

  const renderRows = (rows) => {
    return rows.map((row, index) => {
      return (
        <RowStyled title={`${row['Buy/Sell']} order`} key={index}>
          <td>
            <OrderTypeIcon size={20} type={row['Buy/Sell']} />
            <SmallCaps $hideOnBreakpoint='md' color='var(--color-text-gray)'>
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
          <CellStyled $hideOnBreakpoint='md'>
            <SmallCaps>{row['Time in force']}</SmallCaps>
          </CellStyled>
          <CellStyled $hideOnBreakpoint='md'>
            {row['Placed on']}
          </CellStyled>
          <CellStyled>
            <CancelButton
              onClick={() => {
                setCancelableOrder(row)
                setTimeout(() => {
                  btnCancelRef.current.focus()
                }, 1)
                setShow(true)
              }}
            />
          </CellStyled>
        </RowStyled>
      )
    })
  }

  if (ordersData.orders) {
    return (
      <>
        {title && <SectionTitle>{title}</SectionTitle>}
        <Table hover>
          <thead>
            <tr>{makeCustomHeader(tableHeaders)}</tr>
          </thead>
          <tbody>{renderRows(ordersData.orders.pending, gameId)}</tbody>
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

            <Button
              variant='info'
              onClick={handleClose}
            >
                I&apos;ll think about it
            </Button>
            <Button
              ref={btnCancelRef}
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

PendingOrdersTable.propTypes = {
  ordersData: PropTypes.object,
  onCancelOrder: PropTypes.func,
  gameId: PropTypes.number,
  title: PropTypes.string,
  update: PropTypes.string
}

OrderTypeIcon.propTypes = {
  type: PropTypes.string
}

export { PendingOrdersTable }
