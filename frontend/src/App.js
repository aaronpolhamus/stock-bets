import React from 'react';
import './App.css';

import { BrowserRouter as Router, Route } from 'react-router-dom';
import Home from './pages/Home';
import Login from './pages/Login'
import Welcome from './components/Welcome';
import {MakeGame} from "./pages/MakeGame";

export default function App() {
  return (
    <div className="App">
      <Router>
        <Route exact path='/' component={Home} />
        <Route exact path='/login' component={Login} />
        <Route exact path='/welcome' component={Welcome} />
        <Route exact path='/make' component={MakeGame} />
      </Router>
    </div>
  );
}