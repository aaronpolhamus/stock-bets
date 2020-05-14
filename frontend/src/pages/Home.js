import React from 'react';
import { Link, Redirect } from 'react-router-dom';
import { Button, Container, Row, Col, Card } from "react-bootstrap";
import {isEmpty, usePostRequest} from "../components/functions/api";
import axios from "axios";

const Logout = async () => {
  await axios.post('/api/logout')
  window.location.assign('/login')
};

const Home = () => {

  const { data, loading, error } = usePostRequest('/api/home');
   
  if (loading) {
    return <p>Loading...</p>
  }

  if ( !isEmpty(error) ) { 
    if (error.response.status === 401){ 
      return <Redirect to="/login" />
    }
  }
  
  if( isEmpty(data.username)) { 
    return <Redirect to="/welcome" />
  }

  const gameCardBuilder = (statusType, gamesArray) => {
    return (
      gamesArray.map((entry) => {
        let linkTo = null
        if (entry.status === "pending") {
          linkTo = "/join"
        } else if (entry.status === "active") { 
          linkTo = "/play" 
        }

        if(entry.status === statusType){
          return(
            <Card key={entry.id}>
              <Card.Body>
                <Link to={{pathname: linkTo, game_id: entry.id}}>{entry.title}</Link>
              </Card.Body>
            </Card>
          )
        }
      })
    )
  }

  return (
    <div className="App">
      <Container fluid="md">
        <Row>
          <Col>
            <Button href="/make">Make a new game</Button>
          </Col>
          <Col>
            <Button onClick={Logout}>Logout</Button>
          </Col>
        </Row>
        <Row>
          <h1> What's up, { data.name } ( {data.username} )? Your email is { data.email } </h1> 
        </Row>
        <Row className="justify-content-md-center">
          <img src={ data.profile_pic} height="200" width="200" alt="your beautiful profile pic"/>
        </Row>
        <Row>
          <Col>
            <Card.Header>Active games</Card.Header>
            {data && gameCardBuilder("active", data.game_info)}
          </Col>
          <Col>
            <Card.Header>Game invites</Card.Header>
            {data && gameCardBuilder("pending", data.game_info)}
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default Home;