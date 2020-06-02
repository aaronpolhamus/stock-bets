import React from "react";
import { Redirect } from "react-router-dom";
import { Row } from "react-bootstrap";
import { isEmpty, usePostRequest } from "components/functions/api";
import axios from "axios";

// Left in un-used for now: we'll almost certainly get to this later
const Logout = async () => {
  await axios.post("/api/logout");
  window.location.assign("/login");
};

const Home = () => {
  const { data, loading, error } = usePostRequest("/api/home");

  if (loading) {
    return <p>Loading...</p>;
  }

  if (!isEmpty(error)) {
    if (error.response.status === 401) {
      return <Redirect to="/login" />;
    }
  }

  if (isEmpty(data.username)) {
    return <Redirect to="/welcome" />;
  }

  return (
    <div className="App">
      <Row>
        <h1>
          {" "}
          What's up, {data.name} ( {data.username} )? Your email is {data.email}{" "}
        </h1>
      </Row>
      <Row className="justify-content-md-center">
        <img
          src={data.profile_pic}
          height="200"
          width="200"
          alt="your beautiful profile pic"
        />
      </Row>
    </div>
  );
};

export default Home;
