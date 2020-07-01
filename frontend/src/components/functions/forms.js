import React from 'react'

const optionBuilder = (optionsObject) =>
  // Takes an object of key-value pairs and turns it into an array of options for a form dropdown where the target value
  // is assigned to both the option key and value, while what's actually displayed is the value element from the
  // passed-in object
  Object.keys(optionsObject).map((key, index) => (
    <option key={key} value={key}>
      {optionsObject[key]}
    </option>
  ))

export { optionBuilder }
