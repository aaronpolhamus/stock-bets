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

    // Reset every line to gray
    fieldChartDatasets.map((dataset, datasetIndex) => {
      dataset.borderColor = 'ABAAC6'
      dataset.borderWidth = 1
    })

    // Go through all the selected players (checkboxes)
    Object.keys(selectedCheckboxes).map((index) => {
      // Shortcut for the checkbox value in which the username is stored
      const selectedUsername = selectedCheckboxes[index].value

      // We grab the corresponding user color from the color attribute
      const selectedUsernameColor = selectedCheckboxes[index].getAttribute('color')

      // We go to the dataset which contains the username of the selected player and change it's color and borderWidth
      fieldChartDatasets.findIndex((dataset, datasetIndex) => {
        if (dataset.label === selectedUsername) {
          dataset.borderColor = selectedUsernameColor
          dataset.borderWidth = 2
        }
      })
    })

    // Update the chart with the corresponging colors according to the selectedUsers (the 0 is to avoid an animation everytime the data is changed)
    fieldChartInstance.update(0)
  }

  const dataCopy = { ...data }

  // I had the option to invoke handleSelectUser here, but with this method we avoid a flash of color and then changing to gray

  // What this does id that copies the data from the api query and modifies it to leave color only in the currentUser line
  if (data.datasets && data.datasets !== []) {
    const newDatasets = dataCopy.datasets.map((dataset, index) => {
      const newDataset = { ...dataset }
      if (dataset.label !== user.username) {
        newDataset.borderColor = 'ABAAC6'
        newDataset.borderWidth = 1
      }
      return newDataset
    }, [])

    dataCopy.datasets = newDatasets
  }
  console.log(typeof dataCopy)
  return (
    <Row>
      <Col md={3}>
        <Leaderboard
          data={data.leaderboard} onSelect={handleSelectUser}
        />
      </Col>
      <Col md={9}>
        <BaseChart ref={chartRef} data={dataCopy} height={height} yScaleType='dollar' legends={false} />
      </Col>
    </Row>
  )
}

FieldChart.propTypes = {
  gameId: PropTypes.string,
  height: PropTypes.string
}

export { FieldChart }
