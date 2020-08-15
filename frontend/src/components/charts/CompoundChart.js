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

  const handleSelectedLines = (selectedLines) => {
    // Shortcut for calling the instance of the chart
    // We referenced it with forwardRef in BaseCharts and in here with chartRef (via useRef)
    const fieldChartInstance = chartRef.current.chartInstance

    // Shortcut for the chart datasets which is the part that we are going to update in the chart
    const fieldChartDatasets = fieldChartInstance.data.datasets

    fieldChartDatasets.map((dataset, datasetIndex) => {
      // Check if the current user is in the list of selected users
      const selectedIndex = selectedLines.findIndex((line, index) => {
        return line.label === dataset.label
      })

      if (selectedIndex === -1) {
        // if the selected index is -1 the user is not in the selected users list so we paint it gray
        dataset.borderColor = '#ABAAC6'
        dataset.borderWidth = 1
      } else {
        // if it is in the list we assign a color
        dataset.borderColor = selectedLines[selectedIndex].color
        dataset.borderWidth = 2
      }
    })

    // Update the chart with the corresponging colors according to the selectedUsers (the 0 is to avoid an animation everytime the data is changed)
    fieldChartInstance.update(0)
  }

  useEffect(() => {
    getData()
  }, [update])

  const Children = children // transforms children to jsx node

  // Set Data for Chart
  // We make a copy of data to keep the original reference
  const dataCopy = { ...chartData }
  // This copies the data from the api query and modifies it to leave color only in the currentUser line

  if (chartData && chartData.datasets !== []) {
    const newDatasets = dataCopy.datasets.map((dataset, index) => {
      const newDataset = { ...dataset }
      newDataset.borderColor = '#ABAAC6'
      newDataset.borderWidth = 1
      return newDataset
    }, [])

    dataCopy.datasets = newDatasets
  }
  return (
    <>
      <BaseChart
        ref={chartRef}
        data={dataCopy}
        yScaleType='dollar'
        legends={legends}
      />
      {
        children &&
        <Children
          handleSelectedLines={handleSelectedLines}
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
    PropTypes.func,
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ])
}

export { CompoundChart }
