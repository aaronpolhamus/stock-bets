import React, { useState, useCallback } from "react";
import { Button, Modal, Accordion, Form } from "react-bootstrap";
import {
  TextButton,
  AuxiliarText,
  FlexRow,
} from "components/textComponents/Text";
import { AsyncTypeahead } from "react-bootstrap-typeahead";
import styled from "styled-components";
import * as Icon from "react-feather";
import { apiPost } from "components/functions/api";
import { UserMiniCard } from "components/users/UserMiniCard";

const AddFriends = (props) => {
  const [friendSuggestions, setFriendSuggestions] = useState([]);

  const [friendInvitee, setFriendInvitee] = useState("");

  const [show, setShow] = useState(false);

  const handleClose = () => setShow(false);

  const handleFriendInvite = async (e) => {
    e.preventDefault();

    if (friendInvitee !== "") {
      await apiPost("send_friend_request", {
        friend_invitee: friendInvitee,
      });
      setShow(true);
    }
  };

  const handleChange = (invitee) => {
    if (invitee[0] === undefined) return;
    setFriendInvitee(invitee[0].username);
  };

  const handleSuggestions = async (query) => {
    const friends = await apiPost("suggest_friend_invites", { text: query });
    setFriendSuggestions(friends);
  };

  const friendLabel = (label) => {
    switch (label) {
      case "you_invited":
        return <AuxiliarText>Invite sent</AuxiliarText>;
      case "invited_you":
        return <AuxiliarText>Invited you</AuxiliarText>;
    }
  };

  return (
    <Accordion defaultActiveKey="0" className="text-right">
      <Accordion.Toggle
        as={TextButton}
        eventKey="1"
        color="var(--color-light-gray)"
      >
        <span>Add Friend </span>
        <Icon.PlusCircle color="var(--color-primary)" size="16" />
      </Accordion.Toggle>
      <Accordion.Collapse eventKey="1">
        <Form onSubmit={handleFriendInvite}>
          <Form.Group>
            <AsyncTypeahead
              id="typeahead-particpants"
              name="invitees"
              labelKey={"username"}
              options={friendSuggestions}
              placeholder="Who's playing?"
              onSearch={handleSuggestions}
              onChange={handleChange}
              renderMenuItemChildren={(option, props) => (
                <FlexRow justify="space-between">
                  <UserMiniCard
                    avatarSrc={option.profile_pic}
                    avatarSize="small"
                    username={option.username}
                  />
                  {friendLabel(option.label)}
                </FlexRow>
              )}
            />
          </Form.Group>
          <Accordion.Toggle as={Button} size="sm" variant="outline-primary">
            Close
          </Accordion.Toggle>
          <Button type="submit" size="sm">
            Add friend
          </Button>
        </Form>
      </Accordion.Collapse>
      <Modal show={show} onHide={handleClose}>
        <Modal.Body>
          <div className="text-center">
            You've invited
            <strong> {friendInvitee} </strong>
            <div>to be friends with you.</div>
            <div>
              <small>We'll let them know!</small>
            </div>
          </div>
        </Modal.Body>
        <Modal.Footer className="centered">
          <Button variant="primary" onClick={handleClose}>
            Awesome!
          </Button>
        </Modal.Footer>
      </Modal>
    </Accordion>
  );
};

export { AddFriends };
