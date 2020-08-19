import React, { useEffect, useContext, useState, useRef } from 'react'
import {
  Button,
  Col,
  Modal,
  Row,
  Tab,
  Tabs,
  Toast
} from 'react-bootstrap'
import { useParams, Link, Redirect } from 'react-router-dom'
import { PlaceOrder } from 'components/forms/PlaceOrder'
import {
  Breadcrumb,
  Column,
  Layout,
  PageSection,
  PageFooter,
  Sidebar
} from 'components/layout/Layout'
import { SectionTitle, AlignText } from 'components/textComponents/Text'
import { FieldChart } from 'components/charts/FieldChart'
import { GameHeader } from 'components/game/GameHeader'
import { ChevronLeft } from 'react-feather'
import { UserContext } from 'Contexts'
import { fetchGameData, apiPost } from 'components/functions/api'
import { PayoutsTable } from 'components/tables/PayoutsTable'
import { CompoundChart } from 'components/charts/CompoundChart'
import { FormattableTable } from 'components/tables/FormattableTable'
import { CancelOrderButton } from 'components/ui/buttons/CancelOrderButton'
import { CSVLink } from 'react-csv'
import api from 'services/api'
import { IconBuySell } from 'components/ui/icons/IconBuySell'
import { Sneak } from 'components/game/Sneak'

