import React, { useState, useMemo } from 'react'
import { BrowserRouter as Router, Route } from 'react-router-dom'
import Home from 'pages/Home'
import Login from 'pages/Login'
import Welcome from 'components/Welcome'
import { PlayGame } from 'pages/PlayGame'
import { JoinGame } from 'pages/JoinGame'
import { NewGame } from 'pages/NewGame'
import { Admin } from 'pages/Admin'
import { PrivacyPolicy } from 'pages/PrivacyPolicy'
import { UserContext } from 'Contexts'

export default function App () {
  const [user, setUser] = useState({})
  const userProviderValue = useMemo(() => ({ user, setUser }), [user, setUser])

  return (
    <Router>
      <UserContext.Provider value={userProviderValue}>
        <Route exact path='/' component={Home} />
        <Route exact path='/play/:gameId/' component={PlayGame} />
        <Route exact path='/join/:gameId/' component={JoinGame} />
        <Route path='/new/:gameMode' component={NewGame} />
      </UserContext.Provider>
      <Route path='/welcome/' component={Welcome} />
      <Route path='/login/' component={Login} />
      <Route path='/privacy/' component={PrivacyPolicy} />
      <Route path='/admin/' component={Admin} />

    </Router>
  )
}
