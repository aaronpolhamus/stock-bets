import React, { useState, useEffect } from 'react'
import { Table } from 'react-bootstrap'
import styled from 'styled-components'
import { breakpoints } from 'design-tokens'
import PropTypes from 'prop-types'
import { apiPost } from 'components/functions/api'
import { toCurrency, toFormattedDate } from 'components/functions/formattingHelpers'

const CheckboxGroup = styled.span`
  cursor: pointer;
  input{
    display: none;
  }

`
const CheckboxText = styled.span`
  display: flex;
  align-items: center;
  &::before{
    content: '';
    display: inline-block;
    width: 16px;
    height: 16px;
    margin-right: var(--space-100); 
    border-width: 3px;
    border-style: solid;
    border-radius: 50%;
    transition: border-width .3s;
    border-color: ${props => props.$checkboxColor !== undefined ? props.$checkboxColor : 'var(--color-text-gray)'};
  }
  input:checked + &::before{
    border-width: 8px;
  }
  tr:hover &::before{
    border-width: 6px;
  }
  tr:hover input:checked + &::before{
    border-width: 8px;
  }
`

const simpleTokenize = (string) => {
  return string.toLowerCase().replace('%', '').replace(/\s/g, '-')
}

const simpleFormat = (value, format) => {
  format.map((operator, index) => {
    switch (operator) {
      case 'currency':
        value = toCurrency(value)
        break
      case 'percentage':
        value = `${(value * 100).toFixed(3)}%`
        break
      case 'date':
        value = toFormattedDate(value)
        break
      case 'bold':
        value = (<strong>{value}</strong>)
        break
      default :
        break
    }
  }, [])
  return value
}

const sorter = (array, key, order) => {
  const cleanValue = `${array[0][key]}`.replace('$', '')

  const isString = isNaN(parseFloat(cleanValue))

  return array.sort((a, b) => {
    switch (isString) {
      case false:
        a = parseFloat(a[key])
        b = parseFloat(b[key])
        break
      default:
        a = a[key]
        b = b[key]
        break
    }

    switch (order) {
      case 'DESC':
        return a > b ? -1 : 1
      default:
        return a < b ? -1 : 1
    }
  })
}

