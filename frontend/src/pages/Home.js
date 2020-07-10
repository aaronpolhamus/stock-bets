import React, { useEffect } from 'react'
import { Link, Redirect } from 'react-router-dom'
import { Button, Col, Row } from 'react-bootstrap'
import { usePostRequest } from 'components/functions/api'
import api from 'services/api'
import styled from 'styled-components'
import {
  Breadcrumb,
  Column,
  Content,
  Header,
  Layout,
  PageSection,
  Sidebar
} from 'components/layout/Layout'
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

  useEffect(() => {
    // identify user once they've hit the homepage
    LogRocket.identify(data.id, {
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
          nameColor='var(--color-lighter)'
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
            <h1>Games</h1>
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
          <Col>
          Active
            <GameList
              games={gamesActive}
              currentUser={data.username}
            />
          </Col>
          <Col>
            Pending
            <GameList
              games={gamesPending}
              currentUser={data.username}
              cardType={'pending'}
            />
            Invitations
            <GameList
              games={gamesInvited}
              currentUser={data.username}
              cardType={'pending'}
            />
          </Col>
        </Row>
      </Column>
    </Layout>
  )
}

export default Home
