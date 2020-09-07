import React, { useEffect, useState, useRef } from 'react'
import api from 'services/api'
import { Row, Col, Button, Form, InputGroup } from 'react-bootstrap'
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
import CurrencyInput from 'components/ui/inputs/CurrencyInput'

const StyledOrderForm = styled(Form)`
  position: relative;
  @media screen and (max-width: ${breakpoints.md}){
    overflow: auto;
    background-color: var(--color-secondary);
    bottom: 0;
    left: 0;
    height: 90vh;
    height: -webkit-fill-available;
    padding: 0 var(--space-400) var(--space-600);
    position: fixed;
    transition: transform .3s, box-shadow .5s;
    width: 100vw;
    z-index: 2;

    box-shadow: ${props => props.$show
      ? '0px -30px 30px rgba(17, 7, 60, 0.3)'
      : '0'
    };
    transform: ${props => props.$show
      ? 'translateY(0)'
      : 'translateY(calc(100% - var(--space-lg-100)))'
    };
    
  }
  /* Processig Form Loader */
  &::before {
    content: '';
    display: block;
    position: absolute;
    background-color: var(--color-secondary);
    width: 100%;
    height: 200vh;
    z-index: 1;
    left: 0;
    top: -200vh;
    opacity: 0;
    ${({ $loading }) => $loading && `
      top: 0;
      opacity: .5;
    `}
  }

`

const CollapsibleClose = styled.div`
  align-items: flex-end;
  appearance: none;
  border: none;
  display: none;
  height: 2.5rem;
  justify-content: center;
  text-align: right;
  width: 100%;
  margin: auto;
  z-index: 1;
  position: relative;
  margin-bottom: -1rem;

  @media screen and (max-width: ${breakpoints.md}){
    transition: max-height .2s ease-out;
    display: ${props => props.$show ? 'flex' : 'none'};
  }
`
const OrderFormHeader = styled(Form.Group)`
  min-height: var(--space-600);
  @media screen and (max-width: ${breakpoints.md}){
    position: sticky;
    top: 0;
    text-align: right;
    background-color: var(--color-secondary);
    min-height: var(--space-900);
    margin-bottom: var(--space-200);
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

const AmountInput = styled.div`
  .form-check{
    font-size: var(--font-size-min);
    margin-bottom: 0;
    margin-left: var(--space-100);
    &:first-child{
      margin-left: 0;
    }
  }
  label{
    min-width: 0;
    padding: 9px var(--space-50) 0;
    display: inline-block;
  }
  .input-group-append{
    background-color: #fff;
    border-radius: 0 var(--space-50) var(--space-50) 0;
    padding: 0 var(--space-100);
    border: 1px solid #ced4da;
    border-left-color: transparent; 
  }
  .form-control {
    border-right-color: transparent; 
  }
