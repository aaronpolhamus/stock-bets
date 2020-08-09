import { PayPalButton } from 'react-paypal-button-v2'
import React from 'react'

const CustomPaypalButton = (amount, onApproval = () => null) => {
  return (
    <PayPalButton
      shippingPreference='NO_SHIPPING'
      createOrder={(data, actions) => {
        return actions.order.create({
          purchase_units: [{
            amount: {
              currency_code: 'USD',
              value: amount
            }
          }]
        })
      }}
      onApprove={(data, actions) => {
      // Capture the funds from the transaction
        return actions.order.capture().then(function (details) {
          onApproval()
        })
      }}
      options={{
        clientId: process.env.REACT_APP_PAYPAL_CLIENT_ID,
        currency: 'USD'
      }}
    />
  )
}

export { CustomPaypalButton }
