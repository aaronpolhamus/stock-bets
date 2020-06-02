import React from "react";
import { BrowserRouter as Router, Route } from "react-router-dom";

import Home from "pages/Home";
import Login from "pages/Login";
import Welcome from "components/Welcome";
import { Workbench } from "pages/Workbench";

import "./App.css";

export default function App() {
  return (
    <div className="App">
      <Router>
        <Route exact path="/" component={Home} />{" "}
        <Route exact path="/login" component={Login} />
        <Route exact path="/welcome" component={Welcome} />
        <Route exact path="/workbench" component={Workbench} />
      </Router>
    </div>
  );
}
