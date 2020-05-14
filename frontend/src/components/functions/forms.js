import React from "react"

const optionBuilder = (optionsArray) => 
  Object.keys(optionsArray).map((key, index) => 
  <option key={key} value={key}>{optionsArray[key]}</option>)

export {optionBuilder}