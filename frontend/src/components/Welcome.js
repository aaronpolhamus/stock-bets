import React, {Component} from "react";
import axios from "axios";
import { Redirect } from "react-router-dom";



class Welcome extends Component {
  constructor(props){
    super(props);
    this.state={'username': ''}
  }

  handleChange(e){
    this.setState({username: e.target.value});
  }
  
  async handleSubmit(e){
    e.preventDefault()
    await axios.post("/api/set_username", {
      withCredentials: true,
      username: this.state.username
    }).then(
      console.log("success")
      // <Redirect to="/" />
    ) 
  }
  
  render(){
    return (
      <div className="modal">
        <div className="modal_content">
          <form>
            <input onChange={this.handleChange.bind(this)} type="text" name="username" placeholder="Enter name here" />
            <button onClick={this.handleSubmit.bind(this)}>Submit</button>
          </form>
        </div>
      </div>
    );
  }
 }

export default Welcome;
