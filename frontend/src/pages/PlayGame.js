import React, { useEffect, useState } from "react";
import axios from "axios";
import { Container, Row, Col, Button, Card, Form, Dropdown } from "react-bootstrap";
import { Typeahead } from "react-bootstrap-typeahead";

const PlayGame = (props) => {
  const [gameInfo, setGameInfo] = useState({})
  const [orderTicket, setOrderTicket] = useState({})
  const [buyOrSell, setbuyOrSell] = useState("buy")
  const [amountType, setAmountType] = useState("quantity")

  const fetchGameInfo = async (gameId) => {
    const resp = await axios.post("/api/play_game_landing", {game_id: gameId, withCredentials: true})
    setGameInfo(resp.data)
  }

  useEffect(() => {
    fetchGameInfo(props.location.game_id)
  }, [])

  const handleTickerChange = async (ticker) => {
    return null
  }

  const handleIsBuyOrder = (e) => {
    setbuyOrSell(e.target.value)
  }

  const handleIsQuantity = (e) => {
    setAmountType(e.target.value)
  }

  const handleChange = (e) => {
    return null
  }

  const handleSubmit = (e) => { 
    e.preventDefaullt()
    return null
  }

  console.log(gameInfo)

  return(
    <Container fluid="md">
      <Row className="justify-content-md-left">
        <Button href="/">Home</Button>
      </Row>
      <Row className="justify-content-md-center">
          {gameInfo.title}
      </Row>
      <Row>
        <Col>
          <Form onSubmit={handleSubmit}>
            <Row>
              <Typeahead
                id="typeahead-trades"
                name="tradeForm"
                options={["AMZN", "MSFT", "GOOG", "AAPL", "NFLX", "FB", "TSLA"]}
                placeholder="What are we trading?"
                onChange={handleTickerChange}
            />
            </Row>
            <Row>STOCK TITLE PLACEHOLDER</Row>
            <Row>
              <Col>
                Placeholder price ($)
              </Col>
              <Col>
                Placeholder change data (%)
              </Col>
            </Row>
              <Card>
                <Row>
                  <Button type="button" value="buy" variant={buyOrSell === "buy" ? "outline-primary" : "outline-secondary"} onClick={handleIsBuyOrder}>Buy Order</Button>
                  <Button type="button" value="sell" variant={buyOrSell === "sell" ? "outline-primary" : "outline-secondary"} onClick={handleIsBuyOrder}>Sell Order</Button>
                </Row>
                <Row>
                  <Col>
                    <Form.Label>{buyOrSell === "quantity" ? "Quantity" : "Amount"}</Form.Label>
                    <Form.Control type="number" onChange={handleChange}/>
                  </Col>
                  <Col>
                    <Button type="button" value="quantity" variant={amountType === "quantity" ? "outline-primary" : "outline-secondary"} onClick={handleIsQuantity}>Shares</Button>
                    <Button type="button" value="usd" variant={amountType === "usd" ? "outline-primary" : "outline-secondary"} onClick={handleIsQuantity}>USD</Button>
                  </Col>
                </Row>
                <Row>
                  <Col>
                    <Dropdown>
                    </Dropdown>
                  </Col>
                  <Col>

                  </Col>
                </Row>
            
            </Card>
            <Row className="justify-content-md-left">
              <Button variant="primary" type="submit">Submit {buyOrSell === "buy" ? "Buy" : "Sell"} Order</Button>
            </Row>
          </Form>
        </Col>
        <Col>
          <Row>

          </Row>
          <Row>

          </Row>
        </Col>
      </Row>
    </Container>
  )
}

export {PlayGame};
