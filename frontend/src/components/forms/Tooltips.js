import React, { useState, useRef } from 'react'
import { Popover, Overlay } from 'react-bootstrap'
import { HelpCircle } from 'react-feather'
import PropTypes from 'prop-types'

const Tooltip = ({ message, showDelay = 300, hideDelay = 300 }) => {
  const [show, setShow] = useState(false)
  const target = useRef(null)
  let hideTimeout = null
  let showTimeout = null

  const handleMouseEnter = () => {
    clearTimeout(hideTimeout)
    if (!show) {
      showTimeout = setTimeout(() => {
        setShow(true)
      }, showDelay)
    }
  }

  const handleMouseOut = () => {
    clearTimeout(showTimeout)
    if (show) {
      hideTimeout = setTimeout(() => {
        setShow(false)
      }, hideDelay)
    }
  }
  return (
    <>
      <HelpCircle
        size={14}
        style={{ marginTop: '2px', cursor: 'pointer'}}
        ref={target}
        onClick={() => {
          setShow(!show)
        }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseOut}
      />
      <Overlay
        placement='auto'
        flip
        target={target.current}
        show={show}
        arrowProps={{
          ref: target.current
        }}
      >
        {({ ...props }) => (
          <Popover
            {...props}
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

Tooltip.propTypes = {
  message: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.node
  ]),
  showDelay: PropTypes.number,
  hideDelay: PropTypes.number

}
export { Tooltip }
