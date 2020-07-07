import React, { useEffect, useState } from 'react'
import { Line } from 'react-chartjs-2'
import { Form } from 'react-bootstrap'
import { apiPost, fetchGameData } from 'components/functions/api'
import { simplifyCurrency } from 'components/functions/currencyHelpers'

const BaseChart = ({ data, height, yScaleType = 'dollar' }) => {
  // See here for interactive documentation: https://nivo.rocks/line/
  return (
    <Line
      data={data}
      options={{
        legend: {
          position: 'right',
          labels: {
            usePointStyle: true
          }
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
          ]
        }
      }}
    />
  )
}

const UserDropDownChart = ({ gameId, endpoint, height, yScaleType = 'dollar' }) => {
  const [data, setData] = useState([])
  const [myUsername, setMyUsername] = useState(null)
  const [usernames, setUsernames] = useState([])
  const [username, setUsername] = useState(null)
  useEffect(() => {
    const getSidebarStats = async () => {
      const data = await fetchGameData(gameId, 'get_sidebar_stats')
      setUsernames(data.records.map((entry) => entry.username))
    }
    getSidebarStats()

    const getUserInfo = async () => {
      const data = await apiPost('get_user_info', { withCredentials: true })
      setMyUsername(data.username)
    }
    getUserInfo()
  }, [])

  useEffect(() => {
    const getGameData = async () => {
      const data = await apiPost(endpoint, {
        game_id: gameId,
        username: username,
        withCredentials: true
      })
      setData(data)
    }
    getGameData()
  }, [gameId, username])
  return (
    <>
      <Form.Control
        name='username'
        as='select'
        defaultValue={null}
        onChange={(e) => setUsername(e.target.value)}
        defalutValue={myUsername}
      >
        {usernames && usernames.map((element) => <option key={element} value={element}>{element}</option>)}
      </Form.Control>
      <BaseChart data={data} height={height} yScaleType={yScaleType} />
    </ >
  )
}
export { BaseChart, UserDropDownChart }
