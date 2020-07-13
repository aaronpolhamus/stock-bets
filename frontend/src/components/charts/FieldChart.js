import React, { useEffect, useState } from 'react'
import { Row, Col } from 'react-bootstrap'
import { fetchGameData } from 'components/functions/api'
import { BaseChart } from 'components/charts/BaseCharts'
import { Leaderboard } from 'components/lists/Leaderboard'
import PropTypes from 'prop-types'

const FieldChart = ({ gameId, height }) => {
  const [data, setData] = useState([])

  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, 'get_field_chart')
      setData(data)
    }
    getGameData()
  }, [gameId])

  const handleSelectUser = (selectedPlayer) => {
    console.log(selectedPlayer.username)
  }
  console.log(data)
  return (
    <Row>
      <Col md={3}>
        <Leaderboard data={data.leaderboard} onSelect={(player) => {
          handleSelectUser(player)
        }
        }
        />
      </Col>
      <Col md={9}>
        <BaseChart data={data} height={height} legends={false}/>
      </Col>
    </Row>
  )
}

FieldChart.propTypes = {
  gameId: PropTypes.number,
  height: PropTypes.string
}

export { FieldChart }
