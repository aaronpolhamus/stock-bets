import React from 'react';
import './App.css';

import { BrowserRouter as Router, Route } from 'react-router-dom';
import Home from './pages/Home';
import Login from './pages/Login'
import Welcome from './components/Welcome';
import Sidebar from './components/Sidebar';
import {MakeGame, PlayGame, JoinGame} from "./pages/Games";

const sidebar_items = [
  { name: "home", label: "Home", url: "/" },
  { 
    name: "games", 
    label: "Games",
    items: [
      { name: "make", label: "Make", url: "/make"},
      { name: "join", label: "Join", url: "/join"},
      { name: "play", label: "Play", url: "/play" }
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

const no_nav_paths = ["/login", "/welcome"]

export default function App() {
  return (
    <div className="App">
      <Router>
        <Route render={() => {
          if(!no_nav_paths.includes(window.location.pathname)){
            return <Sidebar items={ sidebar_items }/>
          }
        }} />
        <Route exact path='/' component={Home} />
        <Route exact path='/login' component={Login} />
        <Route exact path='/welcome' component={Welcome} />
        <Route exact path='/make' component={MakeGame} />
        <Route exact path='/join' component={JoinGame} />
        <Route exact path='/play' component={PlayGame} />
      </Router>
    </div>
  );
}