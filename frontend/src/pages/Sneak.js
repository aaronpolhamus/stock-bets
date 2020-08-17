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
import { CompoundChart } from 'components/charts/CompoundChart'
import * as Icon from 'react-feather'

const Sneak = props => {
  const { gameId } = useParams()
  const [username, setUsername] = useState(null)
  const [gameData, setGameData] = useState(null)
  const [players, setPlayers] = useState([])

  useEffect(() => {
    const getPlayers = async () => {
      const data = await fetchGameData(gameId, 'get_leaderboard')
      setUsername(data.records[0].username)
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
              {username}
            </small>
            <div>
              <Form.Control
                name='username'
                as='select'
                size='sm'
                onChange={(e) => setUsername(e.target.value)}
              >
                {players && players.map((element) => <option key={element} value={element}>{element}</option>)}
              </Form.Control>
            </div>
          </Header>
        </PageSection>
        <PageSection $marginBottomMd='var(--space-300)'>
          <CompoundChart
            gameId={gameId}
            username={username}
            chartDataEndpoint='get_order_performance_chart'
            legends={false}
          >
            {
              ({ handleSelectedLines }) => (
                <FormattableTable
                  hover
                  endpoint='get_fulfilled_orders_table'
                  name='orders_table'
                  gameId={gameId}
                  username={username}
                  onRowSelect={(output) => {
                    handleSelectedLines(output)
                  }}
                  tableCellCheckbox={0}
                  formatOutput={(output) => {
                    const label = `${output.Symbol}/${output.Quantity} @ ${output['Clear price']}/${output['Cleared on']}`
                    return {
                      label: label,
                      color: output.color
                    }
                  }}
                  formatCells={{
                    Symbol: function renderSymbol (value, row) {
                      return (
                        <strong>
                          {value}
                        </strong>
                      )
                    },
                    'Hypothetical return': function netChangeFormat (value) {
                      let color = 'var(--color-text-gray)'
                      if (parseFloat(value) < 0) {
                        color = 'var(--color-danger)'
                      } else if (parseFloat(value) > 0) {
                        color = 'var(--color-success)'
                      }

                      return (
                        <strong
                          style={{
                            color: color
                          }}
                        >
                          {value}
                        </strong>
                      )
                    },
                    'Clear price': function clearPriceFormat (value, row) {
                      const qty = row.Quantity
                      const price = value.replace(/\$|,/g, '')
                      const totalPrice = (qty * price).toLocaleString()
                      return (
                        <>
                          <strong>
                            {`$${totalPrice}`}
                          </strong>
                          <br/>
                          <span
                            style={{
                              color: 'var(--color-text-gray)'
                            }}
                          >
                            {`(${value})`}
                          </span>
                        </>
                      )
                    }
                  }}
                  exclude={[
                    'as of',
                    'Buy/Sell',
                    'Order type',
                    'Time in force',
                    'Market price',
                    'Placed on',
                    'Order price'
                  ]}
                  sortBy='Hypothetical return'
                  showColumns={{
                    md: [
                      'Symbol',
                      'Quantity',
                      'Clear price',
                      'Hypothetical return'
                    ]
                  }}
                />
              )
            }
          </CompoundChart>
        </PageSection>
      </Column>
    </Layout>
  )
}

export { Sneak }
