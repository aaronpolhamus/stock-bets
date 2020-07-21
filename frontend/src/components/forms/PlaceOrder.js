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
import { breakpoints } from 'design-tokens'
import { CashInfo } from 'components/lists/CashInfo'
import { ChevronsDown } from 'react-feather'

const StyledOrderForm = styled(Form)`
  @media screen and (max-width: ${breakpoints.md}){
    position: fixed;
    z-index: 2;
    padding: 0 var(--space-400) var(--space-600);
    background-color: var(--color-secondary);
    bottom: 0;
    left: 0;
    width: 100vw;
    transition: transform .3s;
    transform: ${props => props.$show
      ? 'translate(100%)'
      : 'translateY(calc(100% - var(--space-lg-100)));'
    }
    
    box-shadow: 0px -30px 30px rgba(17, 7, 60, 0.3);
  }
`

const CollapsibleClose = styled.div`
  display: none;
  appearance: none;
  border: none;
  background-color: transparent;
  position: absolute;
  top: -40px;
  right: var(--space-100);
  @media screen and (max-width: ${breakpoints.md}){
    transition: max-height .2s ease-out;
    display: ${props => props.$show ? 'block' : 'none'};
  }
`
const OrderFormHeader = styled(Form.Group)`
  @media screen and (max-width: ${breakpoints.md}){
    height: var(--space-900);
    text-align: center;
    .form-check {
      width: 50%;
    }
    label {
      justify-content: center;
      border-bottom: none;
      padding: var(--space-300) 0 var(--space-200);
    }
    label::after{
      content: '';
      position: absolute;
      bottom: 0;
      left: 25%;
      display: block;
      width: 50%;
      height: 2px;
      background-color: var(--color-secondary-muted);
    }
    input:checked + label::after {
      background-color: var(--color-primary);
    }
  }
`

const PlaceOrder = ({ gameId, onPlaceOrder }) => {
  const [gameInfo, setGameInfo] = useState({})
  const [orderTicket, setOrderTicket] = useState({})
  const [symbolSuggestions, setSymbolSuggestions] = useState([])
  const [symbolValue, setSymbolValue] = useState('')
  const [symbolLabel, setSymbolLabel] = useState('')
  const [priceData, setPriceData] = useState({})
  const [cashData, setCashData] = useState({})

  const [showCollapsible, setShowCollapsible] = useState(false)
  const [intervalId, setintervalId] = useState(null)
  const formRef = useRef(null)
  const autosugestRef = useRef(null)

  useEffect(() => {
    const getFormInfo = async () => {
      const data = await fetchGameData(gameId, 'order_form_defaults')

      const cashInfo = await fetchGameData(gameId, 'get_cash_balances')

      setCashData(cashInfo)
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

  const handleBuySellClicked = () => {
    setShowCollapsible(true)
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
    <StyledOrderForm
      onSubmit={handleSubmit}
      ref={formRef}
      $show={showCollapsible}
    >
      <CollapsibleClose
        $show={showCollapsible}
        onClick={() => {
          setShowCollapsible(false)
        }}
      >
        <ChevronsDown
          size={24}
          color='var(--color-secondary)'
        />
      </CollapsibleClose>
      <OrderFormHeader>
        <TabbedRadioButtons
          mode='tabbed'
          name='buy_or_sell'
          defaultChecked={orderTicket.buy_or_sell}
          onChange={handleChange}
          onClick={handleBuySellClicked}
          options={gameInfo.buy_sell_options}
          color='var(--color-text-light-gray)'
          $colorChecked='var(--color-lightest)'
        />
      </OrderFormHeader>
      <CashInfo cashData={cashData}/>
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
              Place {orderTicket.buy_or_sell === 'buy' ? 'Buy' : 'Sell'} Order
        </Button>
      </FormFooter>
    </StyledOrderForm>
  )
}

PlaceOrder.propTypes = {
  gameId: PropTypes.string,
  onPlaceOrder: PropTypes.func
}

export { PlaceOrder }
