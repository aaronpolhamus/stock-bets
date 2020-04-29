import React, { Component } from "react";
import GoogleLogin from "react-google-login";
import axios from "axios";
import { Redirect } from "react-router-dom";

class AlphabetLogin extends Component {   

  state = {
    redirect: false
  }

  handleSubmit (response) {
    axios.post("/register", response)
      .then(() => this.setState({ redirect: true }));
  }

  responseError (response) {
    return (
      <div>
        <h1>Google login failed. Here's the response that you got back:</h1>
        <p>{ response }</p>
      </div>
    )
  }

  render() {
    const { redirect } = this.state

    if (redirect) { 
      return <Redirect to='/'/>
    }

    return (
      <div className="App">
        <GoogleLogin
          clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}
          buttonText="Login with Google"
          onSuccess={this.handleSubmit}
          onFailure={this.responseError}
          cookiePolicy={"single_host_origin"}        />
      </div>
    )
  }
};

export default AlphabetLogin;