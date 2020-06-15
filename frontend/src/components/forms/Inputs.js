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

const buildRadios = (props, type) => {
  if (props.options === undefined) return null;
  return Object.keys(props.options).map((key, index) => (
    <StyledRadio
      type="radio"
      label={props.options[key]}
      name={props.name}
      value={key}
      onChange={props.onChange}
      id={`${props.name}${index}`}
      checked={props.defaultValue === key ? true : false}
    />
  ));
};

const RadioButtons = (props) => {
  return <div>{props && buildRadios(props)}</div>;
};

const TabbedRadioButtons = ({}) => {};

export { RadioButtons };
