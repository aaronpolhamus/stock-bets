import React from "react";
import "./button.css";

//https://www.youtube.com/watch?v=JfNjGLGaxR4

const STYLES = [
  "btn--primary--solid",
  "btn--warnings--solid",
  "btn--danger--solid",
  "btn--success--solid",
  "btn--primary--outline",
  "btn--warnings--outline",
  "btn--danger--outline",
  "btn--success--outline",
]

const SIZES = ["btn--medium", "btn--small"]


export const Button = ({
  children,
  type,
  onClick,
  buttonStyle,
  buttonSize
}) => { 

  const checkButtonStyle = STYLES.includes(buttonStyle) ? buttonStyle : STYLES[0];

  const checkButtonSize = SIZES.includes(buttonSize) ? buttonSize: SIZES[0];

  return (
    <button className={`btn ${checkButtonStyle} ${checkButtonSize}`} onClick={onClick} type={type}>
      {children}
    </button>
  )
}

export default Button;