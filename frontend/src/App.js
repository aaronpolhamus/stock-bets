import React, {useState} from 'react'
import { BrowserRouter as Router, Route } from 'react-router-dom'
import Home from 'pages/Home'
import Login from 'pages/Login'
import Welcome from 'components/Welcome'
import { PlayGame } from 'pages/PlayGame'
import { JoinGame } from 'pages/JoinGame'
import { NewGame } from 'pages/NewGame'
import { Admin } from 'pages/Admin'
import { PrivacyPolicy } from 'pages/PrivacyPolicy'
import { UserContext } from './UserContext'

export default function App () {
  const [user, setUser] = useState({})

  return (
    <div className='App'>
      <Router>
        <UserContext.Provider value={{ user, setUser }}>
          <Route exact path='/' component={Home} />
          <Route exact path='/login' component={Login} />
          <Route exact path='/welcome' component={Welcome} />
          <Route exact path='/new' component={NewGame} />
          <Route exact path='/play/:gameId' component={PlayGame} />
          <Route exact path='/join/:gameId' component={JoinGame} />
        </UserContext.Provider>
        <Route exact path='/privacy' component={PrivacyPolicy} />
        <Route exact path='/admin' component={Admin} />
      </Router>
    </div>
  )
}
