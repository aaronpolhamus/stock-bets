import React, { useState, useMemo } from 'react'
import { BrowserRouter as Router, Route } from 'react-router-dom'
import Home from 'pages/Home'
import Login from 'pages/Login'
import { PlayGame } from 'pages/PlayGame'
import { Sneak } from 'pages/Sneak'
import { JoinGame } from 'pages/JoinGame'
import { NewGame } from 'pages/NewGame'
import { Admin } from 'pages/Admin'
import { Playground } from 'pages/Playground'
import { PrivacyPolicy } from 'pages/PrivacyPolicy'
import { TermsAndConditions } from 'pages/TermsAndConditions'
import { UserContext } from 'Contexts'

export default function App () {
  const [user, setUser] = useState({})
  const userProviderValue = useMemo(() => ({ user, setUser }), [user, setUser])

  return (
    <Router>
      <UserContext.Provider value={userProviderValue}>
        <Route exact path='/' component={Home} />
        <Route exact path='/play/:gameId/' component={PlayGame} />
        <Route exact path='/play/:gameId/sneak' component={Sneak} />
        <Route exact path='/join/:gameId/' component={JoinGame} />
        <Route path='/new/' component={NewGame} />
      </UserContext.Provider>
      <Route path='/login/' component={Login} />
      <Route path='/privacy/' component={PrivacyPolicy} />
      <Route path='/terms/' component={TermsAndConditions} />
      <Route path='/admin/' component={Admin} />
      <Route path='/playground/' component={Playground} />

    </Router>
  )
}
