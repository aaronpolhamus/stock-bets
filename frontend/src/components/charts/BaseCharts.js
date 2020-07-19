import React, { useEffect, useState, useContext, forwardRef } from 'react'
import { Line } from 'react-chartjs-2'
import { Form, Col, Row } from 'react-bootstrap'
import { apiPost, fetchGameData } from 'components/functions/api'
import { simplifyCurrency } from 'components/functions/formattingHelpers'
import { SectionTitle } from 'components/textComponents/Text'
import PropTypes from 'prop-types'
import { UserContext } from 'Contexts'

const BaseChart = forwardRef(({ data, yScaleType = 'count', maxXticks = 25, legends = true }, ref) => {
  // Check the documentation here: https://github.com/jerairrest/react-chartjs-2

  return (
    <Line
      ref={ref}
      data={data}
      options={{
        spanGaps: true,
        legend: {
          position: 'left',
          align: 'start',
          labels: {
            usePointStyle: true,
            padding: 10
          },
          display: legends
        },
        elements: {
          point: {
            radius: 0
          }
        },
        tooltips: {
          intersect: false,
          backgroundColor: 'rgba(0,0,0,0.5)'
        },
        scales: {
          yAxes: [
            {
              ticks: {
                callback: function (value, index, values, yScale = yScaleType) {
                  if (yScaleType === 'count') {
                    return value
                  }
                  if (yScaleType === 'dollar') {
                    if (parseInt(value) >= 1000) {
                      return simplifyCurrency(value)
                    } else {
                      return '$' + value
                    }
                  }
                  if (yScaleType === 'percent') {
                    // for now the pattern here is to convert percent data server-side then decorate it here
                    return value + '%'
                  }
                }
              }
            }
          ],
          xAxes: [{
            ticks: {
              autoSkip: true,
              maxTicksLimit: maxXticks
            }
          }]
        },
        // see zoom settings at https://github.com/chartjs/chartjs-plugin-zoom
        plugins: {
          zoom: {
            pan: {
              enabled: true,
              mode: 'xy',
              rangeMin: {
                x: null,
                y: null
              },
              rangeMax: {
                x: null,
                y: null
              },
              speed: 20,
              threshold: 10
            },
            zoom: {
              enabled: true,
              drag: true,
              mode: 'xy',
              rangeMin: {
                x: null,
                y: null
              },
              rangeMax: {
                x: null,
                y: null
              },
              speed: 0.1,
              threshold: 2,
              sensitivity: 3
            }
          }
        }
      }}
    />
  )
})

const UserDropDownChart = ({ gameId, endpoint, height, yScaleType = 'dollar', title }) => {
  const [data, setData] = useState({})
  const [usernames, setUsernames] = useState([])
  const [username, setUsername] = useState(null)
  const { user } = useContext(UserContext)

  useEffect(() => {
    const getSidebarStats = async () => {
      const data = await fetchGameData(gameId, 'get_leaderboard')
      setUsernames(data.records.map((entry) => entry.username))
    }
    getSidebarStats()

    const getGameData = async () => {
      const data = await apiPost(endpoint, {
        game_id: gameId,
        username: username,
        withCredentials: true
      })
      setData(data)
    }
    getGameData()

    if (username === null) {
      setUsername(user.username)
    }
  }, [gameId, username, endpoint])

  return (
    <>
      <Row>
        <Col xs={6} sm={9}>
          {title &&
            <SectionTitle>{title}</SectionTitle>}
        </Col>
        <Col xs={6} sm={3}>
          <Form.Control
            name='username'
            as='select'
            size='sm'
            onChange={(e) => setUsername(e.target.value)}
            value={username || user.username}
          >
            {usernames && usernames.map((element) => <option key={element} value={element}>{element}</option>)}
          </Form.Control>
        </Col>
      </Row>
      <BaseChart data={data} height={height} yScaleType={yScaleType} />
    </ >
  )
}

BaseChart.propTypes = {
  data: PropTypes.object,
  height: PropTypes.string,
  yScaleType: PropTypes.string,
  legends: PropTypes.bool,
  maxXticks: PropTypes.number
}

BaseChart.displayName = 'BaseChart'

UserDropDownChart.propTypes = {
  gameId: PropTypes.string,
  height: PropTypes.string,
  endpoint: PropTypes.string,
  yScaleType: PropTypes.string,
  legends: PropTypes.bool,
  title: PropTypes.string
}

export { BaseChart, UserDropDownChart }
