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
    try {
      await axios.post("/api/set_username", {
        withCredentials: true,
        username: username
      })
      setUpdated(true)
    }
    catch (error) {
      alert(`'${username}' looks like it's taken, try another one`)
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
          <h2>Welcome! Pick a username that other plays will see and let's get started.</h2>
          <input onChange={handleChange} type="text" name="username" placeholder="Enter name here" />
          <button onClick={handleSubmit}>Submit</button>
        </form>
      </div>
    </div>
  );
}

export default Welcome;
