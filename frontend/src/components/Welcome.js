import React, { useState } from "react";
import api from "services/api";
import { Redirect } from "react-router-dom";
import { Form, Button } from "react-bootstrap";

const Welcome = () => {
  const [username, setUserName] = useState("");
  const [updated, setUpdated] = useState(false);

  const handleChange = (e) => {
    setUserName(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/api/set_username", {
        withCredentials: true,
        username: username,
      });
      setUpdated(true);
    } catch (error) {
      alert(`'${username}' looks like it's taken, try another one`);
      setUpdated(false);
    }
  };

  if (updated) {
    return <Redirect to="/" />;
  }

  return (
    <Form>
      <Form.Label>
        Welcome! Pick a username that other players will see and let's get
        started.
      </Form.Label>
      <Form.Control
        onChange={handleChange}
        type="input"
        name="username"
        placeholder="Enter name here"
      />
      <Button onClick={handleSubmit} variant="primary" type="submit">
        Submit
      </Button>
    </Form>
  );
};

export default Welcome;
