import { Button } from 'react-bootstrap'
import styled from 'styled-components'

const AuxiliarButton = styled(Button)`
  font-size: var(--font-size-min);
  font-weight: normal;
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-smallcaps);
  svg{
    width: 16px;
    height: 16px;
    margin-top: -3px;
  }
`

export { AuxiliarButton }
