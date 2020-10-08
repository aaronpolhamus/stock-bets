import React, { useState, useEffect, useContext } from 'react'
import {
  Button,
  Col,
  Form,
  Modal,
  Row,
  Tabs,
  Tab
} from 'react-bootstrap'
import api from 'services/api'
import styled from 'styled-components'
import { UserContext } from 'Contexts'
import {
  Header,
  Layout,
  PageSection,
  HomeSidebar,
  GameContent,
  SidebarSection
} from 'components/layout/Layout'
import { UserAvatar } from 'components/users/UserAvatar'
import { SmallCaps } from 'components/textComponents/Text'
import { AddFriends } from 'components/forms/AddFriends'
import { FriendsList } from 'components/lists/FriendsList'
import { SlideinBlock } from 'components/layout/SlideinBlock'
import { GameList } from 'components/lists/GameList'
import { GlobalLeaderboard } from 'components/lists/GlobalLeaderboard'
import { breakpoints } from 'design-tokens'
import {
  Globe,
  Users,
  X as IconClose,
  Users as IconUsers
} from 'react-feather'
import { IconTabs } from 'components/ui/icons/IconTabs'
import { Navbar } from 'components/ui/Navbar'
import { LogoutButton } from 'components/ui/buttons/LogoutButton'
import { formatPercentage } from 'components/functions/formattingHelpers'
import LogRocket from 'logrocket'

const filterEntries = (array, filters) => {
  return array.filter((entry, index) => {
    return Object.keys(filters).every((key, value) => {
      return filters[key].includes(entry[key])
    })
  })
}

const FormCheckStack = styled.div`
  .form-check + .form-check{
     margin-top: var(--space-100);
  }
`

const UserCard = styled.div`
  display: flex;
  align-items: center;
  padding: 0;
`

const UserInfo = styled.div`
  margin-left: var(--space-100);
  p {
    margin-bottom: 0;
  }
`
const UserInfoName = styled.p`
  font-weight: bold;
  font-size: var(--font-size-large);
  line-height: 1;
`

const UserStats = styled.div`
  color: var(--color-text-gray);
  small{
    margin-right: var(--space-200);
  }
  strong {
    color: var(--color-text-primary);
  }
`
const SidebarTabs = styled.div`
  .nav-tabs{
    position: sticky;
    top: 0;
    z-index: 1; 
    border-bottom: none;
    background-color: var(--color-secondary-dark);
  }
  .nav-link{
    width: 50%;
    justify-content: center;
    font-size: var(--font-size-min);
    color: var(--color-text-light-gray);
    padding: calc(var(--space-300)) 0;
    border-bottom-color: var(--color-secondary-muted);
  }
  .nav-link.active{
    background-color: transparent;
    color: var(--color-primary);
    border-bottom-color: var(--color-primary);
  }
  .nav-link:hover{
    border-bottom-color: var(--color-primary-lighten);
  }
`

const AddFriendsWrapper = styled.div`
  text-align: center;
  position: sticky;
  width: 90vw;
  bottom: 0;
  right: 0;
  padding: var(--space-700) 0 var(--space-200);
  background: linear-gradient(rgba(33, 27, 44, 0.15), var(--color-secondary-dark) 46.64%);

  @media screen and (min-width: ${breakpoints.md}){
    width: var(--sidebar-size);
    right: 0;
    z-index: 2;
    position: fixed;
  }
`

