import React, { useState, useEffect } from "react";
import axios from "axios";
import { Form, Button, Card } from "react-bootstrap";
import { textAlign } from "@material-ui/system";

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
    <Card style={{ width: '18rem' }} alignItems="center" justifyContent="center" >
      <Form controlId="createGameForm" onSubmit={handleSubmit}>
        <Form.Group controlId="title" >
          <Form.Label>Title</Form.Label>
          <Form.Control type="input" defaultValue={defaults.default_title}/>
        </Form.Group>
        <Form.Group controlId="mode">
          <Form.Label>Game mode</Form.Label>
          <Form.Control as="select" defaultValue={defaults.default_game_mode}>
            {defaults.game_modes && optionBuilder(defaults.game_modes)}
          </Form.Control>
        </Form.Group>
        <Form.Group controlId="duration">
          <Form.Label>Game duration (days)</Form.Label>
          <Form.Control type="input" defaultValue={defaults.default_duration}/>
        </Form.Group>
        <Form.Group controlId="buy_in" >
          <Form.Label>Buy-in</Form.Label>
          <Form.Control type="input" defaultValue={defaults.default_buyin}/>
        </Form.Group>
        <Form.Group controlId="n_rebuys" >
          <Form.Label>Number of re-buys</Form.Label>
          <Form.Control type="input" defaultValue={defaults.default_rebuys}/>
        </Form.Group>
        <Form.Group controlId="benchmark">
          <Form.Label>Benchmark</Form.Label>
          <Form.Control as="select" defaultValue={defaults.default_benchmark}>
            {defaults.benchmarks && optionBuilder(defaults.benchmarks)}
          </Form.Control>
        </Form.Group>
        <Form.Group controlId="side_bets_perc" >
          <Form.Label>Sidebet % of pot</Form.Label>
          <Form.Control type="input" value={sidePotPct} onChange={(e) => setSidePotPct(e.target.value)}/>
        </Form.Group>
        {sidePotPct > 0 &&
          <Form.Group controlId="side_bets_period">
            <Form.Label>Sidebet period</Form.Label>
            <Form.Control as="select" defaultValue={defaults.default_sidebet_period}>
              {defaults.sidebet_periods && optionBuilder(defaults.sidebet_periods)}
            </Form.Control>
          </Form.Group>
        }
        <Form.Group controlId="participants">
          <Form.Label>Participants (Cntrl + click to select)</Form.Label>
          <Form.Control as="select" className="multiselect" multiple>
            {defaults.available_participants && optionBuilder(defaults.available_participants)}
          </Form.Control>
        </Form.Group>
        <Button variant="primary" type="submit">
          Submit
        </Button>
      </Form>
    </Card>
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