`

const PlaceOrder = ({ gameId, onPlaceOrder, update, cashData }) => {
  const [gameInfo, setGameInfo] = useState({})
  const [orderTicket, setOrderTicket] = useState({})
  const [symbolSuggestions, setSymbolSuggestions] = useState([])
  const [symbolValue, setSymbolValue] = useState('')
  const [symbolLabel, setSymbolLabel] = useState('')
  const [priceData, setPriceData] = useState({})
  const [orderProcessing, setOrderProcessing] = useState(false)

  const [showCollapsible, setShowCollapsible] = useState(false)
  const [intervalId, setintervalId] = useState(null)
  const formRef = useRef(null)
  const autosugestRef = useRef(null)

  const getFormInfo = async () => {
    const data = await fetchGameData(gameId, 'order_form_defaults')
    setOrderTicket(data)
    setGameInfo(data)
  }

  useEffect(() => {
    getFormInfo()
  }, [gameId, update])

  const handleChange = (e) => {
    const orderTicketCopy = { ...orderTicket }
    orderTicketCopy[e.target.name] = e.target.value
    setOrderTicket(orderTicketCopy)
  }

  const handleChangeAmount = (e) => {
    const orderTicketCopy = { ...orderTicket }
    const amount = parseFloat(e.target.value.replace(',', ''))
    orderTicketCopy.amount = amount
    setOrderTicket(orderTicketCopy)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const orderTicketCopy = { ...orderTicket }
    orderTicketCopy.symbol = symbolValue
    setOrderTicket(orderTicketCopy)
    setOrderProcessing(true)
    await api.post('/api/place_order', orderTicketCopy)
      .then(request => {
        setShowCollapsible(false)
        setOrderProcessing(false)
        onPlaceOrder(orderTicketCopy)
        setSymbolValue('')
        setSymbolLabel('')
        setPriceData({})
        formRef.current.reset()
        clearInterval(intervalId)
      })
      .catch(error => {
        setOrderProcessing(false)
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

    if (method === 'enter') {
      event.preventDefault()
    }
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
      $loading={orderProcessing}
    >
      <OrderFormHeader>
        <CollapsibleClose
          $show={showCollapsible}
          onClick={() => {
            setShowCollapsible(false)
          }}
        >
          <ChevronsDown
            size={24}
            color='var(--color-text-gray)'
          />
        </CollapsibleClose>
        <TabbedRadioButtons
          mode='tabbed'
          name='buy_or_sell'
          $defaultChecked={orderTicket.buy_or_sell}
          onChange={handleChange}
          onClick={handleBuySellClicked}
          options={gameInfo.buy_sell_options}
          color='var(--color-text-light-gray)'
          $colorChecked='var(--color-lightest)'
        />
      </OrderFormHeader>
      <CashInfo cashData={cashData} balance={false} />
      <Form.Group>
        <Form.Label>
          Symbol
          <small>
            <a
              href='https://iexcloud.io'
              target='_blank'
              rel='noopener noreferrer'
            >
              Data by IEX Cloud
            </a>
          </small>
        </Form.Label>
        {symbolSuggestions && (
          <Form.Control
            as={Autosuggest}
            required
            ref={autosugestRef}
            suggestions={symbolSuggestions}
            onSuggestionsFetchRequested={onSuggestionsFetchRequested}
            onSuggestionsClearRequested={onSuggestionsClearRequested}
            getSuggestionValue={getSuggestionValue}
            renderSuggestion={renderSuggestion}
            highlightFirstSuggestion
            focusInputOnSuggestionClick
            onSuggestionSelected={onSuggestionSelected}
            inputProps={{
              placeholder: 'What are we trading today?',
              value: symbolValue,
              onChange: onSymbolChange
            }}
          />
        )}

        <AuxiliarText color={symbolValue !== '' ? 'var(--color-light-gray)' : 'transparent'}>
          <strong>
            {symbolValue !== '' && priceData.price && `${symbolLabel} $${priceData.price}`}
          </strong>
          <br />
          <small>
            {symbolValue !== '' ? `Last updated: ${priceData.last_updated}` : '-'}
          </small>
        </AuxiliarText>

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
            <AmountInput>
              <InputGroup>
                <Form.Control required as={CurrencyInput} placeholder='0.00' type='text' name='amount' onChange={handleChangeAmount} precision={0} value={orderTicket.amount} />
                <InputGroup.Append>
                  <TabbedRadioButtons
                    mode='tabbed'
                    name='quantity_type'
                    $defaultChecked={orderTicket.quantity_type}
                    onChange={handleChange}
                    options={gameInfo.quantity_options}
                    colorTab='var(--color-lightest)'
                    color='var(--color-text-gray)'
                    $colorChecked='var(--color-secondary)'
                  />
                </InputGroup.Append>
              </InputGroup>
            </AmountInput>
          </Form.Group>
        </Col>
      </Row>
      <Row>
        <Col>
          <Form.Group>
            <Form.Label>
                  Order type
              <Tooltip
                message={
                  <>
                    <p>
                      A <strong>Market Order</strong> clears right away, at  whatever price is currently on the market.
                    </p>
                    <p>
                      A <strong>Limit Order</strong> clears if the price is equal or better* than your limit price.
                    </p>
                    <p>
                     A <strong>Stop Order</strong> triggers a market order when the price reaches your stop price.
                    </p>
                    <p className='annotation'>
                      <small>*Better is less than your price if you're buying and greater than your price if you're selling. <a href=''>Read more about market, limit and stop orders</a></small>
                    </p>
                  </>
                }
              />
            </Form.Label>
            <RadioButtons
              name='order_type'
              $defaultChecked={orderTicket.order_type}
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
  cashData: PropTypes.object,
  gameId: PropTypes.string,
  onPlaceOrder: PropTypes.func,
  update: PropTypes.string
}

export { PlaceOrder }
