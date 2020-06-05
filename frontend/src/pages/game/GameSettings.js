import React from "react";
import { SidebarSection } from "components/layout/Layout";
import { SectionTitle } from "components/textComponents/Text";
import { UserMiniCard } from "components/users/UserMiniCard";

const GameSettings = ({ gameInfo }) => {
  console.log(gameInfo);
  return (
    <div>
      <SidebarSection>
        <SectionTitle color="var(--color-primary)">Game Host</SectionTitle>
        <UserMiniCard
          username={gameInfo.creator_username}
          nameColor="var(--color-lighter)"
        />
      </SidebarSection>
      <SidebarSection>
        <SectionTitle color="var(--color-primary)">Game Settings</SectionTitle>
        <dl>
          <dt>Game Mode</dt>
          <dd>{gameInfo.mode}</dd>
          <dt>Buy In</dt>
          <dd>{gameInfo.buy_in}</dd>
          <dt>Game Duration</dt>
          <dd>{gameInfo.duration} days</dd>
          <dt>Benchmark</dt>
          <dd>{gameInfo.benchmark}</dd>
          <dt>Sidebet</dt>
          <dd>
            {gameInfo.side_bets_perc}% {gameInfo.side_bets_period}
          </dd>
          <dt>Number of rebuys</dt>
          <dd>{gameInfo.n_rebuys}</dd>
        </dl>
      </SidebarSection>
    </div>
  );
};

export { GameSettings };
