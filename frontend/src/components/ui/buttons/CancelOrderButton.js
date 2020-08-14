import React, { useState, useRef } from 'react'
import styled from 'styled-components'
import { XCircle } from 'react-feather'
import PropTypes from 'prop-types'
import { Button, Modal } from 'react-bootstrap'
import { apiPost } from 'components/functions/api'

const CancelButtonWrapper = ({ className, text, orderInfo, gameId, onCancelOrder }) => {
  const [showModal, setShowModal] = useState(false)
  const [cancelableOrder, setCancelableOrder] = useState(null)
  const btnCancelRef = useRef()

  const handleCloseModal = () => {
    setShowModal(false)
  }

  const handleCancelOrder = async (gameId, orderId) => {
    await apiPost('cancel_order', {
      order_id: orderId
    })
    onCancelOrder !== undefined && onCancelOrder()
    handleCloseModal()
  }

  return (
    <>
      <Modal centered show={showModal} onHide={handleCloseModal}>
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
            onClick={handleCloseModal}
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
      <button
        onClick={() => {
          setCancelableOrder(orderInfo)
          setTimeout(() => {
            btnCancelRef.current.focus()
          }, 1)
          setShowModal(true)
        }
        }
        className={className}
        title='Cancel Order'
      >
        <XCircle size={16} />
      </button>
    </>
  )
}

const CancelOrderButton = styled(CancelButtonWrapper)`
  appearance: none;
  border: none;
  border-radius: var(--space-50);
  background-color: transparent;
  height: auto;
  line-height: 1;
  padding: var(--space-100) var(--space-200);
  transition: all 0.3s;
  margin-left: var(--space-100);
  svg {
    transition: all 0.3s;
  }
  tr:hover & svg {
    stroke: red;
  }
  &:hover {
    background-color: var(--color-terciary);
  }
  tr:hover &:hover svg {
    stroke: white;
  }
`

CancelButtonWrapper.propTypes = {
  className: PropTypes.string,
  gameId: PropTypes.string,
  onCancelOrder: PropTypes.func,
  orderInfo: PropTypes.object,
  text: PropTypes.string
}

export { CancelOrderButton }
