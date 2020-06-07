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

  const getFriendSuggestions = async (query) => {
    const friends = await apiPost("suggest_friend_invites", { text: query });
    console.log(query, friends);
    setFriendSuggestions(friends);
  };

  const handleSuggestions = useCallback((query) => {
    setIsLoading(true);
    getFriendSuggestions(query);
  });

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
        <Form.Group>
          <AsyncTypeahead
            id="typeahead-particpants"
            name="invitees"
            labelKey="name"
            options={friendSuggestions}
            placeholder="Who's playing?"
            onSearch={handleSuggestions}
          />
        </Form.Group>
      </Accordion.Collapse>
    </Accordion>
  );
};

export { AddFriends };
