import React from "react";
import { Link, Redirect } from "react-router-dom";
import { Button, Container, Row, Col, Card } from "react-bootstrap";
import { isEmpty, usePostRequest } from "components/functions/api";
import axios from "axios";
import styled from "styled-components";
import { Layout, Sidebar, Content, Header } from "components/layout/Layout";
import { UserMiniCard } from "components/users/UserMiniCard";

import { GameCard } from "pages/game/GameCard";

// Left in un-used for now: we'll almost certainly get to this later
const Logout = async () => {
  await axios.post("/api/logout");
  window.location.assign("/login");
};

const GameList = styled.div`
  margin-top: var(--space-400);
`;

const Invitation = styled(Link)`
  color: var(--color-text-primary);
`;

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
      if (entry.status === statusType) {
        return <GameCard gameId={entry.id} />;
      }
    });
  };

  const invitesBuilder = (gamesArray) => {
    return gamesArray.map((entry) => {
      if (entry.status === "pending") {
        return (
          <div>
            <Invitation to={{ pathname: `join/${entry.id}` }}>
              You have an invitation to:
              <strong> {entry.title}</strong>
            </Invitation>
          </div>
        );
      }
    });
  };

  return (
    <Layout>
      <Sidebar>
        <UserMiniCard
          avatarSrc={data.profile_pic}
          username={data.username}
          email={data.email}
          nameColor="var(--color-lighter)"
          dataColor="var(--color-text-light-gray)"
          info={["Return: 50%", "Sharpe: 0.324"]}
        />
        <p>
          <Button onClick={Logout}>Logout</Button>
        </p>
      </Sidebar>
      <Content>
        <Header>
          <h1>Games</h1>
          <Button href="/make">Make a new game</Button>
        </Header>
        <GameList>{data && invitesBuilder(data.game_info)}</GameList>
        <GameList>{data && gameCardBuilder("active", data.game_info)}</GameList>
      </Content>
    </Layout>
  );
};

export default Home;
