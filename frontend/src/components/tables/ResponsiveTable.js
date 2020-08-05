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

const renderRows = (tableData, name, exclude = ['order_id']) => {
  // The name option allows us to specify unique id's for the table headers. This for accesibility and for css manipulation in responsive mode

  // The exclude option allows us to leave out data that we don't necessarily want represented in our table, e.g. the
  // order id for order cancellations

  return tableData.data.map((row, index) => {
    return <tr key={index}>{renderRow(row, tableData.headers, name, exclude)}</tr>
  })
}

const renderHeaders = (headers, name) => {
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

const simpleTokenize = (string) => {
  return string.toLowerCase().replace(/\s/g, '-')
}

const ResponsiveTable = ({ tableData, tableOptions, name, ...props }) => {
  if (tableData && tableData.data) {
    return (
      <Table {...props}>
        <thead>
          <tr>{renderHeaders(tableData.headers, name)}</tr>
        </thead>
        <tbody>{renderRows(tableData, name)}</tbody>
      </Table>
    )
  }
  return null
}

ResponsiveTable.propTypes = {
  tableData: PropTypes.object,
  tableOptions: PropTypes.object,
  name: PropTypes.string
}

export { ResponsiveTable }
