import React, { useState } from "react";
import axios from "axios";
import { Redirect } from "react-router-dom";

const Welcome = () => {
  const [username, setUserName] = useState("")
  const [updated, setUpdated] = useState(false)

  const handleChange = (e) => {
    setUserName(e.target.value)
  }
  
  const handleSubmit = async (e) => { 
    e.preventDefault()
    const response = await axios.post("/api/set_username", {
      withCredentials: true,
      username: username
    })
    if(response.status === 200){ 
      setUpdated(true)
    }
  }

  if (updated) { 
    return(
      <Redirect to="/" />
    )
  }

  return (
    <div className="modal">
      <div className="modal_content">
        <form>
          <input onChange={handleChange} type="text" name="username" placeholder="Enter name here" />
          <button onClick={handleSubmit}>Submit</button>
        </form>
      </div>
    </div>
  );
}

export default Welcome;