const Home = () => {
  const [username, setUserName] = useState('')
  const [acceptedTerms, setAcceptedTerms] = useState(false)
  const [acceptedPrivacy, setAcceptedPrivacy] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true)
  const [showStartGame, setShowStartGame] = useState(false)
  const [pilotGameFinished, setPilotGameFinished] = useState(false)
  const [homeData, setHomeData] = useState({})
  const [loading, setLoading] = useState(true)
  const [friendInvites, setFriendInvites] = useState(0)
  const { setUser } = useContext(UserContext)

  useEffect(() => {
    const getHomeData = async () => {
      try {
        setLoading(true)
        const response = await api.post('/api/home')
        setHomeData(response.data)
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
    LogRocket.identify(homeData.id, {
      name: homeData.name,
      email: homeData.email
    })

    // Set user info to persist in all app while the session is active.
    setUser({
      username: homeData.username,
      name: homeData.name,
      email: homeData.email,
      profile_pic: homeData.profile_pic
    })
  }, [homeData])

  if (loading) {
    return <p>Loading...</p>
  }

  if (homeData.username !== null) window.heap.identify(homeData.username)

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

  const gamesActive = filterEntries(homeData.game_info, {
    game_status: ['active', 'finished'],
    game_mode: ['multi_player']
  })

  const gamesPending = filterEntries(homeData.game_info, {
    game_status: ['pending'],
    invite_status: ['joined'],
    game_mode: ['multi_player']
  })

  const gamesInvited = filterEntries(homeData.game_info, {
    game_status: ['pending'],
    invite_status: ['invited'],
    game_mode: ['multi_player']
  })

  const gamesSinglePlayer = filterEntries(homeData.game_info, {
    game_status: ['active', 'finished'],
    game_mode: ['single_player']
  })

  return (
    <>
      <Layout
        className='home-layout'
      >
        <HomeSidebar md={3}>
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
            backgroundColor='var(--color-secondary-dark)'
          >
            <SidebarSection>
              <SidebarTabs>
                <Tabs>
                  <Tab
                    eventKey='leaderboard'
                    title={(
                      <>
                        <IconTabs><Globe /></IconTabs>
                        Leaderboard
                      </>
                    )}
                  >
                    <GlobalLeaderboard />
                  </Tab>
                  <Tab
                    eventKey='friends'
                    title={(
                      <>
                        <IconTabs><Users /></IconTabs>
                        Friends
                      </>
                    )}
                  >
                    <FriendsList
                      onLoadFriends={(invites) => {
                        setFriendInvites(invites.length)
                      }}
                    />
                  </Tab>
                </Tabs>
              </SidebarTabs>
            </SidebarSection>
            <AddFriendsWrapper>
              <AddFriends
                variant='alt'
              />
            </AddFriendsWrapper>
          </SlideinBlock>
        </HomeSidebar>
        <GameContent md={9} className='game-content'>
          <Navbar
            homeButton={false}
            itemsRight={
              <LogoutButton />
            }
          />
          <PageSection className='page-section'>
            <Header>
              <UserCard>
                <UserAvatar
                  src={homeData.profile_pic}
                  size='big'
                />
                <UserInfo>
                  <UserInfoName>
                    {homeData.username}
                  </UserInfoName>
                  <UserStats>
                    <p>
                      <SmallCaps>
                        Global Rating: <strong>{homeData.rating.toFixed(2)}</strong>
                      </SmallCaps>
                      <SmallCaps>
                        3-Month Return: <strong>{formatPercentage(homeData.three_month_return)}</strong>
                      </SmallCaps>
                    </p>
                  </UserStats>
                </UserInfo>
              </UserCard>
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
                  title='Games'
                />
                <GameList
                  games={gamesSinglePlayer}
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
        </GameContent>
      </Layout>
      <Modal show={homeData.username === null && showWelcome} onHide={() => {}} centered>
        <Modal.Header>
        Welcome! Let&apos;s get started.
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
            I&apos;ll come back later
            </Button>
            <Button onClick={setUsername} variant='primary' type='submit' disabled={!acceptedTerms || !acceptedPrivacy}>
            Submit
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
      <Modal show={showStartGame} centered>
        <Modal.Body>
        To get you introduced to the feature set we&apos;ve setup a single player &quot;pilot game&quot; for you -- it lasts a week,
        and you&apos;ll be playing against the major market indexes. To play against other stockbets users go ahead and add
        a couple friends, or accept any outstanding invitations that you have. You can join or start multiplayer games
        with people once they are in your network.
          <Button onClick={() => setShowStartGame(false)} variant='primary'>
          Start trading
          </Button>
        </Modal.Body>
      </Modal>
    </>
  )
}

export default Home
