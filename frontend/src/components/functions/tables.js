import React from 'react'
import { Table } from 'react-bootstrap'
import styled from 'styled-components'
import { breakpoints } from 'design-tokens'
import PropTypes from 'prop-types'

const renderRow = (row, headers, name, exclude = ['order_id']) => {
  return headers.map((key, index) => {
    if (exclude.includes(key)) {
      return null
    }
    return (
      <td
        key={index}
        headers={`${name}-${simpleTokenize(key)}`}
      >
        {row[key]}
      </td>
    )
  })
}

const makeRows = (tableData, name, exclude = ['order_id']) => {
  // The name option allows us to specify unique id's for the table headers. This for accesibility and for css manipulation in responsive mode

  // The exclude option allows us to leave out data that we don't necessarily want represented in our table, e.g. the
  // order id for order cancellations

  return tableData.data.map((row, index) => {
    return <tr key={index}>{renderRow(row, tableData.headers, name, exclude)}</tr>
  })
}

const makeHeader = (headers, name) => {
  return headers.map((key, index) => {
    return (
      <th
        key={key}
        id={`${name}-${simpleTokenize(key)}`}
      >
        {key}
      </th>
    )
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

const simpleTokenize = (string) => {
  return string.toLowerCase().replace(/\s/g, '-')
}

const AutoTable = (props) => {
  if (props.tabledata.data) {
    return (
      <Table {...props}>
        <thead>
          <tr>{makeHeader(props.tabledata.headers, props.name)}</tr>
        </thead>
        <tbody>{makeRows(props.tabledata, props.name)}</tbody>
      </Table>
    )
  }
  return null
}

AutoTable.propTypes = {
  tabledata: PropTypes.object,
  name: PropTypes.string
}

export { AutoTable, makeHeader, makeRows, makeCustomHeader }
