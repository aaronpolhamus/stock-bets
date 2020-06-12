import React from "react";
import { Form } from "react-bootstrap";
import styled from "styled-components";

//This is a helper function to render radio buttons
//It's very important to define a name for radio buttons to work as expected and avoid collisions with other radios

const StyledRadio = styled(Form.Check)`
  color: var(--color-text-gray);
  padding-left: 0;
  display: inline-block;
  margin-right: var(--space-200);
  margin-bottom: var(--space-100);

  label {
    cursor: pointer;
    &::before {
      border: 1px solid var(--color-text-gray);
      border-radius: 50%;
      content: "";
      display: inline-block;
      height: 16px;
      margin-right: var(--space-50);
      position: relative;
      top: 2px;
      width: 16px;
    }
  }

  input {
    display: none;
  }

  input:checked + label {
    color: var(--color-text-primary);
    &::before {
      border-color: var(--color-primary-darken);
      background: radial-gradient(
        circle,
        var(--color-primary-darken) 35%,
        rgba(255, 255, 255, 1) 45%
      );
    }
  }
`;

const RadioButtons = ({ options, name, onChange, defaultValue }) => {
  const buildRadios = () => {
    return Object.keys(options).map((key, index) => (
      <StyledRadio
        type="radio"
        label={options[key]}
        name={name}
        value={key}
        onChange={onChange}
        id={`${name}${index}`}
        checked={defaultValue === key ? true : false}
      />
    ));
  };
  return <div>{options && buildRadios()}</div>;
};

export { RadioButtons };
