import React from 'react';

import '../App.css';

export default function Landing() {
  const resp = fetch('/', {method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({msg: "test"})});
  console.log(resp)
  // axios.post("/", JSON.stringify({message: "test"})).then(api_response => console.log(api_response))
  
  return (
    <div>
        <h1>Here's the API response: "API RESPONSE HERE" -- what do you want to do now?</h1>    
    </div>
  );
};
