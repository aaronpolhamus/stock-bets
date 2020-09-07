import React from 'react'
import * as Icon from 'react-feather'
import PropTypes from 'prop-types'

const IconBuySell = props => {
  return (
    <>
      {props.type === 'sell'
        ? <Icon.ArrowUpRight
          size={16}
          style={{
            position: 'relative',
            top: '-2px',
            marginRight: 'var(--space-50)'
          }}
          strokeWidth={3}
          color='var(--color-danger)'
        />
        : <Icon.ArrowDownLeft
          color='var(--color-success)'
          size={16}
          strokeWidth={3}
          style={{
            position: 'relative',
            top: '-2px',
            marginRight: 'var(--space-50)'
          }}
        />}
    </>
  )
}

IconBuySell.propTypes = {
  type: PropTypes.string
}

export { IconBuySell }
