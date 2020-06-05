import React, { useEffect, useState } from "react";
import api from "services/api";
import { Row, Col, Button, Form } from "react-bootstrap";
import Autosuggest from "react-autosuggest";
import { optionBuilder } from "components/functions/forms";

// request -> guardar datos -> actualizar form -> limpiar datos -> request submit

const PlaceOrder = ({ gameId }) => {
  const [gameInfo, setGameInfo] = useState({});
  const [orderTicket, setOrderTicket] = useState({});
  const [symbolSuggestions, setSymbolSuggestions] = useState([]);
  const [symbolValue, setSymbolValue] = useState("");
  const [symbolLabel, setSymbolLabel] = useState("");
  const [priceData, setPriceData] = useState(null);
  const [intervalId, setintervalId] = useState(null);

  useEffect(() => {
    fetchGameInfo(gameId);
  }, [gameId]);

  const fetchGameInfo = async (gameId) => {
    const resp = await api.post("/api/order_form_defaults", {
      game_id: gameId,
      withCredentials: true,
    });
    setGameInfo(resp.data);
    setOrderTicket(resp.data);
  };

  const handleChange = (e) => {
    let orderTicketCopy = { ...orderTicket };
    orderTicketCopy[e.target.name] = e.target.value;
    setOrderTicket(orderTicketCopy);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    let orderTicketCopy = { ...orderTicket };
    orderTicketCopy["symbol"] = symbolValue;
    orderTicketCopy["market_price"] = priceData.price;
    setOrderTicket(orderTicketCopy);
    await api.post("/api/place_order", orderTicket);
  };

  const getSuggestionValue = (suggestion) => {
    setSymbolLabel(suggestion.label);
    return suggestion.symbol;
  };

  const renderSuggestion = (suggestion) => {
    return <span>{suggestion.label}</span>;
  };

  const onSymbolChange = (event, { newValue, method }) => {
    setSymbolValue(newValue);
  };

  const onSuggestionsFetchRequested = async (text) => {
    const response = await api.post("/api/suggest_symbols", {
      text: text.value,
      withCredentials: true,
    });
    setSymbolSuggestions(response.data);
  };

  const onSuggestionsClearRequested = () => {
    setSymbolSuggestions([]);
  };

  const onSuggestionSelected = (
    event,
    { suggestion, suggestionValue, suggestionIndex, sectionIndex, method }
  ) => {
    // This part of the code handles the dynamically-updating price ticker when a stock pick gets made. We need to clear the old interval and set
    // a new one each time there is a change
    if (intervalId) {
      clearInterval(intervalId);
    }

    fetchPrice(suggestionValue);
    const newIntervalID = setInterval(() => {
      fetchPrice(suggestionValue);
    }, 2500);
    setintervalId(newIntervalID);
  };

  const stopLimitElement = () => {
    return (
      <Form.Group>
        <Form.Label>
          {orderTicket.order_type === "stop" ? "Stop" : "Limit"} Price
        </Form.Label>
        <Form.Control
          name="stop_limit_price"
          as="input"
          onChange={handleChange}
        ></Form.Control>
      </Form.Group>
    );
  };

  const fetchPrice = async (symbol) => {
    const response = await api.post("/api/fetch_price", {
      symbol: symbol,
      withCredentials: true,
    });
    setPriceData(response.data);
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Form.Group>
        {symbolSuggestions && (
          <Autosuggest
            suggestions={symbolSuggestions}
            onSuggestionsFetchRequested={onSuggestionsFetchRequested}
            onSuggestionsClearRequested={onSuggestionsClearRequested}
            getSuggestionValue={getSuggestionValue}
            renderSuggestion={renderSuggestion}
            onSuggestionSelected={onSuggestionSelected}
            inputProps={{
              placeholder: "What are we trading today?",
              value: symbolValue,
              onChange: onSymbolChange,
            }}
          />
        )}
      </Form.Group>
      <Row>
        <Form.Label>{symbolLabel}</Form.Label>
      </Row>
      <Row>
        <Form.Label>
          {priceData
            ? `$${priceData.price} (last updated: ${priceData.last_updated})`
            : null}
        </Form.Label>
      </Row>

      <Form.Group>
        <Form.Label>Buy or Sell</Form.Label>
        <Form.Control
          name="buy_or_sell"
          as="select"
          defaultValue={gameInfo.default_buy_sell}
          onChange={handleChange}
        >
          {gameInfo.buy_sell_options &&
            optionBuilder(gameInfo.buy_sell_options)}
        </Form.Control>
      </Form.Group>

      <Row>
        <Col>
          <Form.Group>
            <Form.Label>
              {orderTicket.shares_or_usd &&
              orderTicket.shares_or_usd === "Shares"
                ? "Quantity"
                : "Amount"}
            </Form.Label>
            <Form.Control
              name="amount"
              as="input"
              defaultValue={gameInfo.default_buy_sell}
              onChange={handleChange}
            ></Form.Control>
          </Form.Group>
        </Col>
        <Col>
          <Form.Group>
            <Form.Label>Shares or USD</Form.Label>
            <Form.Control
              name="shares_or_usd"
              as="select"
              defaultValue={gameInfo.quantity_type}
              onChange={handleChange}
            >
              {gameInfo.quantity_options &&
                gameInfo.quantity_options.map((value) => (
                  <option>{value}</option>
                ))}
            </Form.Control>
          </Form.Group>
        </Col>
      </Row>

      <Row>
        <Col>
          <Form.Group>
            <Form.Label>Order type</Form.Label>
            <Form.Control
              name="order_type"
              as="select"
              defaultValue={gameInfo.order_type}
              onChange={handleChange}
            >
              {gameInfo.order_type_options &&
                optionBuilder(gameInfo.order_type_options)}
            </Form.Control>
          </Form.Group>
        </Col>
        <Col>
          {["stop", "limit"].includes(orderTicket.order_type) &&
            stopLimitElement()}
        </Col>
      </Row>

      <Form.Group>
        <Form.Label>Time in Force</Form.Label>
        <Form.Control
          name="time_in_force"
          as="select"
          defaultValue={gameInfo.time_in_force}
          onChange={handleChange}
        >
          {gameInfo.time_in_force_options &&
            optionBuilder(gameInfo.time_in_force_options)}
        </Form.Control>
      </Form.Group>

      <Button variant="primary" type="submit">
        Submit {orderTicket.buy_or_sell === "buy" ? "Buy" : "Sell"} Order
      </Button>
    </Form>
  );
};

export { PlaceOrder };
