import React, { useEffect, useState } from "react";
import axios from "axios";
import { Container, Row, Col, Button, Card, Form } from "react-bootstrap";
import { Typeahead } from "react-bootstrap-typeahead";
import {optionBuilder} from "../components/functions/forms"


const PlayGame = (props) => {
  const [gameInfo, setGameInfo] = useState({})
  const [orderTicket, setOrderTicket] = useState({})

  const fetchGameInfo = async (gameId) => {
    const resp = await axios.post("/api/play_game_landing", {game_id: gameId, withCredentials: true})
    setGameInfo(resp.data)
    setOrderTicket(resp.data)
  }

  useEffect(() => {
    fetchGameInfo(props.location.game_id) // ask matheus or julio about a better way to do this
  }, [])

  const handleTickerChange = async (ticker) => {
    let orderTicketCopy = {...orderTicket}
    orderTicketCopy["ticker"] = ticker
    setOrderTicket(orderTicketCopy)
  }

  const handleChange = (e) => {
    let orderTicketCopy = {...orderTicket}
    orderTicketCopy[e.target.name] = e.target.value
    setOrderTicket(orderTicketCopy)
  }

  const handleSubmit = async (e) => { 
    e.preventDefault()
    await axios.post("/api/place_order", orderTicket)
  }

  const stopLimitElement = () => {
    return (
      <Form.Group>
      <Form.Label>{orderTicket.order_type === "stop" ? "Stop": "Limit"} Price</Form.Label>
        <Form.Control name="stop_limit_price" as="input" onChange={handleChange}>
      </Form.Control>
      </Form.Group>
    )
  }

  console.log(orderTicket)

  return (
    <Container>
      <Row className="justify-content-md-left">
        <Button href="/">Home</Button>
      </Row>
      <Row className="justify-content-md-center">
          {gameInfo.title}
      </Row>
      <Form onSubmit={handleSubmit}>
        <Form.Group>
          <Typeahead
            id="typeahead-trades"
            name="tradeForm"
            options={["AMZN", "MSFT", "GOOG", "AAPL", "NFLX", "FB", "TSLA"]}
            placeholder="What are we trading today?"
            onChange={handleTickerChange}
          />
        </Form.Group>
      
        <Form.Group>
        <Form.Label>Buy or Sell</Form.Label>
          <Form.Control name="buy_or_sell" as="select" 
            defaultValue={gameInfo.default_buy_sell} onChange={handleChange}>
            {gameInfo.buy_sell_options && optionBuilder(gameInfo.buy_sell_options)}
          </Form.Control>
        </Form.Group>
        
        <Row>
          <Col>
            <Form.Group>
            <Form.Label>{orderTicket.shares_or_usd && orderTicket.shares_or_usd === "Shares" ? "Quantity" : "Amount"}</Form.Label>
              <Form.Control name="amount" as="input" 
                defaultValue={gameInfo.default_buy_sell} onChange={handleChange}>
              </Form.Control>
            </Form.Group>
          </Col>
          <Col>
            <Form.Group>
            <Form.Label>Shares or USD</Form.Label>
              <Form.Control name="shares_or_usd" as="select" 
                defaultValue={gameInfo.quantity_type} onChange={handleChange}>
                {gameInfo.quantity_options && gameInfo.quantity_options.map((value) => <option>{value}</option>)}
              </Form.Control>
            </Form.Group>
          </Col>
        </Row>

        <Row>
          <Col>
            <Form.Group>
            <Form.Label>Order type</Form.Label>
              <Form.Control name="order_type" as="select" 
                defaultValue={gameInfo.order_type} onChange={handleChange}>
                {gameInfo.order_type_options && optionBuilder(gameInfo.order_type_options)}
              </Form.Control>
            </Form.Group>
          </Col>
          <Col>
            {["stop", "limit"].includes(orderTicket.order_type) && stopLimitElement()}
          </Col>
        </Row>

        <Form.Group>
        <Form.Label>Time in Force</Form.Label>
          <Form.Control name="time_in_force" as="select" 
            defaultValue={gameInfo.time_in_force} onChange={handleChange}>
            {gameInfo.time_in_force_options && optionBuilder(gameInfo.time_in_force_options)}
          </Form.Control>
        </Form.Group>

        <Button variant="primary" type="submit">Submit {orderTicket.buy_or_sell === "buy" ? "Buy" : "Sell"} Order</Button>
      </Form>
    </Container>
  )  
}

export {PlayGame};
