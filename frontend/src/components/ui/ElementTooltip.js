import React, { useState, useRef } from 'react'
import { Popover, Overlay } from 'react-bootstrap'
import PropTypes from 'prop-types'

const ElementTooltip = ({ message, children, placement='auto' }) => {
  const [show, setShow] = useState(false)
  const target = useRef(null)
  return (
    <>
      <div
        ref={target}
        onMouseEnter={() => {
          setShow(true)
        }}
        onMouseLeave={() => {
          setShow(false)
        }}
      >
        {children}
      </div>
      <Overlay
        placement={placement}
        flip
        target={target.current}
        show={show}
        popperConfig={{
          modifiers: [
            {
              name: 'offset',
              options: {
                offset: [65, 0]
              }
            }
          ]
        }}
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

ElementTooltip.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.func,
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ]),
  placement: PropTypes.string,
  message: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.node
  ])
}
export { ElementTooltip }