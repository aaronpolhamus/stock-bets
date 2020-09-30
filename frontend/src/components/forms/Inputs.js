import React from 'react'
import { Form } from 'react-bootstrap'
import styled from 'styled-components'
import PropTypes from 'prop-types'
// This is a helper function to render radio buttons
// It's very important to define a name for radio buttons to work as expected and avoid collisions with other radios

const StyledRadio = styled(Form.Check)`
  padding-left: 0;
  display: inline-block;
  margin-right: var(--space-200);
  margin-bottom: var(--space-100);

  label {
    color: ${(props) => props.color || 'var(--color-text-gray)'};
    cursor: pointer;
    &::before {
      border: 1px solid var(--color-text-gray);
      border-radius: 50%;
      background: #fff;
      content: "";
      display: inline-block;
      height: 16px;
      margin-right: var(--space-50);
      position: relative;
      top: .22rem;
      width: 16px;
    }
  }

  input {
    display: none;
  }

  input:checked + label {
    color: ${(props) => props.$colorChecked || 'var(--color-text-primary)'};
    &::before {
      border-color: var(--color-primary-darken);
      background: radial-gradient(
        circle,
        var(--color-primary-darken) 35%,
        rgba(255, 255, 255, 1) 45%
      );
    }
  }
`

const TabbedRadio = styled(Form.Check)`
  padding-left: 0;
  display: inline-block;
  margin-bottom: var(--space-100);
  font-size: var(--font-size-small);
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-smallcaps);

  label {
    cursor: pointer;
    color: ${(props) => props.color || 'var(--color-text-gray)'};
    border-bottom-width: 2px;
    border-bottom-style: solid;
    border-bottom-color: ${(props) =>
      props.colorTab || 'var(--color-secondary-muted)'};
    padding: var(--space-100) var(--space-300);
    min-width: var(--space-lg-100);
    text-align: center;
  }

  input {
    display: none;
  }

  input:checked + label {
    color: ${(props) => props.$colorChecked || 'var(--color-text-primary)'};
    border-bottom-color: ${(props) => props.colorTabChecked || 'var(--color-primary)'};
  }
`

const buildRadios = (props, mode) => {
  if (props.options === undefined) return null
  const optionsIsArray = Array.isArray(props.options)
  const mappable = optionsIsArray ? props.options : Object.keys(props.options)
  return mappable.map((key, index) => {

    const commonProps = {
      type: 'radio',
      label: optionsIsArray ? key : props.options[key],
      value: key,
      key: index,
      id: `${props.name}-${index}`,
      defaultChecked: props.$defaultChecked === key,
      ...props
    }

    switch (mode) {
      case 'tabbed':
        return <TabbedRadio {...commonProps} />

      default:
        return <StyledRadio {...commonProps} />
    }
  })
}

const RadioButtons = (props) => (
  <div>{props.options && buildRadios(props)}</div>
)

// -- Props
// color: default tab color
// colorChecked: selected tab color
// colorTab: tab underline color
// colorTabChecked: selected tab underline color
const TabbedRadioButtons = (props) => (
  <>
    {props.options && buildRadios(props, 'tabbed')}
  </>
)

RadioButtons.propTypes = {
  options: PropTypes.object
}

TabbedRadioButtons.propTypes = {
  options: PropTypes.oneOfType([
    PropTypes.array,
    PropTypes.object
  ])
}

export { RadioButtons, TabbedRadioButtons }
