import React, { useEffect, useContext, useState } from 'react'
import { Tabs, Tab, Toast, Button, Modal } from 'react-bootstrap'
import { useParams, Link, Redirect } from 'react-router-dom'
import { PlaceOrder } from 'components/forms/PlaceOrder'
import {
  Breadcrumb,
  Column,
  Header,
  Layout,
  PageSection,
  PageFooter,
  Sidebar
} from 'components/layout/Layout'
import { FieldChart } from 'components/charts/FieldChart'
import { VanillaChart, UserDropDownChart } from 'components/charts/BaseCharts'
import { OpenOrdersTable } from 'components/tables/OpenOrdersTable'
import { PendingOrdersTable } from 'components/tables/PendingOrdersTable'
import { GameHeader } from 'pages/game/GameHeader'
import { ChevronLeft } from 'react-feather'
import { BalancesTable } from 'components/tables/BalancesTable'
import { PayoutsTable } from 'components/tables/PayoutsTable'
import { UserContext } from 'Contexts'
import { fetchGameData, apiPost } from 'components/functions/api'
import { SectionTitle } from 'components/textComponents/Text'

const PlayGame = () => {
  const { gameId } = useParams()
  const { user, setUser } = useContext(UserContext)
  const [ordersData, setOrdersData] = useState({})
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

  const getOrdersData = async () => {
    const data = await fetchGameData(gameId, 'get_order_details_table')
    setOrdersData(data)
  }

  const handlePlacedOrder = (order) => {
    setLastOrder(order)
    setShowToast(true)
    setUpdateTables(new Date())
    getOrdersData()
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
                <PendingOrdersTable
                  update={updateTables}
                  gameId={gameId}
                  title='Pending Orders'
                  onCancelOrder={handleCancelOrder}
                />

              </PageSection>
            </Tab>
            <Tab eventKey='balances-chart' title='Balances'>
              <PageSection>
                {gameMode === 'multi_player'
                  ? <UserDropDownChart
                    gameId={gameId}
                    endpoint='get_balances_chart'
                    yScaleType='dollar'
                  />
                  : <VanillaChart
                    gameId={gameId}
                    endpoint='get_balances_chart'
                    yScaleType='dollar'
                  />}
              </PageSection>
              <PageSection>
                <BalancesTable
                  gameId={gameId}
                  update={updateTables}
                />
              </PageSection>
            </Tab>
            <Tab
              eventKey='orders-chart' title='Orders'
            >
              <PageSection>
                {gameMode === 'multi_player'
                  ? <UserDropDownChart
                    gameId={gameId}
                    endpoint='get_order_performance_chart'
                    yScaleType='percent'
                    title='Order Performance'
                    update={updateTables}
                  />
                  : <VanillaChart
                    gameId={gameId}
                    endpoint='get_order_performance_chart'
                    yScaleType='percent'
                    title='Order Performance'
                    update={updateTables}
                  />}
              </PageSection>
              <PageSection>
                <PendingOrdersTable
                  tableData={ordersData}
                  gameId={gameId}
                  title='Pending Orders'
                  onCancelOrder={getOrdersData}
                />
              </PageSection>
              <PageSection>
                <OpenOrdersTable
                  gameId={gameId}
                  update={updateTables}
                />
              </PageSection>
            </Tab>
            {gameMode === 'multi_player' &&
              <Tab eventKey='order-performance-chart' title='Payouts'>
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
