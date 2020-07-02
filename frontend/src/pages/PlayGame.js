import React from 'react'
import { Tabs, Tab } from 'react-bootstrap'
import { useParams } from 'react-router-dom'
import { PlaceOrder } from 'components/forms/PlaceOrder'
import {
  Layout,
  Sidebar,
  PageSection,
  Content,
  SmallColumn,
  Breadcrumb
} from 'components/layout/Layout'
import { FieldChart } from 'components/charts/FieldChart'
import { UserDropDownChart } from 'components/charts/BaseCharts'
import { OrdersAndBalancesCard } from 'components/tables/OrdersAndBalancesCard'
import { GameHeader } from 'pages/game/GameHeader'
import { PlayGameStats } from 'components/lists/PlayGameStats'
import { ChevronLeft } from 'react-feather'

const PlayGame = (props) => {
  const { gameId } = useParams()

  return (
    <Layout>
      <Sidebar>
        <PlaceOrder gameId={gameId} />
      </Sidebar>
      <SmallColumn>
        <PlayGameStats gameId={gameId} />
      </SmallColumn>
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
            <Tab eventKey='field-chart' title='Field'>
              <FieldChart gameId={gameId} />
            </Tab>
            <Tab eventKey='balances-chart' title='Balances'>
              <UserDropDownChart gameId={gameId} endpoint='get_balances_chart' />
            </Tab>
            <Tab eventKey='order-performance-chart' title='Order Performance'>
              <UserDropDownChart gameId={gameId} endpoint='get_order_performance_chart' yScaleType='percent' />
            </Tab>
          </Tabs>
        </PageSection>
        <PageSection>
          <OrdersAndBalancesCard gameId={gameId} />
        </PageSection>
      </Content>
    </Layout>
  )
}

export { PlayGame }
