import React, { useEffect, useState, useRef, useContext } from 'react'
import PropTypes from 'prop-types'
import { fetchGameData } from 'components/functions/api'
import { BaseChart } from 'components/charts/BaseCharts'
import { ResponsiveTable } from 'components/tables/ResponsiveTable'

const CompoundChart = ({ gameId, chartDataEndpoint, tableDataEndpoint, tableOptions, tableId, selectableCell = 0, update }) => {
  const [tableData, setTableData] = useState()
  const [chartData, setChartData] = useState()
  const chartRef = useRef()
  const labelsRef = useRef()

  const getData = async () => {
    const tableDataQuery = await fetchGameData(gameId, tableDataEndpoint)
    const chartDataQuery = await fetchGameData(gameId, chartDataEndpoint)

    setChartData(chartDataQuery)
    setTableData(tableDataQuery)
  }

  const handleSelect = () => {

  }

  const formatLabelCell = (value) => {
    return (
      <label>
        <input type='checkbox'/>
        {value}
      </label>
    )
  }

  useEffect(() => {
    getData()
  }, [update])

  return (
    <>
      <BaseChart
        ref={chartRef}
        data={chartData}
        yScaleType='dollar'
        legends={false}
      />
      <ResponsiveTable
        ref={labelsRef}
        tableData={tableData}
        name={tableId}
        onSelect={handleSelect}
        tableOptions={{
          cellFormatByIndex: {
            [selectableCell]: formatLabelCell
          },
          showOnBreakpointDown: {
            '768px': [
              'symbol',
              'balance',
              'recent change',
              'value'
            ]
          }
        }}
      />
    </>
  )
}

CompoundChart.propTypes = {
  chartDataEndpoint: PropTypes.string,
  gameId: PropTypes.string,
  selectableCell: PropTypes.number,
  tableDataEndpoint: PropTypes.string,
  tableId: PropTypes.string,
  tableOptions: PropTypes.object,
  update: PropTypes.string
}

export { CompoundChart }
