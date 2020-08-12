import React, { useEffect, useState, useRef, useContext } from 'react'
import { Row, Col } from 'react-bootstrap'
import { fetchGameData } from 'components/functions/api'
import { BaseChart } from 'components/charts/BaseCharts'
import { Leaderboard } from 'components/lists/Leaderboard'
import PropTypes from 'prop-types'
import { UserContext } from 'Contexts'

const FieldChart = ({ gameId, height }) => {
  const [data, setData] = useState({})
  const { user } = useContext(UserContext)
  const chartRef = useRef()

  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, 'get_field_chart')
      setData(data)
    }
    getGameData()
  }, [gameId])

  const handleSelectUser = () => {
    // This function colors the lines of the selected players in the field chart

    // We grab all the selected players with a querySelector
    const selectedCheckboxes = document.querySelectorAll('#leaderboard input:checked')

    // Shortcut for calling the instance of the chart
    // We referenced it with forwardRef in BaseCharts and in here with chartRef (via useRef)
    const fieldChartInstance = chartRef.current.chartInstance

    // Shortcut for the chart datasets which is the part that we are going to update in the chart
    const fieldChartDatasets = fieldChartInstance.data.datasets

    const selectedUsers = Object.keys(selectedCheckboxes).reduce((agg, index) => {
      const user = {
        name: selectedCheckboxes[index].value,
        color: selectedCheckboxes[index].getAttribute('color')
      }

      agg.push(user)
      return agg
    }, [])

    fieldChartDatasets.map((dataset, datasetIndex) => {
      // Check if the current user is in the list of selected users
      const selectedIndex = selectedUsers.findIndex((user, index) => {
        return user.name === dataset.label
      })

      if (selectedIndex === -1) {
        // if the selected index is -1 the user is not in the selected users list so we paint it gray
        dataset.borderColor = '#ABAAC6'
        dataset.borderWidth = 1
      } else {
        // if it is in the list we assign a color
        dataset.borderColor = selectedUsers[selectedIndex].color
        dataset.borderWidth = 2
      }
    })

    // Update the chart with the corresponging colors according to the selectedUsers (the 0 is to avoid an animation everytime the data is changed)
    fieldChartInstance.update(0)
  }

  // We make a copy of data to keep the original reference
  const dataCopy = { ...data }

  // This copies the data from the api query and modifies it to leave color only in the currentUser line
  if (data.datasets && data.datasets !== []) {
    const newDatasets = dataCopy.datasets.map((dataset, index) => {
      const newDataset = { ...dataset }
      if (dataset.label !== user.username) {
        newDataset.borderColor = '#ABAAC6'
        newDataset.borderWidth = 1
      }
      return newDataset
    }, [])

    dataCopy.datasets = newDatasets
  }

  return (
    <Row>
      <Col md={3}>
        <Leaderboard
          data={data.leaderboard} onSelect={handleSelectUser}
        />
      </Col>
      <Col md={9}>
        <BaseChart
          ref={chartRef}
          data={dataCopy}
          yScaleType='dollar'
          legends={false}
        />
      </Col>
    </Row>
  )
}

FieldChart.propTypes = {
  gameId: PropTypes.string,
  height: PropTypes.string
}

export { FieldChart }
