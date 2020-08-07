import React, { useState, useEffect } from 'react'
import { Table } from 'react-bootstrap'
import styled from 'styled-components'
import { breakpoints } from 'design-tokens'
import PropTypes from 'prop-types'
import { fetchGameData } from 'components/functions/api'

const simpleTokenize = (string) => {
  return string.toLowerCase().replace(/\s/g, '-')
}

const FormattableTable = ({ endpoint, gameId, tableCellFormat, name, update, onRowSelect, tableCellCheckbox, exclude = ['order_id'], ...props }) => {
  const [tableData, setTableData] = useState()
  const getData = async () => {
    const tableDataQuery = await fetchGameData(gameId, endpoint)
    setTableData(tableDataQuery)
  }

  useEffect(() => {
    getData()
  }, [update])
  // The name option allows us to specify unique id's for the table headers. This for accesibility and for css manipulation in Formattable mode

  // The exclude option allows us to leave out data that we don't necessarily want represented in our table, e.g. the
  // order id for order cancellations
  // This function formats the value of the cell according to the tableOptions Object
  const formatCell = (key, value, index) => {
    // If there is no tableOptions or tableOptions has not a formatCell property the function returns the plain value
    let cellContent = value
    if (tableCellFormat !== undefined) {
      // We need to know if the key exists in the tableCellFormat Object
      const index = Object.keys(tableCellFormat).indexOf(key)

      if (index >= 0) {
        // If the key exists, we call the render function
        cellContent = tableCellFormat[key](value)
      }
    }

    if (tableCellCheckbox !== undefined && tableCellCheckbox === index) {
      return addCheckboxToCell(cellContent, name)
    }
    return cellContent
  }

  const handleRowSelect = () => {
    onRowSelect()
  }

  const addCheckboxToCell = (cellContent, name) => {
    return (
      <label>
        <input
          type='checkbox'
          name={name}
          onInput={handleRowSelect}
        />
        {cellContent}
      </label>
    )
  }

  const renderRow = (row) => {
    return tableData.headers.map((key, index) => {
      if (exclude.includes(key)) {
        return null
      }
      return (
        <td
          key={index}
          headers={`${name}-${simpleTokenize(key)}`}
        >

          {formatCell(key, row[key], index)}
        </td>
      )
    })
  }

  const renderRows = () => {
    return tableData.data.map((row, index) => {
      return <tr key={index}>{renderRow(row)}</tr>
    })
  }

  const renderHeaders = (headers) => {
    return headers.map((key, index) => {
      if (exclude.includes(key)) {
        return null
      }
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

  if (tableData && tableData.data) {
    return (
      <Table {...props}>
        <thead>
          <tr>{renderHeaders(tableData.headers)}</tr>
        </thead>
        <tbody>{renderRows()}</tbody>
      </Table>
    )
  }
  return null
}

FormattableTable.propTypes = {
  tableData: PropTypes.object,
  tableCellFormat: PropTypes.object,
  tableCellCheckbox: PropTypes.number,
  exclude: PropTypes.array,
  endpoint: PropTypes.string,
  onRowSelect: PropTypes.func,
  gameId: PropTypes.string,
  update: PropTypes.string,
  name: PropTypes.string
}

export { FormattableTable }
