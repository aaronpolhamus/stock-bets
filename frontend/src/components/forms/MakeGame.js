import React, { useState, useEffect } from "react";
import api from "services/api";
import { Form, Button, Row, Col } from "react-bootstrap";
import { Typeahead } from "react-bootstrap-typeahead";
import { optionBuilder } from "components/functions/forms";

const MakeGame = () => {
  const [defaults, setDefaults] = useState({});
  const [sidePotPct, setSidePotPct] = useState(0);
  const [formValues, setFormValues] = useState({});

  const fetchData = async () => {
    const response = await api.post("/api/game_defaults");
    if (response.status === 200) {
      setDefaults(response.data);
      setFormValues(response.data); // this syncs our form value submission state with the incoming defaults
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log(e, formValues);
    await api
      .post("/api/create_game", formValues)
      .then()
      .catch((e) => {
        console.log(e);
      });
  };

  const handleChange = (e) => {
    let formValuesCopy = { ...formValues };
    formValuesCopy[e.target.name] = e.target.value;
    setFormValues(formValuesCopy);
  };

  // necessary because this field has a special change action whereby the
  const handleSideBetChange = (e) => {
    setSidePotPct(e.target.value);
    let formValuesCopy = { ...formValues };
    formValuesCopy["side_bets_perc"] = e.target.value;
    setFormValues(formValuesCopy);
  };

  // I'm not in love wit this separate implementation for typeahead fields. I couldn't figure out a good way to get them to play well
  // with standard bootstrap controlled forms, so this is what I went with
  const handleInviteesChange = (inviteesInput) => {
    let formValuesCopy = { ...formValues };
    formValuesCopy["invitees"] = inviteesInput;
    setFormValues(formValuesCopy);
  };

  return (
    <Form onSubmit={handleSubmit}>
      {/* We should probably have this on the bottom of the form. It's just here for now because test_user can't write CSS */}
      <Row>
        <Col lg={4}>
          <Form.Group>
            <Form.Label>Title</Form.Label>
            <Form.Control
              name="title"
              type="input"
              defaultValue={defaults.title}
              onChange={handleChange}
            />
          </Form.Group>
          <Form.Group>
            <Form.Label>Game mode</Form.Label>
            <Form.Control
              name="mode"
              as="select"
              defaultValue={defaults.mode}
              onChange={handleChange}
            >
              {defaults.game_modes && optionBuilder(defaults.game_modes)}
            </Form.Control>
          </Form.Group>
          <Row>
            <Col xs={6}>
              <Form.Group>
                <Form.Label>Game duration (days)</Form.Label>
                <Form.Control
                  name="duration"
                  type="input"
                  defaultValue={defaults.duration}
                  onChange={handleChange}
                />
              </Form.Group>
            </Col>
          </Row>
          <Row>
            <Col xs={6}>
              <Form.Group>
                <Form.Label>Buy-in</Form.Label>
                <Form.Control
                  name="buy_in"
                  type="input"
                  defaultValue={defaults.buy_in}
                  onChange={handleChange}
                />
              </Form.Group>
            </Col>
            <Col xs={6}>
              <Form.Group>
                <Form.Label>Number of re-buys</Form.Label>
                <Form.Control
                  name="n_rebuys"
                  type="input"
                  defaultValue={defaults.n_rebuys}
                  onChange={handleChange}
                />
              </Form.Group>
            </Col>
          </Row>
          <Form.Group>
            <Form.Label>Benchmark</Form.Label>
            <Form.Control
              name="benchmark"
              as="select"
              defaultValue={defaults.benchmark}
              onChange={handleChange}
            >
              {defaults.benchmarks && optionBuilder(defaults.benchmarks)}
            </Form.Control>
          </Form.Group>
        </Col>
        <Col lg={4}>
          <Form.Group>
            <Form.Label>Add Participant</Form.Label>
            <Typeahead
              id="typeahead-particpants"
              name="invitees"
              labelKey="name"
              multiple
              options={
                defaults.available_invitees &&
                Object.values(defaults.available_invitees)
              }
              placeholder="Who's playing?"
              onChange={handleInviteesChange}
            />
          </Form.Group>
        </Col>
        <Col lg={4}>
          <Form.Group>
            <Form.Label>Sidebet % of pot</Form.Label>
            <Form.Control
              name="side_bets_perc"
              type="input"
              defaultValue={defaults.side_bets_perc}
              value={sidePotPct}
              onChange={handleSideBetChange}
            />
          </Form.Group>
          {sidePotPct > 0 && (
            <Form.Group>
              <Form.Label>Sidebet period</Form.Label>
              <Form.Control
                name="side_bets_period"
                as="select"
                defaultValue={defaults.side_bets_period}
                onChange={handleChange}
              >
                {defaults.sidebet_periods &&
                  optionBuilder(defaults.sidebet_periods)}
              </Form.Control>
            </Form.Group>
          )}
        </Col>
      </Row>
      <div className="text-right">
        <Button variant="primary" type="submit">
          Create New Game
        </Button>
      </div>
    </Form>
  );
};

export { MakeGame };
