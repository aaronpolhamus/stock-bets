import React from "react";
import { Link, Redirect } from "react-router-dom";
import { Button } from "react-bootstrap";
import { isEmpty, usePostRequest } from "components/functions/api";
import axios from "axios";
import styled from "styled-components";
import {
  Layout,
  Sidebar,
  Content,
  Header,
  Breadcrumb,
} from "components/layout/Layout";
import { UserMiniCard } from "components/users/UserMiniCard";
import { FriendsList } from "components/lists/FriendsList";
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

const StyledMiniCard = styled(UserMiniCard)`
  padding-bottom: var(--space-400);
  border-bottom: 1px solid rgba(0, 0, 0, 0.3);
  position: relative;
  &::after {
    position: absolute;
    bottom: 0px;
    left: 0;
    content: "";
    display: block;
    height: 1px;
    width: 100%;
    background-color: rgba(255, 255, 255, 0.1);
  }
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
    return gamesArray.map((entry, index) => {
      if (entry.status === statusType) {
        return <GameCard gameId={entry.id} key={index} />;
      }

      return "";
    });
  };

  const invitesBuilder = (gamesArray) => {
    return gamesArray.map((entry, index) => {
      if (entry.status === "pending") {
        return (
          <div key={index}>
            <Invitation to={{ pathname: `join/${entry.id}` }}>
              You have an invitation to:
              <strong> {entry.title}</strong>
            </Invitation>
          </div>
        );
      }
      return "";
    });
  };

  return (
    <Layout>
      <Sidebar>
        <StyledMiniCard
          avatarSrc={data.profile_pic}
          username={data.username}
          email={data.email}
          nameColor="var(--color-lighter)"
          dataColor="var(--color-text-light-gray)"
          info={["Return: 50%", "Sharpe: 0.324"]}
        />
        <FriendsList />
      </Sidebar>
      <Content>
        <Breadcrumb justifyContent="flex-end">
          <Button variant="link" onClick={Logout}>
            Logout
          </Button>
        </Breadcrumb>
        <Header>
          <h1>Games</h1>
          <Button href="/new">Make a new game</Button>
        </Header>
        <GameList>{data && invitesBuilder(data.game_info)}</GameList>
        <GameList>{data && gameCardBuilder("active", data.game_info)}</GameList>
      </Content>
    </Layout>
  );
};

export default Home;
