import React, { useState, useEffect, useContext } from 'react'
import { Button, Col, Form, Modal, Row } from 'react-bootstrap'
import api from 'services/api'
import styled from 'styled-components'
import { UserContext } from 'Contexts'
import {
  Breadcrumb,
  Column,
  Header,
  Layout,
  PageSection,
  Sidebar
} from 'components/layout/Layout'
import { UserMiniCard } from 'components/users/UserMiniCard'
import { FriendsList } from 'components/lists/FriendsList'
import { SlideinBlock } from 'components/layout/SlideinBlock'
import { GameList } from 'components/lists/GameList'
import {
  LogOut,
  X as IconClose,
  Users as IconUsers
} from 'react-feather'
import LogRocket from 'logrocket'
import { AddFriends } from 'components/forms/AddFriends'
import { breakpoints } from 'design-tokens'

// Left in un-used for now: we'll almost certainly get to this later
const handleLogout = async () => {
  await api.post('/api/logout')
  window.location.assign('/')
}

const filterEntries = (array, filters) => {
  return array.filter((entry, index) => {
    return Object.keys(filters).every((key, value) => {
      return filters[key].includes(entry[key])
    })
  })
}

const StyledMiniCard = styled(UserMiniCard)`
  padding-bottom: var(--space-400);
  border-bottom: 1px solid rgba(0, 0, 0, 0.3);
  position: relative;
  &::after {
    position: absolute;
    bottom: 0px;
    left: 0;
    content: "";
    display: block;
    height: 1px;
    width: 100%;
    background-color: rgba(255, 255, 255, 0.1);
  }
`
const HomeFooter = styled.div`
  width: 100%;
  position: fixed;
  display: flex;
  align-items: center;
  justify-content: center;
  left: 0;
  bottom: 0;
  height: 13vh;
  background: linear-gradient(0deg, #FFFFFF 52.22%, rgba(255, 255, 255, 0) 100%);
  @media screen and (min-width: ${breakpoints.md}){
    width: 70%;
    bottom: var(--space-400);
    justify-content: flex-end;
    left: auto;
    right: auto;
    height: auto;
    background: none;
  }
`

const FormCheckStack = styled.div`
  .form-check + .form-check{
     margin-top: var(--space-100);
  }
`

