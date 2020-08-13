import React from 'react'
import styled from 'styled-components'

const Loader = props => {
  const colors = [
    '#ffab69',
    '#ff3342',
    '#817094',
    '#2e253d'
  ]
  const drawLoaderElements = () => {
    return colors.map((color, i) => {
      return <i key={i} style={{ '--loader-item': i, backgroundColor: color }}/>
    })
  }

  const LoaderWrapper = styled.div`
    background-color: rgba(255, 255, 255, .9);
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1100;
    display: ${props => props.$show ? 'flex' : 'none'}; 
    transform: translate#d(0, 0, 0);
    justify-content: center; 
    align-items: center;
    span {
      display: flex;
      transform: skew(-20deg, 0)
    }
    i {
      display: block;
      width: 10px;
      height: 35px;
      margin: 0 2px;
      position: relative;
      top: 0;
      animation: element 1s infinite calc(.1s * var(--loader-item)) ease-in-out;
    }
    @keyframes element {
      50%{
        top: -10px;
      }
    }
  `
  return (
    <LoaderWrapper $show={props.show}>
      <span>
        {drawLoaderElements()}
      </span>
    </LoaderWrapper>
  )
}

export { Loader }
