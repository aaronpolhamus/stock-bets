import React from 'react';
import GoogleLogin from 'react-google-login';
 
 
const responseGoogle = (response) => {
  console.log(response);
}

function AlphabetLogin() { 
  return (
    <div className="App">
      <GoogleLogin
        clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}
        buttonText="Login with Google"
        onSuccess={responseGoogle}
        onFailure={responseGoogle}
        cookiePolicy={'single_host_origin'}        />
    </div>
  )
}

export default AlphabetLogin;