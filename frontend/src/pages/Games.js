import React from "react";
import { useForm } from "react-hook-form";
import { usePostRequest } from "../components/api"

const JoinGame = () => {
  return(
    <div>
      <h1>Join a game here</h1>
    </div>
  )
}

const MakeGame = () => {  
  // https://react-hook-form.com/get-started/
  const { register, handleSubmit, watch, errors } = useForm();
  const { defaults, defaultLoading, defaultError} = usePostRequest("/api/game_defaults")
  console.log(defaults)

  const onSubmit = (data) => {
      const payload = {
        withCredentials: true,
        title: data.title,
        mode: data.mode,
        duration: data.duration,
        buyin: data.buyin,
        benchmark: data.benchmark,
        participants: data.participants
      }
      alert(`Submitting Name ${payload}`)
  }

  return (
    <div className="form center">
      <form onSubmit={handleSubmit(onSubmit)}>
        <label>
          Title:
          <input name="title" defaultValue="Boom" ref={register({ required: true })} />
        </label>
        <label>
          Mode:
          <input name="mode" ref={register({ required: true })} />
        </label>
        <label>
          Duration:
          <input name="duration" ref={register({ required: true })} />
        </label>
        <label>
          Buy-in:
          <input name="buyin" ref={register({ required: true })} />
        </label>
        <label>
          Benchmark:
          <input name="benchmark" ref={register({ required: true })} />
        </label>
        <label>
          Participants:
          <input name="participants" ref={register({ required: true })} />
        </label>
        <input type="submit" value="Submit" />
      </form>
    </div>
  );
}

const PlayGame = () => {
  return(
    <div>
      <h1>Play a game here</h1>
    </div>
  )
}

export {JoinGame, MakeGame, PlayGame};
