import React from 'react'
import { Table } from 'react-bootstrap'
import styled from 'styled-components'
import { breakpoints } from 'design-tokens'

const renderRow = (row, headers, exclude = ['order_id']) => {
  return headers.map((key, index) => {
    if (exclude.includes(key)) {
      return null
    }
    return <td key={index}>{row[key]}</td>
  })
}

const makeRows = (tableData, exclude = ['order_id']) => {
  // The exclude option allows us to leave out data that we don't necessarily want represented in our table, e.g. the
  // order id for order cancellations
  return tableData.data.map((row, index) => {
    return <tr key={index}>{renderRow(row, tableData.headers, exclude)}</tr>
  })
}

const makeHeader = (headers) => {
  return headers.map((key, index) => {
    return <th key={key}>{key}</th>
  })
}

const StyledTh = styled.th`
  text-align: ${props => props.$align || 'left'};
  @media screen and (max-width: ${props => props.$breakpoint}){
    display: none;
  }
`

const makeCustomHeader = (headers) => {
  return headers.map((header, index) => {
    const breakpoint = breakpoints[header.hideOnBreakpoint]
    return (
      <StyledTh
        key={index}
        $align={header.align}
        $breakpoint={breakpoint}
      >
        {header.value}
      </StyledTh>
    )
  })
}

const AutoTable = (props) => {
  if (props.tabledata.data) {
    return (
      <Table {...props}>
        <thead>
          <tr>{makeHeader(props.tabledata.headers)}</tr>
        </thead>
        <tbody>{makeRows(props.tabledata)}</tbody>
      </Table>
    )
  }
  return null
}

export { AutoTable, makeHeader, makeRows, makeCustomHeader }
