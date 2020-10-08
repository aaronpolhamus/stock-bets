import React, { useState } from 'react'
import { MakeGame } from 'components/forms/MakeGame'
import {
  Layout,
  Column,
  PageSection,
  Header
} from 'components/layout/Layout'
import { Form } from 'react-bootstrap'
import { RadioButtons } from 'components/forms/Inputs'
import { Navbar } from 'components/ui/Navbar'

const NewGame = () => {
  const [gameMode, setGameMode] = useState('multi_player')
  return (
    <>
      <Layout>
        <Column md={12}>
          <Navbar />
        </Column>
        <Column md={{ span: 8, offset: 2 }}>
          <PageSection>
            <Header>
              <h1>New Game</h1>
            </Header>
          </PageSection>
          <PageSection>
            <Form.Group>
              <Form.Label>
              Choose a Game Mode
              </Form.Label>

              <RadioButtons
                optionsList={{
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
          </PageSection>
        </Column>
      </Layout>
    </>
  )
}

export { NewGame }
