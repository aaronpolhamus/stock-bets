import React, { useState, useRef } from 'react'
import { Popover, Overlay } from 'react-bootstrap'
import { HelpCircle } from 'react-feather'
import PropTypes from 'prop-types'

const Tooltip = ({ message }) => {
  const [show, setShow] = useState(false)
  const target = useRef(null)
  return (
    <>
      <HelpCircle
        size={14}
        style={{ marginTop: '2px' }}
        ref={target}
        onMouseEnter={() => {
          setShow(true)
        }}
        onMouseLeave={() => {
          setShow(false)
        }}
      />
      <Overlay
        placement='auto'
        flip={true}
        target={target.current}
        show={show}
        arrowProps={{
          ref: target.current
        }}
      >
        {({ ...props }) => (
          <Popover
            {...props}
            onMouseEnter={() => {
              setShow(true)
            }}
            onMouseLeave={() => {
              setShow(false)
            }}
          >
            <Popover.Content>
              {message}
            </Popover.Content>
          </Popover>
        )}
      </Overlay>
    </>
  )
}

Tooltip.propTypes = {
  message: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.node
  ])
}
export { Tooltip }
