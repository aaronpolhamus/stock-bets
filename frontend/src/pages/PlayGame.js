import React, { useEffect, useContext, useState } from 'react'
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
import { FieldChart } from 'components/charts/FieldChart'
import { GameHeader } from 'pages/game/GameHeader'
import { ChevronLeft } from 'react-feather'
import { UserContext } from 'Contexts'
import { fetchGameData, apiPost } from 'components/functions/api'
import { PayoutsTable } from 'components/tables/PayoutsTable'

import { CompoundChart } from 'components/charts/CompoundChart'

import { FormattableTable } from 'components/tables/FormattableTable'

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
  const [updateTables, setUpdateTables] = useState('')
  const [updateCashInfo, setUpdateCashInfo] = useState('')

  const handlePlacedOrder = (order) => {
    setLastOrder(order)
    setShowToast(true)
    setUpdateTables(new Date())
  }

  const handleCancelOrder = () => {
    setUpdateCashInfo(new Date())
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

  if (redirect) return <Redirect to='/' />
  return (
    <Layout>
      <Sidebar md={3}>
        <PlaceOrder
          gameId={gameId}
          onPlaceOrder={handlePlacedOrder}
          update={updateCashInfo}
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
          <GameHeader gameId={gameId} />
        </PageSection>
        <PageSection>
          <Tabs>
            <Tab eventKey='field-chart' title='The Field'>
              <PageSection>
                <FieldChart gameId={gameId} />
              </PageSection>

              <PageSection>
                <Row>
                  <Col sm={6}>
                    <FormattableTable
                      hover
                      endpoint='get_pending_orders_table'
                      name='pending-orders'
                      gameId={gameId}
                      tableCellFormat={{

                      }}
                      exclude={[
                        'Hypothetical % return',
                        'Cleared on',
                        'Clear price',
                        'Status',
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
                      replaceHeader={{
                        Quantity: 'Qty.'
                      }}
                    />
                  </Col>
                </Row>
              </PageSection>
            </Tab>
            <Tab eventKey='orders' title='Performance'>
              <CompoundChart
                gameId='3'
                chartDataEndpoint='get_order_performance_chart'
                legends={false}
              >
                {
                  ({ handleSelectedLines }) => (
                    <FormattableTable
                      hover
                      endpoint='get_fulfilled_orders_table'
                      name='orders_table'
                      gameId='3'
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
                      tableCellFormat={{
                        Symbol: function renderSymbol (value, row) {
                          return (
                            <strong>
                              {value}
                            </strong>
                          )
                        },
                        'Hypothetical % return': function formatForNetChange (value) {
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
                        }
                      }}
                      exclude={[
                        'Status',
                        'as of',
                        'Buy/Sell',
                        'Order type',
                        'Time in force',
                        'Market price',
                        'Placed on',
                        'Order price'
                      ]}
                      sortBy='Hypothetical % return'
                      showColumns={{
                      }}
                    />
                  )
                }
              </CompoundChart>
            </Tab>
            <Tab eventKey='balances' title='Balances'>
              <PageSection>
                <CompoundChart
                  gameId={gameId}
                  chartDataEndpoint='get_balances_chart'
                  tableId='balances-table'
                  legends={false}
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
                        tableCellFormat={{
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
              </PageSection>
            </Tab>
            {gameMode === 'multi_player' &&
              <Tab eventKey='payouts' title='Payouts'>
                <PayoutsTable gameId={gameId} />
              </Tab>}
          </Tabs>
        </PageSection>
        <PageFooter>
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
