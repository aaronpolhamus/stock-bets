import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { PageSection } from 'components/layout/Layout'
import { Modal, Button, Tabs, Tab } from 'react-bootstrap'
import { FormattableTable } from 'components/tables/FormattableTable'
import { fetchGameData } from 'components/functions/api'
import { CompoundChart } from 'components/charts/CompoundChart'
import * as Icon from 'react-feather'
import { ReactComponent as IconBinoculars } from 'assets/binoculars-2.svg'
import { CustomSelect } from 'components/ui/inputs/CustomSelect'

const Sneak = props => {
  const { gameId } = useParams()
  const [username, setUsername] = useState(null)
  const [showSneak, setShowSneak] = useState(false)
  const [players, setPlayers] = useState([])

  useEffect(() => {
    const getPlayers = async () => {
      const data = await fetchGameData(gameId, 'get_leaderboard')
      setUsername(data.records[0].username)
      setPlayers(data.records.map((entry) => entry.username))
    }
    getPlayers()
  }, [])

  return (
    <>
      <Button
        variant='link'
        style={{
          fontSize: 'var(--font-size-small)',
          marginTop: 'var(--space-300)',
          display: 'inline-block'
        }}
        onClick={() => {
          setShowSneak(true)
        }}
      >
        Sneak on other players
        <IconBinoculars
          strokeWidth={2}
          stroke='var(--color-primary-darken)'
          width={22}
          style={{
            marginTop: '-3px',
            marginLeft: 'var(--space-50)'
          }}
        />
      </Button>
      <Modal
        dialogClassName='wide-dialog'
        show={showSneak}
        onHide={() => { setShowSneak(false) }}
      >
        <Modal.Header>
          <h1>
            <IconBinoculars
              strokeWidth={2}
              stroke='var(--color-primary-darken)'
              width={32}
              height={32}
              style={{
                marginTop: '-8px',
                marginRight: 'var(--space-200)'
              }}
            />
            Sneaking on
          </h1>
          <CustomSelect
            name='username'
            size='sm'
            onChange={(e) => setUsername(e.target.value)}
          >
            {players && players.map((element) => <option key={element} value={element}>{element}</option>)}
          </CustomSelect>
          <Button
            variant='link'
            style={{
              position: 'absolute',
              right: 'var(--space-100)',
              top: 0
            }}
            onClick={() => {
              setShowSneak(false)
            }}
          >
            <Icon.X
              color='currentColor'
            />
          </Button>
        </Modal.Header>
        <Modal.Body>
          <PageSection $marginBottomMd='var(--space-300)'>

            <Tabs className='center-nav'>
              <Tab
                eventKey='sneak-performance'
                title='Performance'
              >
                <CompoundChart
                  gameId={gameId}
                  username={username}
                  chartDataEndpoint='get_order_performance_chart'
                  legends={false}
                  yScaleType='percent'
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
                          const label = output.order_label
                          return {
                            label: label,
                            color: output.color
                          }
                        }}
                        simpleFormatCells={{
                          'Cleared on': ['date'],
                          'Clear price': ['currency'],
                          'Market price': ['currency'],
                          'Balance (FIFO)': ['currency'],
                          'Realized P&L': ['currency'],
                          'Unrealized P&L': ['currency'],
                          Basis: ['currency', 'bold']
                        }}
                        formatCells={{
                          Symbol: function renderSymbol (value, row) {
                            return (
                              <strong>
                                {value}
                              </strong>
                            )
                          }
                        }}
                        excludeRows={(row) => {
                          return row.event_type === 'sell'
                        }}
                        exclude={[
                          'as of',
                          'Buy/Sell',
                          'Order type',
                          'Time in force',
                          'Placed on',
                          'Order price'
                        ]}
                        showColumns={{
                          md: [
                            'Symbol',
                            'Quantity',
                            'Cleared on',
                            'Clear price',
                            'Market price'
                          ]
                        }}
                      />
                    )
                  }
                </CompoundChart>
              </Tab>
              <Tab
                eventKey='sneak-balances'
                title='Balances'
              >
                <CompoundChart
                  gameId={gameId}
                  username={username}
                  chartDataEndpoint='get_balances_chart'
                  legends={false}
                  yScaleType='dollar'
                >
                  {
                    ({ handleSelectedLines }) => (
                      <FormattableTable
                        hover
                        endpoint='get_current_balances_table'
                        username={username}
                        name='balances-table'
                        gameId={gameId}
                        onRowSelect={(output) => {
                          handleSelectedLines(output)
                        }}
                        tableCellCheckbox={0}
                        formatOutput={(output) => {
                          return {
                            label: output.Symbol,
                            color: output.color
                          }
                        }}
                        simpleFormatCells={{
                          Value: ['currency', 'bold'],
                          'Updated at': ['date'],
                          'Last order price': ['currency'],
                          'Market price': ['currency'],
                          'Portfolio %': ['percentage'],
                          'Change since last close': ['percentage']
                        }}
                        formatCells={{
                          Symbol: function renderSymbol (value, row) {
                            return (
                              <strong>
                                {value}
                              </strong>
                            )
                          }
                        }}
                        sortBy='Balance'
                        showColumns={{
                          md: [
                            'Symbol',
                            'Balance',
                            'Value',
                            'Change since last close'
                          ]
                        }}
                      />
                    )
                  }
                </CompoundChart>
              </Tab>
            </Tabs>
          </PageSection>
        </Modal.Body>
      </Modal>
    </>
  )
}

export { Sneak }
