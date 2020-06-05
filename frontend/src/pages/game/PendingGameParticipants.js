import React from "react";
import styled from "styled-components";
import { Button, Table } from "react-bootstrap";
import { Header, SidebarSection } from "components/layout/Layout";
import { SectionTitle } from "components/textComponents/Text";
import { UserMiniCard } from "components/users/UserMiniCard";

const PendingGameParticipants = ({ participants }) => {
  console.log(participants);

  const participantsBuilder = (participants) => {
    return participants.map((participant, index) => {
      return (
        <tr>
          <td key={index}>
            <UserMiniCard
              avatarSrc={participant.profile_pic}
              avatarSize="small"
              username={participant.username}
            />
          </td>
          <td>{participant.status}</td>
        </tr>
      );
    });
  };

  return (
    <div>
      <SectionTitle>Participants</SectionTitle>
      <Table>
        <thead>
          <tr>
            <th>Player</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>{participants && participantsBuilder(participants)}</tbody>
      </Table>
    </div>
  );
};

export { PendingGameParticipants };
