import 'App.scss'

import React from 'react'
import ReactDOM from 'react-dom'
import App from './App'
import * as serviceWorker from './serviceWorker'

import LogRocket from 'logrocket'
import ReactGA from 'react-ga'

// User traffic monitoring
ReactGA.initialize(process.env.REACT_APP_GA_TRACKING_ID)
LogRocket.init(process.env.REACT_APP_LOG_ROCKET_ID)

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
)

if (module.hot) {
  module.hot.accept('./App', () => {
    const NextApp = require('./App').default
    ReactDOM.render(
      <NextApp />,
      document.getElementById('root')
    )
  })
}

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister()
