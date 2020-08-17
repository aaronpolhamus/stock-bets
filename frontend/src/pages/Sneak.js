import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Layout,
  Sidebar,
  Column,
  Header,
  PageSection,
  Breadcrumb
} from 'components/layout/Layout'
import { Container, Form, Col, Row } from 'react-bootstrap'
import { FormattableTable } from 'components/tables/FormattableTable'
import { fetchGameData, apiPost } from 'components/functions/api'
import * as Icon from 'react-feather'

const Sneak = props => {
  const { gameId } = useParams()
  const [player, setPlayer] = useState(null)
  const [gameData, setGameData] = useState(null)
  const [players, setPlayers] = useState([])

  useEffect(() => {
    const getPlayers = async () => {
      const data = await fetchGameData(gameId, 'get_leaderboard')
      setPlayer(data.records[0].username)
      setPlayers(data.records.map((entry) => entry.username))
    }
    getPlayers()

    const getGameData = async () => {
      const data = await fetchGameData(gameId, 'game_info')
      setGameData(data.game_mode)
    }
    getGameData()
  }, [])

  return (
    <Layout>
      <Sidebar md={2} size='sm' />
      <Column md={10}>
        <PageSection>
          <Breadcrumb>
            <Link to={`/play/${gameId}`}>
              <Icon.ChevronLeft size={14} style={{ marginTop: '-3px' }} />
              Back to game
            </Link>
          </Breadcrumb>
          <Header>
            <h1>Sneak mode</h1>
            <small>
              {player}
            </small>
            <div>
              <Form.Control
                name='username'
                as='select'
                size='sm'
                onChange={(e) => setPlayer(e.target.value)}
              >
                {players && players.map((element) => <option key={element} value={element}>{element}</option>)}
              </Form.Control>
            </div>
          </Header>
        </PageSection>
        <PageSection $marginBottomMd='var(--space-300)'>

        </PageSection>
      </Column>
    </Layout>
  )
}

export { Sneak }
