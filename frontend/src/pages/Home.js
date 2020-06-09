import React, { useEffect } from "react";
import { Link, Redirect } from "react-router-dom";
import { Button } from "react-bootstrap";
import { isEmpty, usePostRequest } from "components/functions/api";
import api from "services/api";
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
import * as Icon from "react-feather";
import LogRocket from "logrocket";

// Left in un-used for now: we'll almost certainly get to this later
const Logout = async () => {
  await api.post("/api/logout");
  window.location.assign("/login");
};

const GameList = styled.div`
  margin-top: var(--space-400);
`;

const Invitation = styled(Link)`
  color: ${(props) => props.color || "var(--color-text-primary)"};
  font-size: var(--font-size-small);
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

  useEffect(() => {
    // identify user once they've hit the homepage
    LogRocket.identify(data.id, {
      name: data.name,
      email: data.email,
    });
  }, [data]);

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

  const gameListBuilder = (data) => {
    return data.map((entry, index) => {
      if (entry.game_status === "active") {
        return <GameCard gameId={entry.game_id} key={index} />;
      }
      return "";
    });
  };

  const pendingListBuilder = (data, inviteStatus) => {
    return data.map((entry, index) => {
      if (
        entry.game_status === "pending" &&
        entry.invite_status === inviteStatus &&
        entry.invite_status === "invited"
      ) {
        return (
          <div key={index}>
            <Invitation to={{ pathname: `join/${entry.game_id}` }}>
              <span>
                <Icon.UserCheck color="var(--color-terciary)" size={16} />
              </span>
              <span> [username] invited you to </span>
              <strong> {entry.title}</strong>
            </Invitation>
          </div>
        );
      } else if (
        entry.game_status === "pending" &&
        entry.invite_status === inviteStatus &&
        entry.invite_status === "joined"
      ) {
        return (
          <div key={index}>
            <Invitation
              to={{ pathname: `join/${entry.game_id}` }}
              color="var(--color-text-gray)"
            >
              <Icon.CheckCircle color="var(--color-success)" size={16} />
              <span>
                {" "}
                You joined
                <strong> {entry.title}</strong>. The Game will start once all
                participants respond to their invitations.
              </span>
            </Invitation>
          </div>
        );
      }
      return null;
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
          <Button variant="success" href="/new">
            Make a new game
          </Button>
        </Header>
        <GameList>
          {data.game_info && pendingListBuilder(data.game_info, "invited")}
        </GameList>
        <GameList>{data.game_info && gameListBuilder(data.game_info)}</GameList>
        <GameList>
          {data.game_info && pendingListBuilder(data.game_info, "joined")}
        </GameList>
      </Content>
    </Layout>
  );
};

export default Home;
