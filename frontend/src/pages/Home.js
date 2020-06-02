import React from "react";
import { Link, Redirect } from "react-router-dom";
import { Button, Container, Row, Col, Card } from "react-bootstrap";
import { isEmpty, usePostRequest } from "components/functions/api";
import axios from "axios";
import { Sidebar } from "components/layout/Sidebar";
import { Layout } from "components/layout/Layout";
import { UserMiniCard } from "components/users/UserMiniCard";

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

  const gameCardBuilder = (statusType, gamesArray) => {
    return gamesArray.map((entry) => {
      let linkTo = null;
      if (entry.status === "pending") {
        linkTo = "/join";
      } else if (entry.status === "active") {
        linkTo = "/play";
      }

      if (entry.status === statusType) {
        return (
          <Card key={entry.id}>
            <Card.Body>
              <Link to={{ pathname: `${linkTo}/${entry.id}` }}>
                {entry.title}
              </Link>
            </Card.Body>
          </Card>
        );
      }
    });
  };

  return (
    <Layout>
      <Sidebar>
        <UserMiniCard
          pictureSrc={data.profile_pic}
          name={data.name}
          username={data.username}
          email={data.email}
          stats={{
            absoluteReturn: "50%",
            sharpeRatio: "0.17",
          }}
        />
      </Sidebar>
      <Container fluid="md">
        <Row>
          <Col>
            <Button href="/make">Make a new game</Button>
          </Col>
          <Col>
            <Button onClick={Logout}>Logout</Button>
          </Col>
        </Row>
        <Row>
          <Col>
            <Card.Header>Active games</Card.Header>
            {data && gameCardBuilder("active", data.game_info)}
          </Col>
          <Col>
            <Card.Header>Game invites</Card.Header>
            {data && gameCardBuilder("pending", data.game_info)}
          </Col>
        </Row>
      </Container>
    </Layout>
  );
};

export default Home;
