import React from 'react'
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
import { GameHeader } from 'pages/game/GameHeader'
import { ChevronLeft } from 'react-feather'
import { BalancesTable } from 'components/tables/BalancesTable'
import { PayoutsTable } from 'components/tables/PayoutsTable'

const PlayGame = (props) => {
  const { gameId } = useParams()

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
                <UserDropDownChart gameId={gameId} endpoint='get_order_performance_chart' yScaleType='percent' />
              </PageSection>
            </Tab>
            <Tab eventKey='balances-chart' title='Orders and Balances'>
              <UserDropDownChart gameId={gameId} endpoint='get_balances_chart' />
              <BalancesTable gameId={gameId} />
              <UserDropDownChart gameId={gameId} endpoint='get_order_performance_chart' yScaleType='percent' />
              <OpenOrdersTable gameId={gameId} />
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
