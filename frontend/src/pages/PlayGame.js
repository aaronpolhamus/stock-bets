import React from 'react'
import { Tabs, Tab } from 'react-bootstrap'
import { useParams } from 'react-router-dom'
import { PlaceOrder } from 'components/forms/PlaceOrder'
import {
  Layout,
  Sidebar,
  PageSection,
  Content,
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
      <Sidebar>
        <PlaceOrder gameId={gameId} />
      </Sidebar>
      <Content>
        <PageSection>
          <Breadcrumb>
            <a href='/'>
              {' '}
              <ChevronLeft size={14} style={{ marginTop: '-3px' }} /> Dashboard
            </a>
          </Breadcrumb>
          <GameHeader gameId={gameId} />
        </PageSection>
        <PageSection>
          <Tabs>
            <Tab eventKey='field-chart' title='The Field'>
              <FieldChart gameId={gameId} />
              <UserDropDownChart gameId={gameId} endpoint='get_order_performance_chart' yScaleType='percent' />
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
      </Content>
    </Layout>
  )
}

export { PlayGame }
