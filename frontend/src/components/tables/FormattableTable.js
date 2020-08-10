import React, { useState, useEffect, useRef } from 'react'
import { Table } from 'react-bootstrap'
import styled from 'styled-components'
import { breakpoints } from 'design-tokens'
import PropTypes from 'prop-types'
import { fetchGameData } from 'components/functions/api'

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
    border-color: ${props => props.$checkboxColor !== undefined ? props.$checkboxColor : 'var(--color-gray'};
  }
  input:checked + &::before{
    border-width: 8px;
  }
`

const StyledTd = styled.td`
  cursor: pointer;
`

const StyledTable = styled(Table)`
  td, th{
    &:first-child{
      text-align: left;
    }
    text-align: right;
  }
`

const simpleTokenize = (string) => {
  return string.toLowerCase().replace(/\s/g, '-')
}

const FormattableTable = (props) => {
  const [tableData, setTableData] = useState()

  let tableOutput = []
  let tableOutputtableInfo = []
  const getData = async () => {
    const tableDataQuery = await fetchGameData(props.gameId, props.endpoint)
    setTableData(tableDataQuery)
  }

  useEffect(() => {
    getData()
  }, [props.update])
  // The name option allows us to specify unique id's for the table headers. This for accesibility and for css manipulation in Formattable mode

  // The exclude option allows us to leave out data that we don't necessarily want represented in our table, e.g. the
  // order id for order cancellations
  // This function formats the value of the cell according to the tableOptions Object

  const handleRowClick = (rowIndex, add) => {
    const firstParam = Object.keys(tableOutputtableInfo[rowIndex])[0]
    const firstValue = tableOutputtableInfo[rowIndex][firstParam]

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
          tableOutputtableInfo[rowIndex]
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

    const formatCell = (key, value, index, row) => {
      // If there is no tableOptions or tableOptions has not a formatCell property the function returns the plain value
      let cellContent = value
      if (props.tableCellFormat !== undefined) {
        // We need to know if the key exists in the tableCellFormat Object
        const index = Object.keys(props.tableCellFormat).indexOf(key)

        if (index >= 0) {
          // If the key exists, we call the render function
          cellContent = props.tableCellFormat[key](value, row)
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
          <StyledTd
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
          </StyledTd>
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

  const buildRows = () => {
    return tableData.data.map((row, index) => {
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

  const buildHeaders = (headers) => {
    return headers.map((key, index) => {
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
  if (tableData && tableData.data) {
    // The data required when a row is selected, determined by the tableRowOutput prop
    tableOutputtableInfo = tableData.data.map((row, index) => {
      return Object.keys(props.tableRowOutput).reduce((agg, curr) => {
        return {
          ...agg,
          [curr]: row[props.tableRowOutput[curr]]
        }
      }, {})
    })

    return (
      <StyledTable
        hover={props.hover}
        striped={props.striped}
        id={props.name}
      >
        <thead>
          <tr>
            {buildHeaders(tableData.headers)}
          </tr>
        </thead>
        <tbody>{buildRows()}</tbody>
      </StyledTable>
    )
  }
  return null
}

FormattableTable.displayName = 'FormattableTable'
FormattableTable.propTypes = {
  tableData: PropTypes.object,
  tableCellFormat: PropTypes.object,
  tableCellCheckbox: PropTypes.number,
  tableRowOutput: PropTypes.object,
  exclude: PropTypes.array,
  endpoint: PropTypes.string,
  onRowSelect: PropTypes.func,
  gameId: PropTypes.string,
  update: PropTypes.string,
  name: PropTypes.string
}

FormattableTable.defaultProps = {
  tableRowOutput: {}
}

export { FormattableTable }
