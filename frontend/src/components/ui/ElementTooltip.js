import React, { useState, useRef } from 'react'
import { Popover, Overlay } from 'react-bootstrap'
import PropTypes from 'prop-types'

const ElementTooltip = ({ message, children, placement = 'auto', delay = 0 }) => {
  const [show, setShow] = useState(false)
  const target = useRef(null)

  let hideTimeout = null
  let showTimeout = null

  const handleMouseEnter = () => {
    clearTimeout(hideTimeout)
    if (!show) {
      showTimeout = setTimeout(() => {
        setShow(true)
      }, 500)
    }
  }
  
  const handleMouseOut = () => {
    clearTimeout(showTimeout)
    if (show) {
      hideTimeout = setTimeout(() => {
        setShow(false)
      }, 300)
    }
  }

  return (
    <>
      <div
        ref={target}
        onClick={() => {
          setShow(!show)
        }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseOut}
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
            className='popover-card'
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseOut}
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
  delay: PropTypes.number,
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
