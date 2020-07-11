import React from 'react'
import { Link } from 'react-router-dom'
import { MakeGame } from 'components/forms/MakeGame'
import {
  Layout,
  Sidebar,
  Column,
  Breadcrumb,
  PageSection,
  Header
} from 'components/layout/Layout'
import * as Icon from 'react-feather'

const NewGame = () => {
  return (
    <Layout>
      <Sidebar md={2} />
      <Column md={10}>
        <PageSection>
          <Breadcrumb>
            <Link to='/'>
              {' '}
              <Icon.ChevronLeft size={16} style={{ marginTop: '-3px' }} />{' '}
              Dashboard
            </Link>
          </Breadcrumb>
          <Header>
            <h1>New Game</h1>
          </Header>
        </PageSection>
        <MakeGame />
      </Column>
    </Layout>
  )
}

export { NewGame }
