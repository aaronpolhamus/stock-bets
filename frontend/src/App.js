import React from 'react';
import './App.css';

import { BrowserRouter as Router, Route } from 'react-router-dom';
import Home from './pages/Home';
import Login from './pages/Login'
import Welcome from './components/Welcome';
import Sidebar from './components/Sidebar';

const sidebar_items = [
  { name: "home", label: "Home" },
  { 
    name: "games", 
    label: "Games",
    items: [
      { name: "make", label: "Make" },
      { name: "join", label: "Join" },
      { name: "play", label: "Play" }
    ]
  },
  { 
    name: "profile", 
    label: "Profile",
    items: [
      { name: "userInfo", label: "User info"},
      { name: "moneyManagement", label: "Money management" },
    ] 
  },
]

export default function App() {
  return (
    <div className="App">
      <Router>
        <Route path={/^(?!.*(login|welcome)).*$/} render={() => <Sidebar items={ sidebar_items }/>} />
        <Route exact path='/' component={Home} />
        <Route exact path='/login' component={Login} />
        <Route exact path='/welcome' component={Welcome} />
      </Router>
    </div>
  );
}