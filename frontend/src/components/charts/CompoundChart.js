import React, { useEffect, useState, useRef } from 'react'
import PropTypes from 'prop-types'
import { fetchGameData } from 'components/functions/api'
import { BaseChart } from 'components/charts/BaseCharts'

const CompoundChart = ({ children, gameId, chartDataEndpoint, update, legends }) => {
  const [chartData, setChartData] = useState()
  const chartRef = useRef()

  const getData = async () => {
    const chartDataQuery = await fetchGameData(gameId, chartDataEndpoint)
    setChartData(chartDataQuery)
  }

  const handleSelect = () => {
    console.log('handled select')
  }

  useEffect(() => {
    getData()
  }, [update])

  const Children = children

  return (
    <>
      <BaseChart
        ref={chartRef}
        data={chartData}
        yScaleType='dollar'
        legends={legends}
      />
      {
        children &&
        <Children
          handleSelect={handleSelect}
        />
      }
    </>
  )
}

CompoundChart.propTypes = {
  chartDataEndpoint: PropTypes.string,
  gameId: PropTypes.string,
  tableCellCheckbox: PropTypes.number,
  tableDataEndpoint: PropTypes.string,
  tableId: PropTypes.string,
  tableCellFormat: PropTypes.object,
  update: PropTypes.string,
  legends: PropTypes.bool,
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ])
}

export { CompoundChart }
