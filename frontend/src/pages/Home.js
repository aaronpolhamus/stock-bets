import React, { useEffect, useContext } from 'react'
import { Redirect } from 'react-router-dom'
import { Button, Col, Row } from 'react-bootstrap'
import { usePostRequest } from 'components/functions/api'
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

import { TitlePage } from 'components/textComponents/Text'
import { UserMiniCard } from 'components/users/UserMiniCard'
import { filterEntries } from 'components/functions/Transformations'
import { FriendsList } from 'components/lists/FriendsList'
import { SlideinBlock } from 'components/layout/SlideinBlock'
import { GameList } from 'components/lists/GameList'
import {
  LogOut,
  X as IconClose,
  Users as IconUsers
} from 'react-feather'
import LogRocket from 'logrocket'

// Left in un-used for now: we'll almost certainly get to this later
const handleLogout = async () => {
  await api.post('/api/logout')
  window.location.assign('/')
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

const Home = () => {
  const { data, loading } = usePostRequest('/api/home')
  const { setUser } = useContext(UserContext)

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
  if (data.username === null) {
    return <Redirect to='/welcome' />
  } else {
    window.heap.identify(data.username)
  }

  const activeAndJustFinished = () => {
    const activeGames = filterEntries(data.game_info, {
      game_status: 'active',
      game_mode: 'multi_player'
    })
    const justFinishedGames = filterEntries(data.game_info, {
      game_status: 'finished',
      game_mode: 'multi_player'
    })
    return activeGames.concat(justFinishedGames)
  }

  const gamesActive = activeAndJustFinished()

  const gamesPending = filterEntries(data.game_info, {
    game_status: 'pending',
    invite_status: 'joined',
    game_mode: 'multi_player'
  })

  const gamesInvited = filterEntries(data.game_info, {
    game_status: 'pending',
    invite_status: 'invited',
    game_mode: 'multi_player'
  })

  const gamesSinglePlayer = filterEntries(data.game_info, {
    game_status: 'active',
    game_mode: 'single_player'
  })

  return (
    <Layout>
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
          <FriendsList />
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
            <TitlePage>
              Games
            </TitlePage>
            <div>
              <Button variant='primary' href='/new/single_player'>
                Play solo
              </Button>
              <Button variant='primary' href='/new/multi_player'>
                Play against your friends
              </Button>
            </div>
          </Header>
        </PageSection>
        <Row>
          <Col lg={6} xl={8}>
            <GameList
              games={gamesActive}
              title='Competitions'
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
          <Col lg={6} xl={8}>
            <GameList
              games={gamesSinglePlayer}
              title='Single player'
            />
          </Col>
        </Row>
      </Column>
    </Layout>
  )
}

export default Home
