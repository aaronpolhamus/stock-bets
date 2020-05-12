import React, { useEffect, useState } from "react";
import axios from "axios";

const PlayGame = (props) => {
  const [gameInfo, setGameInfo] = useState({})

  const fetchGameInfo = async (gameId) => {
    const resp = await axios.post("/api/game_info", {game_id: gameId, withCredentials: true})
    setGameInfo(resp.data)
  }

  useEffect(() => {
    fetchGameInfo(props.location.game_id)
  }, [])

  console.log(gameInfo)

  return(
    <div>
      <h1>Welcome to {gameInfo.title}: Let's get going :) </h1>
    </div>
  )
}

export {PlayGame};