const PlayGame = () => {
  const { gameId } = useParams()
  const { user, setUser } = useContext(UserContext)
  const [showToast, setShowToast] = useState(false)
  const [lastOrder, setLastOrder] = useState({
    buy_or_sell: '',
    amount: '',
    symbol: ''
  })
  const [gameMode, setGameMode] = useState(null)
  const [showLeaveBox, setShowLeaveBox] = useState(false)
  const [redirect, setRedirect] = useState(false)
  const [updateInfo, setUpdateInfo] = useState('')
  const [cashData, setCashData] = useState({})
  const [transactionData, setTransactionData] = useState([])
  const csvLink = useRef()

  const handlePlacedOrder = (order) => {
    setLastOrder(order)
    setShowToast(true)
    handleUpdateInfo()
  }

  const handleUpdateInfo = () => {
    getCashData()
    setUpdateInfo(new Date())
  }

  const getCashData = async () => {
    const cashDataQuery = await fetchGameData(gameId, 'get_cash_balances')
    setCashData(cashDataQuery)
  }
  useEffect(() => {
    // We need to replace this with localstorage, maybe change useContext for redux
    if (Object.keys(user).length === 0) {
      const getUserInfo = async () => {
        const data = await apiPost('get_user_info', { withCredentials: true })
        setUser({
          username: data.username,
          name: data.name,
          email: data.email,
          profile_pic: data.profile_pic
        })
      }
      getUserInfo()
    }

    const getGameData = async () => {
      const data = await fetchGameData(gameId, 'game_info')
      setGameMode(data.game_mode)
    }
    getCashData()
    getGameData()
  }, [user, setUser])

  const handleCancelLeave = () => {
    setShowLeaveBox(false)
  }

  const handleConfirmLeave = async () => {
    await apiPost('leave_game', {
      game_id: gameId,
      withCredentials: true
    })
    setShowLeaveBox(false)
    setRedirect(true)
  }

  const getTransactionData = async () => {
    await api.post('/api/get_transactions_table', { game_id: gameId })
      .then((r) => setTransactionData(r.data))
      .catch((e) => console.log(e))
    csvLink.current.link.click()
  }

  if (redirect) return <Redirect to='/' />
  return (
    <Layout>
      <Sidebar md={3}>
        <PlaceOrder
          gameId={gameId}
          onPlaceOrder={handlePlacedOrder}
          update={updateInfo}
          cashData={cashData}
        />
      </Sidebar>
      <Column md={9}>
        <PageSection
          $marginBottom='var(--space-400)'
          $marginBottomMd='var(--space-400)'
        >
          <Breadcrumb>
            <Link to='/'>
              <ChevronLeft size={14} style={{ marginTop: '-3px' }} />
              <span> Dashboard</span>
            </Link>
          </Breadcrumb>
          <GameHeader
            gameId={gameId}
            cashData={cashData}
          />
        </PageSection>
        <PageSection>
          <Tabs>
            <Tab eventKey='field-chart' title='The Field'>
              <PageSection>
                <FieldChart gameId={gameId} />
                {gameMode === 'multi_player' &&
                  <AlignText align='right'>
                    <Sneak />
                  </AlignText>}
              </PageSection>
              <PageSection>
                <Row>
                  <Col sm={6}>
                    <SectionTitle>
                      Pending Orders
                    </SectionTitle>
                    <FormattableTable
                      hover
                      update={updateInfo}
                      endpoint='get_pending_orders_table'
                      name='pending-orders'
                      gameId={gameId}
                      formatCells={{
                        Symbol: function formatSymbol (value, row) {
                          return (
                            <>
                              <IconBuySell type={row['Buy/Sell']} />
                              <strong>
                                {value}
                              </strong>
                            </>
                          )
                        },
                        'Order price': function placedOn (value, row) {
                          return (
                            <>
                              {value}
                              <CancelOrderButton
                                gameId={gameId}
                                orderInfo={row}
                                onCancelOrder={handleUpdateInfo}
                              />
                            </>
                          )
                        }
                      }}
                      exclude={[
                        'Hypothetical return',
                        'as of',
                        'Buy/Sell',
                        'Order Type',
                        'Time in force',
                        'Market price',
                        'Order type'
                      ]}
                      sortBy=''
                      showColumns={{
                      }}
                      formatHeaders={{
                        Quantity: 'Qty.'
                      }}
                    />
                  </Col>
                  <Col sm={6}>
                    <SectionTitle>
                      Fulfilled Orders
                    </SectionTitle>
                    <FormattableTable
                      hover
                      update={updateInfo}
                      endpoint='get_fulfilled_orders_table'
                      name='fulfilled-orders'
                      gameId={gameId}
                      formatCells={{
                        Symbol: function formatSymbol (value, row) {
                          return (
                            <>
                              <IconBuySell type={row['Buy/Sell']} />
                              <strong>
                                {value}
                              </strong>
                            </>
                          )
                        }
                      }}
                      exclude={[
                        'Hypothetical return',
                        'Cleared on',
                        'Order price',
                        'as of',
                        'Buy/Sell',
                        'Order Type',
                        'Time in force',
                        'Market price',
                        'Order type'
                      ]}
                      sortBy='Placed on'
                      order='DESC'
                      showColumns={{
                      }}
                      formatHeaders={{
                        Quantity: 'Qty.'
                      }}
                    />
                  </Col>
                </Row>
              </PageSection>
            </Tab>
            <Tab eventKey='orders' title='Order Performance'>
              <CompoundChart
                gameId={gameId}
                chartDataEndpoint='get_order_performance_chart'
                legends={false}
                yScaleType='percent'
              >
                {
                  ({ handleSelectedLines }) => (
                    <FormattableTable
                      hover
                      endpoint='get_fulfilled_orders_table'
                      name='orders_table'
                      gameId={gameId}
                      onRowSelect={(output) => {
                        handleSelectedLines(output)
                      }}
                      tableCellCheckbox={0}
                      formatOutput={(output) => {
                        const label = `${output.Symbol}/${output.Quantity} @ ${output['Clear price']}/${output['Cleared on']}`
                        return {
                          label: label,
                          color: output.color
                        }
                      }}
                      formatCells={{
                        Symbol: function renderSymbol (value, row) {
                          return (
                            <strong>
                              {value}
                            </strong>
                          )
                        },
                        'Hypothetical return': function netChangeFormat (value) {
                          let color = 'var(--color-text-gray)'
                          if (parseFloat(value) < 0) {
                            color = 'var(--color-danger)'
                          } else if (parseFloat(value) > 0) {
                            color = 'var(--color-success)'
                          }

                          return (
                            <strong
                              style={{
                                color: color
                              }}
                            >
                              {value}
                            </strong>
                          )
                        },
                        'Clear price': function clearPriceFormat (value, row) {
                          const qty = row.Quantity
                          const price = value.replace(/\$|,/g, '')
                          const totalPrice = (qty * price).toLocaleString()
                          return (
                            <>
                              <strong>
                                {`$${totalPrice}`}
                              </strong>
                              <br />
                              <span
                                style={{
                                  color: 'var(--color-text-gray)'
                                }}
                              >
                                {`(${value})`}
                              </span>
                            </>
                          )
                        }
                      }}
                      excludeRows={(row) => {
                        return row['Buy/Sell'] === 'sell'
                      }}
                      exclude={[
                        'as of',
                        'Buy/Sell',
                        'Order type',
                        'Time in force',
                        'Market price',
                        'Placed on',
                        'Order price'
                      ]}
                      sortBy='Hypothetical return'
                      showColumns={{
                        md: [
                          'Symbol',
                          'Quantity',
                          'Clear price',
                          'Hypothetical return'
                        ]
                      }}
                    />
                  )
                }
              </CompoundChart>
            </Tab>
            <Tab eventKey='balances' title='Balances'>
              <CompoundChart
                gameId={gameId}
                chartDataEndpoint='get_balances_chart'
                tableId='balances-table'
                legends={false}
                yScaleType='dollar'
              >
                {
                  ({ handleSelectedLines }) => (
                    <FormattableTable
                      hover
                      endpoint='get_current_balances_table'
                      name='balances-table'
                      gameId={gameId}
                      onRowSelect={(output) => {
                        handleSelectedLines(output)
                      }}
                      tableCellCheckbox={0}
                      formatOutput={(output) => {
                        return {
                          label: output.Symbol,
                          color: output.color
                        }
                      }}
                      formatCells={{
                        Symbol: function renderSymbol (value, row) {
                          return (
                            <strong>
                              {value}
                            </strong>
                          )
                        },
                        'Change since last close': function formatForNetChange (value) {
                          return (
                            <strong>
                              {value}
                            </strong>
                          )
                        }
                      }}
                      sortBy='Balance'
                      showColumns={{
                        md: [
                          'Symbol',
                          'Balance',
                          'Value',
                          'Change since last close'
                        ]
                      }}
                    />
                  )
                }
              </CompoundChart>
            </Tab>
            {gameMode === 'multi_player' &&
              <Tab eventKey='payouts' title='Payouts'>
                <PayoutsTable gameId={gameId} />
              </Tab>}
          </Tabs>
        </PageSection>
        <PageFooter>
          <CSVLink
            data={transactionData}
            filename='transactions.csv'
            className='hidden'
            ref={csvLink}
            target='_blank'
          />
          <Button onClick={getTransactionData} variant='secondary'>Download transactions to csv</Button>
          <Button variant='outline-danger' onClick={() => setShowLeaveBox(true)}>Leave game</Button>
        </PageFooter>
      </Column>
      <Toast
        style={{
          position: 'fixed',
          top: 'var(--space-400)',
          right: 'var(--space-100)',
          minWidth: '300px'
        }}
        show={showToast}
        delay={6000}
        onClose={() => setShowToast(false)}
        autohide
      >
        <Toast.Header>
          <strong>
            {`${lastOrder.buy_or_sell} order placed`}
          </strong>
        </Toast.Header>
        <Toast.Body>
          {`${lastOrder.amount} ${lastOrder.symbol} ${lastOrder.amount === '1' ? 'share' : 'shares'}`}
        </Toast.Body>
      </Toast>
      <Modal show={showLeaveBox}>
        <Modal.Body>
          <div className='text-center'>
            Are you sure you&apos;d like to leave this game? Once you do you won&apos;t be able to rejoin, and will lose access to this game&apos;s data.
          </div>
        </Modal.Body>
        <Modal.Footer className='centered'>
          <Button variant='danger' onClick={handleConfirmLeave}>
            Yep, I&apos;m sure
          </Button>
          <Button variant='info' onClick={handleCancelLeave}>
            I&apos;ll stick around
          </Button>
        </Modal.Footer>
      </Modal>
    </Layout>
  )
}

export { PlayGame }
