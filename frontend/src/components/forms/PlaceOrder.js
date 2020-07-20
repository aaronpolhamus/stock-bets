import React, { useEffect, useState, useRef } from 'react'
import api from 'services/api'
import { Row, Col, Button, Form } from 'react-bootstrap'
import Autosuggest from 'react-autosuggest'
import { optionBuilder } from 'components/functions/forms'
import { AuxiliarText, FormFooter } from 'components/textComponents/Text'
import { fetchGameData } from 'components/functions/api'
import { RadioButtons, TabbedRadioButtons } from 'components/forms/Inputs'
import { Tooltip } from 'components/forms/Tooltips'
import PropTypes from 'prop-types'
import styled from 'styled-components'

const PlaceOrder = ({ gameId, onPlaceOrder }) => {
  const [gameInfo, setGameInfo] = useState({})
  const [orderTicket, setOrderTicket] = useState({})
  const [symbolSuggestions, setSymbolSuggestions] = useState([])
  const [symbolValue, setSymbolValue] = useState('')
  const [symbolLabel, setSymbolLabel] = useState('')
  const [priceData, setPriceData] = useState({})
  const [intervalId, setintervalId] = useState(null)
  const formRef = useRef(null)
  const autosugestRef = useRef(null)

  useEffect(() => {
    const getFormInfo = async () => {
      const data = await fetchGameData(gameId, 'order_form_defaults')
      setOrderTicket(data)
      setGameInfo(data)
    }
    getFormInfo()
  }, [gameId])

  const handleChange = (e) => {
    const orderTicketCopy = { ...orderTicket }
    orderTicketCopy[e.target.name] = e.target.value
    setOrderTicket(orderTicketCopy)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const orderTicketCopy = { ...orderTicket }
    orderTicketCopy.symbol = symbolValue
    setOrderTicket(orderTicketCopy)

    await api.post('/api/place_order', orderTicketCopy)
      .then(request => {
        onPlaceOrder()
        setSymbolValue('')
        setSymbolLabel('')
        setPriceData({})
        formRef.current.reset()
        clearInterval(intervalId)
      })
      .catch(error => {
        window.alert(error.response.data)
      })
  }

  const getSuggestionValue = (suggestion) => {
    setSymbolLabel(suggestion.label)
    return suggestion.symbol
  }

  const renderSuggestion = (suggestion) => {
    return <span>{suggestion.label}</span>
  }

  const onSymbolChange = (event, { newValue, method }) => {
    setSymbolValue(newValue)
  }

  const onSuggestionsFetchRequested = async (text) => {
    const response = await api.post('/api/suggest_symbols', {
      text: text.value,
      game_id: gameId,
      buy_or_sell: orderTicket.buy_or_sell,
      withCredentials: true
    })
    setSymbolSuggestions(response.data)
  }

  const onSuggestionsClearRequested = () => {
    setSymbolSuggestions([])
  }

  const onSuggestionSelected = (
    event,
    { suggestion, suggestionValue, suggestionIndex, sectionIndex, method }
  ) => {
    // This part of the code handles the dynamically-updating price ticker when a stock pick gets made. We need to clear the old interval and set
    // a new one each time there is a change
    if (intervalId) {
      clearInterval(intervalId)
    }

    fetchPrice(suggestionValue)
    const newIntervalID = setInterval(() => {
      fetchPrice(suggestionValue)
    }, 2500)
    setintervalId(newIntervalID)
  }

  const stopLimitElement = () => {
    return (
      <Form.Group>
        <Form.Label>
          {orderTicket.order_type === 'stop' ? 'Stop' : 'Limit'} Price
        </Form.Label>
        <Form.Control
          name='stop_limit_price'
          as='input'
          onChange={handleChange}
        />
      </Form.Group>
    )
  }

  const fetchPrice = async (symbol) => {
    const response = await api.post('/api/fetch_price', {
      symbol: symbol,
      withCredentials: true
    })
    setPriceData(response.data)
  }

  return (
    <Form
      onSubmit={handleSubmit}
      ref={formRef}
    >
      <Form.Group>
        <TabbedRadioButtons
          mode='tabbed'
          name='buy_or_sell'
          defaultChecked={orderTicket.buy_or_sell}
          onChange={handleChange}
          className=''
          options={gameInfo.buy_sell_options}
          color='var(--color-text-light-gray)'
          $colorChecked='var(--color-lightest)'
        />
      </Form.Group>
      <Form.Group>
        <Form.Label>Symbol</Form.Label>
        {symbolSuggestions && (
          <Autosuggest
            ref={autosugestRef}
            suggestions={symbolSuggestions}
            onSuggestionsFetchRequested={onSuggestionsFetchRequested}
            onSuggestionsClearRequested={onSuggestionsClearRequested}
            getSuggestionValue={getSuggestionValue}
            renderSuggestion={renderSuggestion}
            onSuggestionSelected={onSuggestionSelected}
            inputProps={{
              placeholder: 'What are we trading today?',
              value: symbolValue,
              onChange: onSymbolChange
            }}
          />
        )}
        {Object.keys(priceData).length > 0 && symbolValue !== '' && (
          <AuxiliarText color='var(--color-light-gray)'>
            <strong>
              {symbolLabel} ${priceData.price}
            </strong>
            <br />
            <small>Last updated: {priceData.last_updated}</small>
            <br />
            <small>
              <a href='https://iexcloud.io' target='_blank' rel='noopener noreferrer'>
                  Data provided by IEX Cloud
              </a>
            </small>
          </AuxiliarText>
        )}
      </Form.Group>
      <Row>
        <Col>
          <Form.Group>
            <Form.Label>
              {orderTicket.quantity_type &&
                orderTicket.quantity_type === 'Shares'
                ? 'Quantity'
                : 'Amount'}
            </Form.Label>
            <Form.Control required name='amount' as='input' onChange={handleChange} />
          </Form.Group>
        </Col>
        <Col>
          <Form.Group>
            <Form.Label>Shares or USD</Form.Label>
            <Form.Control
              name='quantity_type'
              as='select'
              defaultValue={orderTicket.quantity_type}
              onChange={handleChange}
            >
              {gameInfo.quantity_options &&
                  gameInfo.quantity_options.map((value) => (
                    <option key={value}>{value}</option>
                  ))}
            </Form.Control>
          </Form.Group>
        </Col>
      </Row>
      <Row>
        <Col>
          <Form.Group>
            <Form.Label>
                Order type
              <Tooltip message="A market order clears right away, at  whatever price is currently on the market. A 'limit' order is an order where the price direction is in your favor, e.g. a buy-limit order clears when the market price is less than or equal to the price you set. A sell-limit order, on the other hand, clears when the market price is greater than or equal to your order price. A sell-stop order is a common way to reduce exposure to loss, and clears when the market price is at or below the sale order price. Orders only clear during trading day--if you're placing orders outside of trading hours, you should see them reflected in your orders table as pending." />
            </Form.Label>
            <RadioButtons
              name='order_type'
              defaultChecked={orderTicket.order_type}
              onChange={handleChange}
              options={gameInfo.order_type_options}
              color='var(--color-text-light-gray)'
              $colorChecked='var(--color-lightest)'
            />
          </Form.Group>
        </Col>
      </Row>
      <Row>
        <Col>
          {['stop', 'limit'].includes(orderTicket.order_type) &&
              stopLimitElement()}
        </Col>
      </Row>
      <Form.Group>
        <Form.Label>
            Time in Force
          <Tooltip message="We'll continually monitor an 'Until cancelled' order for execution until you cancel it by hand." />
        </Form.Label>
        <Form.Control
          name='time_in_force'
          as='select'
          defaultValue={gameInfo.time_in_force}
          onChange={handleChange}
        >
          {gameInfo.time_in_force_options &&
              optionBuilder(gameInfo.time_in_force_options)}
        </Form.Control>
      </Form.Group>
      <FormFooter>
        <Button variant='primary' type='submit'>
            Submit {orderTicket.buy_or_sell === 'buy' ? 'Buy' : 'Sell'} Order
        </Button>
      </FormFooter>
    </Form>
  )
}

PlaceOrder.propTypes = {
  gameId: PropTypes.string,
  onPlaceOrder: PropTypes.func
}

export { PlaceOrder }