// The name option allows us to specify unique id's for the table headers. This for accesibility and for css manipulation in Formattable mode
// The exclude option allows us to leave out data that we don't necessarily want represented in our table, e.g. the order id for order cancellations
const StyledTable = styled(Table)`
  td{
    cursor: pointer
  }
  td, th{
    &:first-child{
      text-align: left;
    }
    text-align: right;
  }
  ${props => props.$responsiveStyles}
`
const FormattableTable = (props) => {
  const [tableData, setTableData] = useState()

  let tableOutput = []
  let tableOutputs = []
  const getData = async () => {
    // const tableDataQuery = await fetchGameData(props.gameId, props.endpoint)

    const queryPostData = {
      game_id: props.gameId
    }
    if (props.username) {
      queryPostData.username = props.username
    }
    await apiPost(props.endpoint, {
      ...queryPostData,
      withCredentials: true
    }).then((response) => {
      setTableData(response)
    })
  }

  useEffect(() => {
    getData()
  }, [props.update])

  const createResponsiveStyles = () => {
    let styles = ''
    if (props.showColumns && tableData) {
      tableData.headers.map((key, index) => {
        Object.keys(props.showColumns).map((col, colIndex) => {
          styles += `@media screen and (max-width: ${breakpoints[col]}){`
          if (props.showColumns[col].indexOf(key) < 0) {
            styles += `
              #${props.name}-${simpleTokenize(key)},
              [headers="${props.name}-${simpleTokenize(key)}"] {
                display: none;
              }
            `
          }
          styles += '}'
        })
      })
    }
    return styles
  }

  const handleRowClick = (rowIndex, add) => {
    const firstParam = Object.keys(tableOutputs[rowIndex])[0]
    const firstValue = tableOutputs[rowIndex][firstParam]

    switch (add) {
      case false: {
        const index = tableOutput.findIndex((element) => {
          return element[firstParam] === firstValue
        })
        tableOutput.splice(index, 1)
        break
      }
      default:

        tableOutput = [
          ...tableOutput,
          tableOutputs[rowIndex]
        ]
        break
    }

    props.onRowSelect && props.onRowSelect(tableOutput)
  }

  const SelectableRow = props => {
    const [selected, setSelected] = useState(false)

    // if a tableCellCheckbox is defined, it adds a checkbox to the cell number
    const addCheckboxToCell = (cellContent, value, row) => {
      return (
        <CheckboxGroup>
          <input
            type='checkbox'
            defaultChecked={selected}
            value={value}
          />
          <CheckboxText $checkboxColor={row.color}>
            {cellContent}
          </CheckboxText>
        </CheckboxGroup>
      )
    }

    // This function applies a render function to a cell, making it able to have any format
    const formatCell = (key, value, index, row) => {
      // If there is no tableOptions or tableOptions has not a formatCell property the function returns the plain value
      let cellContent = value
      if (props.simpleFormatCells !== undefined) {
        const index = Object.keys(props.simpleFormatCells).indexOf(key)

        if (index >= 0) {
          const format = props.simpleFormatCells[key]
          cellContent = simpleFormat(value, format)
        }
      }
      if (props.formatCells !== undefined) {
        // We need to know if the key exists in the formatCells Object
        const index = Object.keys(props.formatCells).indexOf(key)

        if (index >= 0) {
          // If the key exists, we call the render function
          // We can use the value of the cell and we can access the values of the whole rows
          cellContent = props.formatCells[key](value, row)
        }
      }

      if (props.tableCellCheckbox !== undefined && props.tableCellCheckbox === index) {
        return addCheckboxToCell(cellContent, value, row)
      }
      return cellContent
    }

    const buildRow = (row, rowIndex) => {
      return tableData.headers.map((key, index) => {
        if (props.exclude && props.exclude.includes(key)) {
          return null
        }

        return (
          <td
            key={index}
            onClick={() => {
              if (selected) {
                setSelected(false)
                handleRowClick(rowIndex, false)
              } else {
                setSelected(true)
                handleRowClick(rowIndex, true)
              }
            }}
            headers={`${props.name}-${simpleTokenize(key)}`}
          >
            {formatCell(key, row[key], index, row)}
          </td>
        )
      })
    }
    return (
      <tr
        key={props.index}
      >
        {buildRow(props.row, props.index)}
      </tr>
    )
  }
  SelectableRow.propTypes = {
    row: PropTypes.object,
    index: PropTypes.number
  }

  const buildRows = (rowsData) => {
    return rowsData.map((row, index) => {
      if (props.excludeRows && props.excludeRows(row)) {
        return null
      }
      return (
        <SelectableRow
          key={index}
          row={row}
          index={index}
          {...props}
        />
      )
    })
  }

  const buildHeaders = (headersData) => {
    return headersData.map((key, index) => {
      if (props.exclude && props.exclude.includes(key)) {
        return null
      }
      return (
        <th
          key={key}
          id={`${props.name}-${simpleTokenize(key)}`}
        >
          {key}
        </th>
      )
    })
  }

  if (tableData && tableData.data.length > 0) {
    // Sorts the table data by the key provided if sortBy prop is present
    if (props.sortBy) {
      tableData.data = sorter(tableData.data, props.sortBy, props.sortOrder)
    }

    // What format you expect to be outputted when you select rows in the table
    tableOutputs = tableData.data.map((row, index) => {
      return props.formatOutput ? props.formatOutput(row) : row
    })

    return (
      <StyledTable
        hover={props.hover}
        striped={props.striped}
        id={props.name}
        $responsiveStyles={createResponsiveStyles()}
      >
        <thead>
          <tr>
            {buildHeaders(tableData.headers)}
          </tr>
        </thead>
        <tbody>{buildRows(tableData.data)}</tbody>
      </StyledTable>
    )
  }
  return null
}

FormattableTable.displayName = 'FormattableTable'
FormattableTable.propTypes = {
  endpoint: PropTypes.string,
  exclude: PropTypes.array,
  excludeRows: PropTypes.func,
  formatOutput: PropTypes.func,
  gameId: PropTypes.string,
  hover: PropTypes.bool,
  name: PropTypes.string,
  onRowSelect: PropTypes.func,
  showColumns: PropTypes.object,
  sortBy: PropTypes.string,
  sortOrder: PropTypes.string,
  simpleFormatCells: PropTypes.object,
  striped: PropTypes.bool,
  tableCellCheckbox: PropTypes.number,
  formatCells: PropTypes.object,
  tableData: PropTypes.object,
  tableRowOutput: PropTypes.object,
  update: PropTypes.string,
  username: PropTypes.string
}

FormattableTable.defaultProps = {
  tableRowOutput: {},
  sortOrder: 'ASC'
}

export { FormattableTable }
