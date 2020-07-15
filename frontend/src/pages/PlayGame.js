import React, { useEffect, useContext } from 'react'
import { Tabs, Tab } from 'react-bootstrap'
import { useParams, Link } from 'react-router-dom'
import { PlaceOrder } from 'components/forms/PlaceOrder'
import {
  Layout,
  Sidebar,
  PageSection,
  Column,
  Breadcrumb
} from 'components/layout/Layout'
import { FieldChart } from 'components/charts/FieldChart'
import { UserDropDownChart } from 'components/charts/BaseCharts'
import { OpenOrdersTable } from 'components/tables/OpenOrdersTable'
import { PendingOrdersTable } from 'components/tables/PendingOrdersTable'
import { GameHeader } from 'pages/game/GameHeader'
import { ChevronLeft } from 'react-feather'
import { BalancesTable } from 'components/tables/BalancesTable'
import { PayoutsTable } from 'components/tables/PayoutsTable'
import { UserContext } from 'Contexts'
import { apiPost } from 'components/functions/api'
import { SmallCaps } from 'components/textComponents/Text'

const PlayGame = (props) => {
  const { gameId } = useParams()
  const { user, setUser } = useContext(UserContext)

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
  }, [user, setUser])

  return (
    <Layout>
      <Sidebar md={3}>
        <PlaceOrder gameId={gameId} />
      </Sidebar>
      <Column md={9}>
        <PageSection>
          <Breadcrumb>
            <Link to='/'>
              <ChevronLeft size={14} style={{ marginTop: '-3px' }} /> Dashboard
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
                <UserDropDownChart
                  gameId={gameId}
                  endpoint='get_order_performance_chart'
                  yScaleType='percent'
                  title='Order Performance'
                />
              </PageSection>
              <PageSection>
                <PendingOrdersTable gameId={gameId} title='Pending Orders' />

              </PageSection>
            </Tab>
            <Tab eventKey='balances-chart' title='Balances and Orders'>
              <PageSection>
                <h2>
                  <SmallCaps>
                    Your balances
                  </SmallCaps>
                </h2>
                <BalancesTable gameId={gameId} />
              </PageSection>
              <PageSection>
                <UserDropDownChart
                  gameId={gameId}
                  endpoint='get_balances_chart'
                  yScaleType='dollar'
                  title='Balances Chart'
                />
              </PageSection>
              <PageSection>
                <UserDropDownChart
                  gameId={gameId}
                  endpoint='get_order_performance_chart'
                  yScaleType='percent'
                  title='Order Performance'
                />
                <OpenOrdersTable gameId={gameId} />
              </PageSection>

            </Tab>
            <Tab eventKey='order-performance-chart' title='Payouts'>
              <PayoutsTable gameId={gameId} />
            </Tab>
          </Tabs>
        </PageSection>
      </Column>
    </Layout>
  )
}

export { PlayGame }