const Home = () => {
  const [username, setUserName] = useState('')
  const [acceptedTerms, setAcceptedTerms] = useState(false)
  const [acceptedPrivacy, setAcceptedPrivacy] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true)
  const [showStartGame, setShowStartGame] = useState(false)
  const [pilotGameFinished, setPilotGameFinished] = useState(false)
  const [data, setData] = useState({})
  const [loading, setLoading] = useState(true)
  const [friendInvites, setFriendInvites] = useState(0)
  const { setUser } = useContext(UserContext)

  useEffect(() => {
    const getHomeData = async () => {
      try {
        setLoading(true)
        const response = await api.post('/api/home')
        setData(response.data)
      } catch (e) {
        console.log(e)
      } finally {
        setLoading(false)
      }
    }
    getHomeData()
  }, [pilotGameFinished])
  useEffect(() => {
    const kickOff = async () => {
      try {
        await api.post('/api/create_game', {
          title: 'intro game',
          game_mode: 'single_player',
          duration: 7,
          benchmark: 'return_ratio'
        })
        setPilotGameFinished(true)
      } catch (e) {
        console.log(e)
      }
    }
    if (showStartGame) kickOff()
  }, [showStartGame, setShowStartGame])

  useEffect(() => {
    // identify user once they've hit the homepage
    LogRocket.identify(data.id, {
      name: data.name,
      email: data.email
    })

    // Set user info to persist in all app while the session is active.
    setUser({
      username: data.username,
      name: data.name,
      email: data.email,
      profile_pic: data.profile_pic
    })
  }, [data])

  if (loading) {
    return <p>Loading...</p>
  }

  if (data.username !== null) window.heap.identify(data.username)

  const handleChange = (e) => {
    setUserName(e.target.value)
  }

  const setUsername = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/set_username', {
        username: username
      })
      setShowWelcome(false)
      setShowStartGame(true)
    } catch (error) {
      window && window.alert(`Looks like '${username}' is taken, try another one`)
    }
  }

  const gamesActive = filterEntries(data.game_info, {
    game_status: ['active', 'finished'],
    game_mode: ['multi_player']
  })

  const gamesPending = filterEntries(data.game_info, {
    game_status: ['pending'],
    invite_status: ['joined'],
    game_mode: ['multi_player']
  })

  const gamesInvited = filterEntries(data.game_info, {
    game_status: ['pending'],
    invite_status: ['invited'],
    game_mode: ['multi_player']
  })

  const gamesSinglePlayer = filterEntries(data.game_info, {
    game_status: ['active', 'finished'],
    game_mode: ['single_player']
  })
  return (
    <Layout
      className='home-layout'
    >
      <Modal show={data.username === null && showWelcome} onHide={() => {}} centered>
        <Modal.Header>
          Welcome! Let&quot;s get started.
        </Modal.Header>
        <Form>
          <Modal.Body>
            <div>
              <Form.Group style={{ textAlign: 'left' }}>
                <Form.Label>
                Pick a username
                </Form.Label>
                <Form.Control
                  onChange={handleChange}
                  type='input'
                  name='username'
                  placeholder='Your username'
                />
                <Form.Text>
                  This will be your publicly visible username.
                </Form.Text>
              </Form.Group>
              <FormCheckStack>
                <Form.Check
                  type='checkbox'
                  label={
                    <span>
                      I agree to stockbets.io <a href='/terms'>terms and conditions</a>
                    </span>
                  }
                  onChange={() => setAcceptedTerms(!acceptedTerms)}
                  id='terms-and-conditions-check'
                />
                <Form.Check
                  type='checkbox'
                  label={
                    <span>
                      I agree to the stockbets.io <a href='/privacy'>privacy policy</a>
                    </span>
                  }
                  onChange={() => setAcceptedPrivacy(!acceptedPrivacy)}
                  id='privacy-policy-check'
                />
              </FormCheckStack>
            </div>
          </Modal.Body>
          <Modal.Footer className='centered'>
            <Button onClick={() => window.history.go(-2)} variant='light'>
              I'll come back later
            </Button>
            <Button onClick={setUsername} variant='primary' type='submit' disabled={!acceptedTerms || !acceptedPrivacy}>
              Submit
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
      <Modal show={showStartGame} centered>
        <Modal.Body>
          To get you introduced to the feature set we've setup a single player "pilot game" for you -- it lasts a week,
          and you'll be playing against the major market indexes. To play against other stockbets users go ahead and add
          a couple friends, or accept any outstanding invitations that you have. You can join or start multiplayer games
          with people once they are in your network.
          <Button onClick={() => setShowStartGame(false)} variant='primary'>
            Start trading
          </Button>
        </Modal.Body>
      </Modal>
      <Sidebar md={3}>
        <SlideinBlock
          icon={
            <IconUsers
              size={24}
              color='var(--color-primary-darken)'
              style={{
                marginTop: '-3px'
              }}
            />
          }
          iconNotifications={friendInvites}
          iconClose={
            <IconClose
              size={24}
              color='var(--color-primary)'
              style={{
                marginTop: '-3px'
              }}
            />
          }
          context='md'
          backgroundColor='var(--color-secondary)'
        >
          <StyledMiniCard
            avatarSrc={data.profile_pic}
            username={data.username}
            email={data.email}
            nameColor='var(--cotlor-lighter)'
            dataColor='var(--color-text-light-gray)'
            info={['Return: 50%', 'Sharpe: 0.324']}
          />
          <FriendsList
            onLoadFriends={(invites) => {
              setFriendInvites(invites.length)
            }}
          />
        </SlideinBlock>
      </Sidebar>
      <Column md={9}>
        <PageSection>
          <Breadcrumb justifyContent='flex-end'>
            <Button variant='link' onClick={handleLogout}>
              <LogOut size={14} style={{ marginTop: '-3px' }} />
              <span> Logout</span>
            </Button>
          </Breadcrumb>
          <Header>
            <h1>
              Games
            </h1>
            <div style={{ textAlign: 'right' }}>
              <Button variant='success' href='/new'>
                Make new game
              </Button>
            </div>
          </Header>
        </PageSection>
        <PageSection>
          <Row>
            <Col lg={6} xl={8}>
              <GameList
                games={gamesActive}
                title='Competitions'
              />
              <GameList
                games={gamesSinglePlayer}
                title='Single player'
              />
            </Col>
            <Col lg={6} xl={4}>
              <GameList
                games={gamesPending}
                cardType='pending'
                title='Pending'
              />
              <GameList
                games={gamesInvited}
                cardType='pending'
                title='Invited'
              />
            </Col>
          </Row>
        </PageSection>
        <HomeFooter>
          <AddFriends />
        </HomeFooter>

      </Column>
    </Layout>
  )
}

export default Home
