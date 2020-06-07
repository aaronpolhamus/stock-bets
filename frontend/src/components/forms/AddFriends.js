import React, { useState, useEffect, useCallback } from "react";
import { Button, Modal, Accordion, Card, Form } from "react-bootstrap";
import { SectionTitle, TextButton } from "components/textComponents/Text";
import { AsyncTypeahead } from "react-bootstrap-typeahead";
import styled from "styled-components";
import * as Icon from "react-feather";
import { apiPost } from "components/functions/api";

const AddFriends = (props) => {
  const [defaults, setDefaults] = useState({});

  const [formValues, setFormValues] = useState({});
  const [friendSuggestions, setFriendSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [friendInvitee, setFriendInvitee] = useState("");

  const [show, setShow] = useState(false);

  const getFriendSuggestions = async (query) => {
    const friends = await apiPost("suggest_friend_invites", { text: query });
    setFriendSuggestions(friends);
  };

  const handleClose = () => setShow(false);

  const handleFriendInvite = async (e) => {
    e.preventDefault();

    if (friendInvitee !== "") {
      const invite = await apiPost("send_friend_request", {
        friend_invitee: friendInvitee,
      });
      setShow(true);
    }
  };

  const handleChange = (e) => {
    setFriendInvitee(e[0]);
    console.log(friendInvitee);
  };

  const handleSuggestions = useCallback((query) => {
    setIsLoading(true);
    getFriendSuggestions(query);
  });

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
              labelKey="name"
              options={friendSuggestions}
              placeholder="Who's playing?"
              onSearch={handleSuggestions}
              onChange={handleChange}
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
          <p className="text-center">
            You've invited
            <strong> {friendInvitee} </strong>
            <div>to be friends with you.</div>
            <div>
              <small>We'll let them know!</small>
            </div>
          </p>
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
