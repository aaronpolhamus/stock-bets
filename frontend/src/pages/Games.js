import React, { useState, useEffect } from "react";
import axios from "axios";
import { Form, Button, Card } from "react-bootstrap";
import { Typeahead } from "react-bootstrap-typeahead";

const multiSelectParse = (element) => {
  let output = []
  let i = 0
  for (i = 0; i < element.length; i++){
    output.push(element[i].value)
  }
  return output
}

const elementsParse = (elements) => {
  let output = {}
  let i = 0;
  for (i = 0; i < elements.length; i++) {
    const element = elements[i]
    if( element.className.includes("multiselect")){
      output[element.id] = multiSelectParse(element)
    } else { 
      output[element.id] = element.value
    }
  }
  
  return output
}

const JoinGame = () => {
  return(
    <div>
      <h1>Join a game here</h1>
    </div>
  )
}

const MakeGame = () => {  
  const [defaults, setDefaults] = useState({})
  const [sidePotPct, setSidePotPct] = useState(0)
  const [formValues, setFormValues] = useState({})

  const fetchData = async () => {
    const response = await axios.post("/api/game_defaults")
    if (response.status === 200){
      setDefaults(response.data)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])
  
  const optionBuilder = (optionsArray) => 
    Object.keys(optionsArray).map((key, index) => 
    <option key={key} value={optionsArray[key]}>{optionsArray[key]}</option>)

  const handleSubmit = async (event) => {
    event.preventDefault()
    const form = event.currentTarget;
    if (form.checkValidity() === false) {
      event.preventDefault();
      event.stopPropagation();
    }
    const payload = elementsParse(form.elements)
    await axios.post("/api/create_game", payload)
    console.log(form.elements)
  };

  return( 
  <Form>
    <Form.Group>
      <Form.Label>Title</Form.Label>
      <Form.Control name="title" type="input" defaultValue={defaults.default_title}/>
    </Form.Group>
    <Form.Group>
      <Form.Label>Game mode</Form.Label>
      <Form.Control name="mode" as="select" defaultValue={defaults.default_game_mode}>
        {defaults.game_modes && optionBuilder(defaults.game_modes)}
      </Form.Control>
    </Form.Group>
    <Form.Group>
      <Form.Label>Game duration (days)</Form.Label>
      <Form.Control name="duration" type="input" defaultValue={defaults.default_duration}/>
    </Form.Group>
    <Form.Group>
      <Form.Label>Buy-in</Form.Label>
      <Form.Control name="buy_in" type="input" defaultValue={defaults.default_buyin}/>
    </Form.Group>
    <Form.Group>
      <Form.Label>Number of re-buys</Form.Label>
      <Form.Control name="n_rebuys" type="input" defaultValue={defaults.default_rebuys}/>
    </Form.Group>
    <Form.Group>
      <Form.Label>Benchmark</Form.Label>
      <Form.Control name="benchmark" as="select" defaultValue={defaults.default_benchmark}>
        {defaults.benchmarks && optionBuilder(defaults.benchmarks)}
      </Form.Control>
    </Form.Group>
    <Form.Group>
      <Form.Label>Sidebet % of pot</Form.Label>
      <Form.Control name="side_bets_perc" type="input" value={sidePotPct} onChange={(e) => setSidePotPct(e.target.value)}/>
    </Form.Group>
    {sidePotPct > 0 &&
      <Form.Group>
        <Form.Label>Sidebet period</Form.Label>
        <Form.Control name="side_bets_period" as="select" defaultValue={defaults.default_sidebet_period}>
          {defaults.sidebet_periods && optionBuilder(defaults.sidebet_periods)}
        </Form.Control>
      </Form.Group>
    }
    <Form.Group>
      <Form.Label>Participants</Form.Label>
      <Typeahead
        name="participants"
        labelKey="name"
        multiple
        options={defaults.available_participants && Object.values(defaults.available_participants)}
        placeholder="Who's playing?"
      />
    </Form.Group>
    <Button variant="primary" type="submit">
      Submit
    </Button>
  </Form>
  )
}

const PlayGame = () => {
  return(
    <div>
      <h1>Play a game here</h1>
    </div>
  )
}

export {JoinGame, MakeGame, PlayGame};
