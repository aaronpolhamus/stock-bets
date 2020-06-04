import React from "react";
import { Link } from "react-router-dom";
import { MakeGame } from "components/forms/MakeGame";
import {
  Layout,
  Sidebar,
  Content,
  Breadcrumb,
  Header,
} from "components/layout/Layout";

const NewGame = () => {
  return (
    <Layout>
      <Sidebar size="small" />
      <Content>
        <Breadcrumb>
          <Link to="/">&lt; Dashboard</Link>
        </Breadcrumb>
        <Header>
          <h1>New Game</h1>
        </Header>
        <MakeGame />
      </Content>
    </Layout>
  );
};

export { NewGame };