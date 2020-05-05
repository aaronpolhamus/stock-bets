import React from 'react';
import { Redirect } from 'react-router-dom';
import {isEmpty, usePostRequest} from "../components/api";
import Button from "../components/Button.jsx"
import axios from "axios";

const Logout = async () => {
  await axios.post('/logout')
  window.location.assign('/login')
};

class Home extends React.Component {
  constructor(props) {
    super(props)
  }

  render () {
    const { data, loading, error } = usePostRequest('/');

    if (loading) {
      return <p>Loading...</p>
    }
  
    if ( !isEmpty(error) ) { 
      if (error.response.status === 401){ 
        return <Redirect to="/login" />
      }
    }
    
    return (
      <div className="App">
        <h1> What's up, { data.name }? Your email is { data.email } </h1> 
        <img src={ data.profile_pic} alt="your lovely profile pic"/>
        <br></br>
        <br></br>
        <Button onClick={Logout}>Logout</Button>
      </div>
    );
  }
};

export default Home;