import React from "react";
import { useParams } from "react-router-dom";
import { Layout, Sidebar, Content } from "components/layout/Layout";
import { PlaceOrder } from "components/forms/PlaceOrder";

const JoinGame = (props) => {
  const { gameId } = useParams();

  return (
    <Layout>
      <Sidebar>
        <PlaceOrder gameId={gameId} />
      </Sidebar>
      <Content>Hello</Content>
    </Layout>
  );
};

export { JoinGame };
