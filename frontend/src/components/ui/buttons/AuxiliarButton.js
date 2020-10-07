import { Button } from 'react-bootstrap'
import styled from 'styled-components'
import { breakpoints } from 'design-tokens'

const AuxiliarButton = styled(Button)`
  font-size: var(--font-size-min);
  font-weight: normal;
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-smallcaps);
  span{
    display: none;
  }
  svg{
    width: 16px;
    height: 16px;
    margin-top: -3px;
  }
  @media screen and (min-width: ${breakpoints.md}){
    span{
      display: initial;
    }
  }
`

export { AuxiliarButton }
