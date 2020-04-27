import React, { Component } from 'react';
import '../App.css';

class App extends Component {
    constructor(props) {
        super(props);
        this.state = {
          data: null,
        };
      }

      componentDidMount() {
        fetch(`/`)
          .then(response => response.json())
          .then(data => this.setState({ data }));
      }
    
    render() {        
        return (
            <div>
                <h1>Here's the API response: {this.state.data} -- what do you want to do now?</h1>    
            </div>
        )
    };
};

export default App;