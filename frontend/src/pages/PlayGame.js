import React, { useEffect, useContext, useState } from 'react'
import { Tabs, Tab, Accordion, Button, Toast } from 'react-bootstrap'
import { useParams, Link } from 'react-router-dom'
import { PlaceOrder } from 'components/forms/PlaceOrder'
import {
  Breadcrumb,
  Column,
  Header,
  Layout,
  PageSection,
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
import { AlignText, SectionTitle } from 'components/textComponents/Text'

const PlayGame = (props) => {
  const { gameId } = useParams()
  const { user, setUser } = useContext(UserContext)
  const [ordersData, setOrdersData] = useState({})
  const [showToast, setShowToast] = useState(false)
  const [gameMode, setGameMode] = useState(null)

  const getOrdersData = async () => {
    const data = await fetchGameData(gameId, 'get_order_details_table')
    setOrdersData(data)
  }

  const handlePlacedOrder = (order) => {
    setShowToast(true)
    getOrdersData()
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
    getOrdersData()

    const getGameData = async () => {
      const data = await fetchGameData(gameId, 'game_info')
      setGameMode(data.game_mode)
    }
    getGameData()
  }, [user, setUser])

  return (
    <Layout>
      <Sidebar md={3}>
        <PlaceOrder
          gameId={gameId}
          onPlaceOrder={handlePlacedOrder}
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
                  tableData={ordersData}
                  gameId={gameId}
                  title='Pending Orders'
                  onCancelOrder={getOrdersData}
                />

              </PageSection>
            </Tab>
            <Tab eventKey='balances-chart' title='Balances and Orders'>
              <PageSection>
                {gameMode === 'multi_player'
                  ? <UserDropDownChart
                    gameId={gameId}
                    endpoint='get_order_performance_chart'
                    yScaleType='percent'
                    title='Order Performance'
                  />
                  : <VanillaChart
                    gameId={gameId}
                    endpoint='get_order_performance_chart'
                    yScaleType='percent'
                    title='Order Performance'
                  />}
              </PageSection>
              <PageSection>
                <Header>
                  <SectionTitle> Your balances </SectionTitle>
                </Header>
                <BalancesTable gameId={gameId} />
              </PageSection>
              <PageSection>
                <Accordion>
                  <AlignText align='right'>
                    <Accordion.Toggle
                      as={Button}
                      variant='link'
                      eventKey='0'
                    >
                      Show Balances Chart
                    </Accordion.Toggle>
                  </AlignText>
                  <Accordion.Collapse eventKey='0'>
                    {gameMode === 'multi_player'
                      ? <UserDropDownChart
                        gameId={gameId}
                        endpoint='get_balances_chart'
                        yScaleType='dollar'
                        title='Balances Chart'
                      />
                      : <VanillaChart
                        gameId={gameId}
                        endpoint='get_balances_chart'
                        yScaleType='dollar'
                        title='Balances Chart'
                      />}
                  </Accordion.Collapse>
                </Accordion>
              </PageSection>
              <PageSection>
                {gameMode === 'multi_player'
                  ? <UserDropDownChart
                    gameId={gameId}
                    endpoint='get_order_performance_chart'
                    yScaleType='percent'
                    title='Order Performance'
                  />
                  : <VanillaChart
                    gameId={gameId}
                    endpoint='get_order_performance_chart'
                    yScaleType='percent'
                    title='Order Performance'
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
                <OpenOrdersTable gameId={gameId} />
              </PageSection>
            </Tab>
            {gameMode === 'multi_player' &&
              <Tab eventKey='order-performance-chart' title='Payouts'>
                <PayoutsTable gameId={gameId} />
              </Tab>}
          </Tabs>
        </PageSection>
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
          <strong>Order placed</strong>
          <small>Right now</small>
        </Toast.Header>
        <Toast.Body>
          We got your order!
        </Toast.Body>
      </Toast>
    </Layout>
  )
}

export { PlayGame }
