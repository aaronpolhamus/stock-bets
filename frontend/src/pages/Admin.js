import React, { useState, useEffect } from 'react'
import api from 'services/api'
import { Row, Button, Form } from 'react-bootstrap'
import { Redirect } from 'react-router-dom'
import { apiPost } from 'components/functions/api'
import { BaseChart } from 'components/charts/BaseCharts'

const Admin = () => {
  const [redirect, setRedirect] = useState(false)
  const [validated, setValidated] = useState(false)
  const [username, setUsername] = useState(null)
  const [gamesPerUserData, setGamesPerUserData] = useState(null)
  const [ordersPerUserData, setOrdersPerUserData] = useState(null)

  useEffect(() => {
    const validateAdmin = async () => {
      try {
        await api.post('/api/verify_admin')
        setValidated(true)
      } catch (e) {
        console.log(e)
        window && window.alert('Admins only')
        setRedirect(true)
      }
    }
    validateAdmin()
  }, [])

  useEffect(() => {
    const getGamesPerUserData = async () => {
      const data = await apiPost('games_per_users')
      setGamesPerUserData(data)
    }
    getGamesPerUserData()
  }, [validated])

  useEffect(() => {
    const getOrdersPerUserData = async () => {
      const data = await apiPost('orders_per_active_user')
      setOrdersPerUserData(data)
    }
    getOrdersPerUserData()
  }, [validated])

  const changeUser = async (username) => {
    await api.post('/api/change_user', { username: username })
      .then(() => setRedirect(true))
  }

  const handleSubmitChangeUser = (e) => {
    e.preventDefault()
    changeUser(username)
  }

  const handleChangeUser = (e) => {
    setUsername(e.target.value)
  }
  if (redirect) return <Redirect to='/' />
  if (!validated) return <></>
  return (
    <>
      <Row>
        <Button onClick={async () => api.post('/api/refresh_game_statuses')}>
          Refresh all game statuses
        </Button>
      </Row>
      <br />
      <Row>
        <Button onClick={async () => api.post('/api/refresh_metrics')}>
          Refresh KPIs
        </Button>
      </Row>
      <Row>
        <Form onSubmit={handleSubmitChangeUser}>
          <br />
          <Form.Group>
            <Form.Control
              name='change_user'
              as='input'
              onChange={handleChangeUser}
              placeholder='What user do you want to check out?'
            />
          </Form.Group>
          <Button variant='primary' type='submit'>
            Switch
          </Button>
        </Form>
      </Row>
      <br />
      {gamesPerUserData && <BaseChart data={gamesPerUserData} />}
      <br />
      {ordersPerUserData && <BaseChart data={ordersPerUserData} />}
    </>
  )
}

export { Admin }
