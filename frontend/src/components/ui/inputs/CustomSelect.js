import React from 'react'
import { Form } from 'react-bootstrap'
import styled from 'styled-components'

const Select = styled.div`
  display: inline-block; 
  border: 1px solid var(--color-text-gray);
  border-radius: 5px;
  position: relative;
  margin: 0 var(--space-100);
  &::after{
    content: '';
    position: absolute;
    right: var(--space-100);
    top: 55%;
    transform: translateY(-50%);
    display: block;
    width: 0;
    height: 0;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 9px solid var(--color-text-gray);
  }
  select{
    appearance: none;
    padding: 0 var(--space-100);
    font-size: var(--font-size-medium-large);
    height: var(--space-500);
    color: var(--color-text-primary);
    width: auto;
    border: none;
    min-width: 10rem;
  }
`

const CustomSelect = props => {
  return (
    <Select>
      <Form.Control {...props} as='select'>
        {props.children}
      </Form.Control>
    </Select>

  )
}

export { CustomSelect }
