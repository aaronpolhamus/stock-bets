import React, { useState, useEffect } from 'react'
import api from 'services/api'
import { Row, Button, Form } from 'react-bootstrap'
import { Redirect } from 'react-router-dom'

const Admin = () => {
  const [redirect, setRedirect] = useState(false)
  const [validated, setValidated] = useState(false)
  const [stock, setStock] = useState(null)
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
    </>
  )
}

export { Admin }
