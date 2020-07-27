import React from 'react'
import { Popover, OverlayTrigger } from 'react-bootstrap'
import { HelpCircle } from 'react-feather'
import PropTypes from 'prop-types'

const Tooltip = ({ message }) => (
  <OverlayTrigger
    placement='auto'
    trigger={['hover', 'focus']}
    html
    overlay={
      <Popover>
        <Popover.Content>{message}</Popover.Content>
      </Popover>
    }
  >
    <HelpCircle size={14} style={{ marginTop: '2px' }} />
  </OverlayTrigger>
)

Tooltip.propTypes = {
  message: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.node
  ])
}
export { Tooltip }
