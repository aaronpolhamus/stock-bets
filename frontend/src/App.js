import React from 'react';
import './App.css';

import { BrowserRouter as Router, Route } from 'react-router-dom';
import Landing from './components/Landing';
import AlphabetLogin from './components/AlphabetLogin'

export default function App() {
  return (
    <div className="App">
      <Router>
        <Route exact path='/' component={Landing} />
        <Route exact path='/login' component={AlphabetLogin} />
      </Router>
    </div>
  );
}
