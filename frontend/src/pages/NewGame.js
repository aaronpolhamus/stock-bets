import React, { useState } from 'react'
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
import { Form } from 'react-bootstrap'
import { RadioButtons } from 'components/forms/Inputs'

const NewGame = () => {
  const [gameMode, setGameMode] = useState('multi_player')
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
        <Form.Group>
          <Form.Label>
                Choose a Game Mode
          </Form.Label>

          <RadioButtons
            options={{
              multi_player: 'Play with your friends',
              single_player: 'You vs. The Market'
            }}
            name='invite_type'
            defaultChecked={gameMode}
            onClick={(e) => {
              setGameMode(e.target.value)
            }}
          />
        </Form.Group>
        <MakeGame gameMode={gameMode} />
      </Column>
    </Layout>
  )
}

export { NewGame }
