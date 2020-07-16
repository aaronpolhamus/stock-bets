import React, { useState, useEffect } from 'react'
import api from 'services/api'
import { Row, Button, Form } from 'react-bootstrap'
import { Redirect } from 'react-router-dom'
import { apiPost } from 'components/functions/api'
import { BaseChart } from 'components/charts/BaseCharts'

const Admin = () => {
  const [redirect, setRedirect] = useState(false)
  const [validated, setValidated] = useState(false)
  const [stock, setStock] = useState(null)
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

  const fetchPrice = async (symbol) => {
    await api.post('/api/fetch_price', {
      symbol: symbol,
      withCredentials: true
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    fetchPrice(stock)
  }

  const handleChange = (e) => {
    console.log(e.target.value)
    setStock(e.target.value)
  }
  if (redirect) return <Redirect to='/' />
  if (!validated) return <></>
  return (
    <>
      <Form onSubmit={handleSubmit}>
        <br />
        <Form.Group>
          <Form.Control
            name='check_stock_price'
            as='input'
            onChange={handleChange}
            placeholder='Pick a stock to price check'
          />
        </Form.Group>
        <Button variant='primary' type='submit'>
          Fetch
        </Button>
      </Form>
      <br />
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
      <br />
      {gamesPerUserData && <BaseChart data={gamesPerUserData} />}
      <br />
      {ordersPerUserData && <BaseChart data={ordersPerUserData} />}
    </>
  )
}

export { Admin }
