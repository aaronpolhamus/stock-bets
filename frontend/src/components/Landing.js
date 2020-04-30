import React from 'react';
import { Redirect } from 'react-router-dom';
import {isEmpty, usePostRequest} from "./api";

const Landing = () => {
  const { data, loading, error } = usePostRequest('/');
   
  if (loading) {
    return <p>Loading...</p>
  }

  if ( !isEmpty(error) ) { 
    if (error.response.status == 401){ 
      return <Redirect to="/login" />
    }
  }
  
  return (
    <div>
      <h1> What's up, { data.name }? Your email is { data.email } </h1> 
      <img src={ data.profile_pic} />  
    </div>
  );
};

export default Landing;