import React from 'react'
import styled from 'styled-components'
import PropTypes from 'prop-types'
import { Tooltip } from 'components/forms/Tooltips'
import { toCurrency } from 'components/functions/formattingHelpers'

const CashInfoWrapper = styled.div`
  text-align: left;
  color: var(--color-text-gray);
  margin-bottom: var(--space-200);
  p {
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  strong {
    text-transform: uppercase;
    font-size: var(--font-size-min);
  }
  small {
    color: var(--color-text-light-gray);
  }
`

const CashInfo = ({ cashData, balance = true, buyingPower = true }) => {
  return (
    <CashInfoWrapper>
      {balance &&
        <p>
          <span>
            <strong>Cash Balance: </strong>
            {cashData.cash_balance && toCurrency(cashData.cash_balance)}
          </span>
        </p>}
      {buyingPower &&
        <p>
          <small>
            <strong>Buying power: </strong>
            {cashData.buying_power && toCurrency(cashData.buying_power)}
          </small>
          <Tooltip
            message={
              <>
                <p>
                  <strong>Buying power</strong> is your cash minus any outstanding buy order.
                </p>
              </>
            }
          />
        </p>}
    </CashInfoWrapper>
  )
}

CashInfo.propTypes = {
  cashData: PropTypes.object,
  balance: PropTypes.bool,
  buyingPower: PropTypes.bool
}

export { CashInfo }
