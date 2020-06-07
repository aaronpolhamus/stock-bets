import React from "react";
import { Button, Modal, Accordion, Card, Form } from "react-bootstrap";
import { SectionTitle, TextButton } from "components/textComponents/Text";
import styled from "styled-components";
import * as Icon from "react-feather";

const AddFriends = (props) => {
  return (
    <Accordion defaultActiveKey="0">
      <Accordion.Toggle
        as={TextButton}
        eventKey="1"
        color="var(--color-light-gray)"
      >
        <span>Add Friend </span>
        <Icon.PlusCircle color="var(--color-primary)" size="16" />
      </Accordion.Toggle>
      <Accordion.Collapse eventKey="1">
        <span>Hello! I'm the body</span>
      </Accordion.Collapse>
    </Accordion>
  );
};

export { AddFriends };
