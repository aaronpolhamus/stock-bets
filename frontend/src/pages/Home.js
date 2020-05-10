import React from 'react';
import { Redirect } from 'react-router-dom';
import {isEmpty, usePostRequest} from "../components/api";
import Button from "../components/Button.jsx"
import axios from "axios";

const Logout = async () => {
  await axios.post('/api/logout')
  window.location.assign('/login')
};

const Home = () => {

  const { data, loading, error } = usePostRequest('/api/home');
   
  if (loading) {
    return <p>Loading...</p>
  }

  if ( !isEmpty(error) ) { 
    if (error.response.status === 401){ 
      return <Redirect to="/login" />
    }
  }
  
  if( isEmpty(data.username)) { 
    return <Redirect to="/welcome" />
  }
  
  return (
    <div className="App">
      <h1> What's up, { data.name } ( {data.username} )? Your email is { data.email } </h1> 
      <img src={ data.profile_pic} height="200" width="200" alt="your beautiful profile pic"/>
      <Button onClick={Logout}>Logout</Button>
    </div>
  );
};

export default Home;