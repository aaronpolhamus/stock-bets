import React, { useEffect, useContext } from 'react'
import { Redirect } from 'react-router-dom'
import { Button, Col, Row } from 'react-bootstrap'
import { usePostRequest } from 'components/functions/api'
import api from 'services/api'
import styled from 'styled-components'
import { UserContext } from 'UserContext'
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
import { GameList } from 'components/lists/GameList'
import * as Icon from 'react-feather'
import LogRocket from 'logrocket'

// Left in un-used for now: we'll almost certainly get to this later
const Logout = async () => {
  await api.post('/api/logout')
  window.location.assign('/login')
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
      email: data.email
    })
  }, [data])

  if (loading) {
    return <p>Loading...</p>
  }
  if (data.username === null) {
    return <Redirect to='/welcome' />
  }

  // console.log(data.game_info)
  const gamesActive = filterEntries(data.game_info, {
    game_status: 'active'
  })

  const gamesPending = filterEntries(data.game_info, {
    game_status: 'pending',
    invite_status: 'joined'
  })

  const gamesInvited = filterEntries(data.game_info, {
    game_status: 'pending',
    invite_status: 'invited'
  })

  return (
    <Layout>
      <Sidebar md={3}>
        <StyledMiniCard
          avatarSrc={data.profile_pic}
          username={data.username}
          email={data.email}
          nameColor='var(--cotlor-lighter)'
          dataColor='var(--color-text-light-gray)'
          info={['Return: 50%', 'Sharpe: 0.324']}
        />
        <FriendsList />
      </Sidebar>
      <Column md={9}>
        <PageSection>
          <Breadcrumb justifyContent='flex-end'>
            <Button variant='link' onClick={Logout}>
              <Icon.LogOut size={14} style={{ marginTop: '-3px' }} /> Logout
            </Button>
          </Breadcrumb>
          <Header>
            <TitlePage>
              Games
            </TitlePage>
            <Button variant='primary' href='/new'>
              <Icon.PlusCircle
                size={16}
                color='var(--color-primary-darkest)'
                style={{ marginTop: '-3px' }}
              />{' '}
              Make a new game
            </Button>
          </Header>
        </PageSection>
        <Row>
          <Col lg={6} xl={8}>
            <GameList
              games={gamesActive}
              title='Active'
            />
          </Col>
          <Col lg={6} xl={4}>
            <GameList
              games={gamesPending}
              cardType={'pending'}
              title='Pending'
            />
            <GameList
              games={gamesInvited}
              cardType={'pending'}
              title='Invited'
            />
          </Col>
        </Row>
      </Column>
    </Layout>
  )
}

export default Home
