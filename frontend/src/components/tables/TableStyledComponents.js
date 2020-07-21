import React from 'react'
import styled from 'styled-components'
import { XCircle } from 'react-feather'
import { breakpoints } from 'design-tokens'

const CellStyled = styled.td`
  text-align: ${(props) => props.align || 'right'};
  @media screen and (max-width: ${props => breakpoints[props.$hideOnBreakpoint]}){
    display: none;
  }
`

const RowStyled = styled.tr`
  white-space: nowrap;
  td {
    vertical-align: middle;
    position: relative;
  }
`

const CancelButtonWrapper = ({ onClick, className }) => {
  return (
    <button onClick={onClick} className={className} title='Cancel Order'>
      <XCircle size={16} />
    </button>
  )
}

const CancelButton = styled(CancelButtonWrapper)`
  appearance: none;
  border: none;
  border-radius: var(--space-50);
  background-color: transparent;
  height: auto;
  line-height: 1;
  padding: var(--space-100) var(--space-200);
  transition: all 0.3s;
  margin-left: var(--space-100);
  svg {
    transition: all 0.3s;
  }
  tr:hover & svg {
    stroke: red;
  }
  &:hover {
    background-color: var(--color-terciary);
  }
  tr:hover &:hover svg {
    stroke: white;
  }
`

export { RowStyled, CellStyled, CancelButton }
